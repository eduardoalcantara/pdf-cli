"""
Engine Manager - Fase 5: Fallback Inteligente PyMuPDF + pypdf

Este módulo gerencia a escolha e fallback automático entre engines de manipulação de PDF
(PyMuPDF e pypdf) para maximizar a preservação de fontes originais durante edição de textos.
"""

from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import json
from datetime import datetime

from core.models import TextObject
import time

# Importação condicional de PDFRepository para evitar dependência circular
try:
    from app.pdf_repo import PDFRepository
except ImportError:
    PDFRepository = None  # Será importado quando necessário


class EngineType(Enum):
    """Tipos de engines disponíveis para manipulação de PDF."""
    PYMUPDF = "pymupdf"
    PYPDF = "pypdf"


@dataclass
class FontComparison:
    """Resultado da comparação de fontes antes e depois da edição."""
    object_id: str
    page: int
    original_font: str
    original_font_size: int
    final_font: str
    final_font_size: int
    font_preserved: bool
    font_fallback_detected: bool
    fallback_reason: Optional[str] = None


@dataclass
class EngineResult:
    """Resultado de uma tentativa de edição com um engine específico."""
    engine: EngineType
    success: bool
    output_path: Optional[str] = None
    font_comparisons: List[FontComparison] = None
    any_font_fallback: bool = False
    error: Optional[str] = None
    execution_time_ms: Optional[float] = None

    def __post_init__(self):
        if self.font_comparisons is None:
            self.font_comparisons = []
        # Detectar se houve qualquer fallback
        if self.font_comparisons:
            self.any_font_fallback = any(
                comp.font_fallback_detected for comp in self.font_comparisons
            )

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dicionário para serialização JSON."""
        result = asdict(self)
        result['engine'] = self.engine.value
        result['font_comparisons'] = [
            asdict(comp) for comp in self.font_comparisons
        ]
        return result


class EngineManager:
    """
    Gerencia fallback automático entre PyMuPDF e pypdf para preservação de fontes.

    Conforme Fase 5: detecta quando PyMuPDF não preserva a fonte original e
    automaticamente tenta com pypdf.
    """

    def __init__(self, prefer_engine: str = "pymupdf"):
        """
        Inicializa o engine manager.

        Args:
            prefer_engine: Engine preferido ("pymupdf" ou "pypdf")
        """
        self.prefer_engine = EngineType(prefer_engine.lower())
        self.attempts: List[EngineResult] = []

    def detect_font_fallback(
        self,
        original_objects: List[TextObject],
        modified_objects: List[TextObject],
        target_object_ids: List[str],
        search_term: Optional[str] = None,
        new_content: Optional[str] = None
    ) -> List[FontComparison]:
        """
        Detecta se houve fallback de fonte comparando objetos originais e modificados.

        Usa múltiplas propriedades para identificar objetos correspondentes:
        - Página (sempre igual)
        - Posição X/Y aproximada (com tolerância)
        - Tamanho aproximado (com tolerância)
        - Texto modificado (se conhecido - search_term → new_content)
        - Fonte e tamanho original

        Args:
            original_objects: Lista de objetos de texto originais (antes da edição)
            modified_objects: Lista de objetos de texto modificados (depois da edição)
            target_object_ids: IDs dos objetos que foram editados (usado para filtrar objetos originais)
            search_term: Texto original que foi buscado para edição (opcional, ajuda na correspondência)
            new_content: Novo conteúdo que substituiu o search_term (opcional, ajuda na correspondência)

        Returns:
            Lista de FontComparison com os resultados da comparação
        """
        comparisons = []

        # Filtrar apenas objetos originais que foram editados
        target_original_objects = [obj for obj in original_objects if obj.id in target_object_ids]

        # Tolerâncias para comparação (em pontos)
        POSITION_X_TOLERANCE = 1.0  # Posição X muda pouco
        POSITION_Y_TOLERANCE = 3.0  # Posição Y pode mudar mais após redaction
        SIZE_TOLERANCE = 5.0  # Tamanho pode mudar um pouco

        # Para cada objeto original que foi editado, encontrar correspondente no modificado
        for original_obj in target_original_objects:
            original_content = original_obj.content

            # Calcular o texto esperado após modificação
            expected_modified_content = None
            if search_term and new_content and search_term in original_content:
                if search_term != original_content:
                    # Substituição parcial
                    expected_modified_content = original_content.replace(search_term, new_content, 1)
                else:
                    # Substituição completa
                    expected_modified_content = new_content

            # Buscar objeto modificado correspondente usando múltiplos critérios
            best_match = None
            best_score = 0

            for modified_obj in modified_objects:
                score = 0

                # Critério 1: Mesma página (obrigatório)
                if modified_obj.page != original_obj.page:
                    continue
                score += 10

                # Critério 2: Posição X aproximada (muito importante)
                x_diff = abs(modified_obj.x - original_obj.x)
                if x_diff <= POSITION_X_TOLERANCE:
                    score += 20  # Match perfeito
                elif x_diff <= POSITION_X_TOLERANCE * 2:
                    score += 10  # Match aproximado
                else:
                    continue  # X muito diferente, provavelmente não é o mesmo objeto

                # Critério 3: Posição Y aproximada (importante, mas menos precisa)
                y_diff = abs(modified_obj.y - original_obj.y)
                if y_diff <= POSITION_Y_TOLERANCE:
                    score += 15
                elif y_diff <= POSITION_Y_TOLERANCE * 2:
                    score += 8
                else:
                    # Y muito diferente, mas ainda pode ser o mesmo objeto (redaction pode mudar Y)
                    score += 3  # Pontuação baixa, mas não descarta

                # Critério 4: Tamanho aproximado (width/height)
                width_diff = abs(modified_obj.width - original_obj.width)
                height_diff = abs(modified_obj.height - original_obj.height)
                if width_diff <= SIZE_TOLERANCE and height_diff <= SIZE_TOLERANCE:
                    score += 10
                elif width_diff <= SIZE_TOLERANCE * 2 and height_diff <= SIZE_TOLERANCE * 2:
                    score += 5

                # Critério 5: Texto modificado esperado (muito importante se disponível)
                if expected_modified_content:
                    # Verificar se o conteúdo do objeto modificado corresponde ao esperado
                    if modified_obj.content == expected_modified_content:
                        score += 30  # Match perfeito do conteúdo modificado
                    elif expected_modified_content in modified_obj.content or modified_obj.content in expected_modified_content:
                        score += 15  # Conteúdo parcialmente correspondente
                    elif new_content in modified_obj.content:
                        # Pelo menos o novo conteúdo está presente
                        score += 10
                else:
                    # Se não temos o texto esperado, verificar se o conteúdo mudou em relação ao original
                    # (o objeto foi modificado se o conteúdo não é mais o original)
                    if modified_obj.content != original_content and (not search_term or search_term not in modified_obj.content):
                        score += 5  # Conteúdo mudou (provavelmente foi editado)

                # Critério 6: Primeiras letras do conteúdo (ajuda a diferenciar objetos similares)
                # Nota: Não usado para matching direto, mas pode ajudar em casos específicos

                # Critério 7: Fonte e tamanho originais (para validação cruzada)
                # Nota: não usamos isso para matching, mas para verificar depois se houve fallback

                # Se a pontuação é melhor que a anterior, atualizar melhor match
                if score > best_score:
                    best_score = score
                    best_match = modified_obj

            # Se encontrou um match suficientemente bom (score mínimo)
            if best_match and best_score >= 30:  # Score mínimo para considerar válido
                # Comparar fontes
                original_font = original_obj.font_name
                modified_font = best_match.font_name

                font_preserved = (
                    original_font == modified_font and
                    original_obj.font_size == best_match.font_size
                )

                font_fallback_detected = not font_preserved
                fallback_reason = None

                if font_fallback_detected:
                    # Determinar motivo do fallback
                    if modified_font in ["Helvetica", "helv"] and original_font not in ["Helvetica", "helv"]:
                        fallback_reason = f"Fonte '{original_font}' substituída por Helvetica padrão"
                    elif original_font and modified_font != original_font:
                        fallback_reason = f"Fonte '{original_font}' → '{modified_font}'"
                    elif original_obj.font_size != best_match.font_size:
                        fallback_reason = f"Tamanho alterado: {original_obj.font_size}pt → {best_match.font_size}pt"

                comparison = FontComparison(
                    object_id=best_match.id,
                    page=best_match.page,
                    original_font=original_font or "N/A",
                    original_font_size=original_obj.font_size,
                    final_font=modified_font or "N/A",
                    final_font_size=best_match.font_size,
                    font_preserved=font_preserved,
                    font_fallback_detected=font_fallback_detected,
                    fallback_reason=fallback_reason
                )
                comparisons.append(comparison)
            else:
                # Não encontrou match suficientemente bom - registrar como não detectado
                # Mas ainda criar comparação para indicar que não foi possível verificar
                comparison = FontComparison(
                    object_id=original_obj.id,
                    page=original_obj.page,
                    original_font=original_obj.font_name or "N/A",
                    original_font_size=original_obj.font_size,
                    final_font="N/A",
                    final_font_size=0,
                    font_preserved=False,
                    font_fallback_detected=True,  # Assumir fallback se não conseguiu verificar
                    fallback_reason=f"Não foi possível encontrar objeto correspondente após edição (score: {best_score})"
                )
                comparisons.append(comparison)

        return comparisons

    def should_try_fallback(self, result: EngineResult) -> bool:
        """
        Decide se deve tentar fallback para outro engine.

        Args:
            result: Resultado da tentativa atual

        Returns:
            True se deve tentar fallback, False caso contrário
        """
        # Se não foi bem-sucedido, não tentar fallback
        if not result.success:
            return False

        # Se PyMuPDF foi usado e detectou fallback de fonte, tentar pypdf
        if result.engine == EngineType.PYMUPDF and result.any_font_fallback:
            return True

        return False

    def get_next_engine(self, current_engine: EngineType) -> Optional[EngineType]:
        """
        Retorna o próximo engine a ser tentado em caso de fallback.

        Args:
            current_engine: Engine atual que foi tentado

        Returns:
            Próximo engine a tentar, ou None se não houver mais opções
        """
        if current_engine == EngineType.PYMUPDF:
            return EngineType.PYPDF
        elif current_engine == EngineType.PYPDF:
            return EngineType.PYMUPDF
        return None

    def calculate_file_hash(self, file_path: str) -> str:
        """
        Calcula hash SHA256 de um arquivo PDF para auditoria.

        Args:
            file_path: Caminho do arquivo PDF

        Returns:
            Hash SHA256 hexadecimal do arquivo
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def create_audit_entry(
        self,
        pdf_path: str,
        output_path: Optional[str],
        operation_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cria entrada de auditoria para logs detalhados.

        Args:
            pdf_path: Caminho do PDF original
            output_path: Caminho do PDF modificado (se existir)
            operation_type: Tipo de operação realizada
            parameters: Parâmetros da operação

        Returns:
            Dicionário com dados de auditoria
        """
        audit = {
            "timestamp": datetime.now().isoformat(),
            "operation_type": operation_type,
            "input_file": pdf_path,
            "output_file": output_path,
            "input_hash": self.calculate_file_hash(pdf_path) if Path(pdf_path).exists() else None,
            "output_hash": self.calculate_file_hash(output_path) if output_path and Path(output_path).exists() else None,
            "parameters": parameters,
            "engine_attempts": [attempt.to_dict() for attempt in self.attempts],
            "final_engine_used": self.attempts[-1].engine.value if self.attempts else None,
            "final_success": self.attempts[-1].success if self.attempts else False
        }

        # Adicionar operação ID único baseado em hash
        audit_id_content = f"{pdf_path}{operation_type}{datetime.now().isoformat()}"
        audit["operation_id"] = hashlib.md5(audit_id_content.encode()).hexdigest()

        return audit

    def edit_text_with_pypdf(
        self,
        pdf_path: str,
        output_path: str,
        search_term: str,
        new_content: str,
        target_object_ids: List[str],
        original_objects: List[TextObject]
    ) -> EngineResult:
        """
        Edita texto usando PyPDF2 preservando especificações de fonte (/F1, /F2, etc.).

        Extrai as referências de fonte do PDF original e as mantém ao editar o texto,
        modificando apenas o conteúdo do stream mantendo as especificações de fonte.

        Args:
            pdf_path: Caminho do PDF original
            output_path: Caminho de saída
            search_term: Texto a buscar
            new_content: Novo conteúdo
            target_object_ids: IDs dos objetos a editar
            original_objects: Objetos originais para preservar propriedades

        Returns:
            EngineResult com o resultado da tentativa
        """
        start_time = time.time()

        try:
            import PyPDF2
            import re

            # Criar dicionário de objetos originais por ID para busca rápida
            original_by_id = {obj.id: obj for obj in original_objects}
            target_objects = [obj for obj in original_objects if obj.id in target_object_ids]

            # Abrir PDF original
            with open(pdf_path, "rb") as input_file:
                reader = PyPDF2.PdfReader(input_file)
                writer = PyPDF2.PdfWriter()

                # Copiar todas as páginas mantendo recursos (incluindo fontes)
                for page_num, page in enumerate(reader.pages):
                    # Tentar extrair e modificar o conteúdo da página preservando fontes
                    try:
                        # Obter conteúdo da página
                        content_object = page.get_contents()

                        if content_object is None:
                            # Se não houver conteúdo, apenas copiar a página
                            writer.add_page(page)
                            continue

                        # Extrair stream de conteúdo
                        if hasattr(content_object, 'get_data'):
                            content_stream = content_object.get_data()
                        elif hasattr(content_object, 'getData'):
                            content_stream = content_object.getData()
                        else:
                            # Se não conseguir extrair, copiar página original
                            writer.add_page(page)
                            continue

                        # Decodificar stream se necessário
                        try:
                            content_str = content_stream.decode('utf-8', errors='ignore')
                        except:
                            content_str = content_stream.decode('latin-1', errors='ignore')

                        # Procurar objetos de texto na página atual para modificar
                        page_modified = False
                        for target_obj in target_objects:
                            if target_obj.page == page_num and search_term in target_obj.content:
                                # Substituir texto mantendo referências de fonte
                                original_text = target_obj.content

                                # Se search_term é substring, fazer substituição parcial
                                if search_term in original_text and search_term != original_text:
                                    replacement_text = original_text.replace(search_term, new_content, 1)
                                else:
                                    replacement_text = new_content

                                # Escapar caracteres especiais do PDF para regex
                                # re.escape() já escapa tudo corretamente para regex
                                escaped_original = re.escape(original_text)

                                # Escapar caracteres especiais para string PDF de saída
                                def escape_pdf_string_for_output(text):
                                    """Escapa caracteres especiais para string PDF de saída."""
                                    # No PDF, precisamos escapar: \ ( )
                                    return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

                                escaped_replacement = escape_pdf_string_for_output(replacement_text)

                                # Padrão 1: (texto) Tj - formato mais comum
                                # O padrão encontrado na investigação mostra: (LUIZ EDUARDO ALVES DE ALCANTARA) Tj
                                # Buscar exatamente o texto original entre parênteses seguido de espaço(s) e Tj
                                pattern_tj = re.compile(
                                    r'\(' + escaped_original + r'\)\s+Tj',
                                    re.IGNORECASE
                                )

                                if pattern_tj.search(content_str):
                                    # Substituir mantendo formato exato
                                    content_str = pattern_tj.sub(f'({escaped_replacement}) Tj', content_str)
                                    page_modified = True
                                    continue

                                # Padrão 2: (texto) TJ - com operador TJ (array)
                                # Procurar texto seguido de TJ (operador de array)
                                pattern_tj_upper = re.compile(
                                    r'\(' + escaped_original + r'\)\s*TJ',
                                    re.IGNORECASE
                                )

                                if pattern_tj_upper.search(content_str):
                                    content_str = pattern_tj_upper.sub(f'({escaped_replacement}) TJ', content_str)
                                    page_modified = True
                                    continue

                                # Padrão 3: Array de texto [texto] TJ
                                # Procurar texto dentro de arrays PDF: [texto] TJ
                                # O texto pode estar no meio do array
                                pattern_tj_array = re.compile(
                                    r'\[([^\]]*)\(' + escaped_original + r'\)([^\]]*)\]\s*TJ',
                                    re.IGNORECASE
                                )

                                if pattern_tj_array.search(content_str):
                                    def replace_array(match):
                                        before = match.group(1)  # Texto antes no array
                                        after = match.group(2)   # Texto depois no array
                                        return f'[{before}({escaped_replacement}){after}] TJ'

                                    content_str = pattern_tj_array.sub(replace_array, content_str)
                                    page_modified = True
                                    continue

                                # Padrão 4: Buscar texto mesmo sem operador explícito
                                # Último recurso: substituir apenas o texto entre parênteses
                                simple_pattern = re.compile(
                                    r'\(' + escaped_original + r'\)',
                                    re.IGNORECASE
                                )

                                if simple_pattern.search(content_str):
                                    # Substituir apenas se encontrarmos o padrão exato
                                    content_str = simple_pattern.sub(f'({escaped_replacement})', content_str)
                                    page_modified = True
                                    continue

                        if page_modified:
                            # Recodificar stream para bytes
                            try:
                                new_content_stream = content_str.encode('utf-8')
                            except UnicodeEncodeError:
                                # Tentar latin-1 se UTF-8 falhar (comum em PDFs)
                                try:
                                    new_content_stream = content_str.encode('latin-1')
                                except:
                                    # Fallback: tentar cp1252 (Windows)
                                    try:
                                        new_content_stream = content_str.encode('cp1252')
                                    except:
                                        # Último recurso: usar original se não conseguir codificar
                                        new_content_stream = content_stream
                                        page_modified = False  # Marcar como não modificado

                            # Atualizar conteúdo da página apenas se realmente modificou
                            if page_modified:
                                try:
                                    # PyPDF2 tem limitações na edição direta de EncodedStreamObject
                                    # Tentar diferentes abordagens baseadas no tipo de objeto

                                    # Abordagem 1: Tentar atualizar _data diretamente (worksaround)
                                    if hasattr(content_object, '_data'):
                                        # Atualizar diretamente o atributo _data
                                        content_object._data = new_content_stream
                                        # Forçar atualização do stream
                                        if hasattr(content_object, '_write_object'):
                                            # Marcar como modificado
                                            pass

                                    # Abordagem 2: Criar novo ContentStream se possível
                                    elif hasattr(page, '/Contents'):
                                        from PyPDF2.generic import ContentStream, NameObject
                                        try:
                                            # Criar novo stream objeto
                                            from PyPDF2.generic import StreamObject
                                            new_stream_obj = StreamObject()
                                            new_stream_obj._data = new_content_stream
                                            # Copiar filtros e parâmetros do original se houver
                                            if hasattr(content_object, 'get'):
                                                for key in ['/Filter', '/Length', '/DecodeParms']:
                                                    if key in content_object:
                                                        new_stream_obj[key] = content_object[key]
                                            # Atualizar página com novo conteúdo
                                            page[NameObject('/Contents')] = new_stream_obj
                                        except Exception as e2:
                                            # Se falhar, tentar abordagem mais simples
                                            pass

                                    # Abordagem 3: Usar clone e modificar
                                    # Clonar página e substituir conteúdo
                                    try:
                                        from PyPDF2.generic import IndirectObject, DictionaryObject
                                        # Criar nova página baseada na original
                                        new_page = page.__class__(page.get_object())
                                        # Atualizar conteúdo manualmente
                                        if '/Contents' in new_page:
                                            contents = new_page['/Contents']
                                            if isinstance(contents, list):
                                                # Múltiplos objetos de conteúdo
                                                # Atualizar o primeiro (onde está o texto)
                                                if len(contents) > 0:
                                                    first_content = reader.get_object(contents[0])
                                                    if hasattr(first_content, '_data'):
                                                        first_content._data = new_content_stream
                                            else:
                                                # Objeto único
                                                content_obj = reader.get_object(contents) if isinstance(contents, IndirectObject) else contents
                                                if hasattr(content_obj, '_data'):
                                                    content_obj._data = new_content_stream
                                        page = new_page
                                    except Exception as e3:
                                        # Se todas as abordagens falharem, usar página original
                                        pass

                                    # Adicionar página ao writer
                                    writer.add_page(page)
                                except Exception as e:
                                    # Se falhar completamente, usar página original sem modificação
                                    writer.add_page(page)
                                    page_modified = False  # Marcar como não modificado para indicar falha
                            else:
                                # Não modificou (problema na codificação), usar original
                                writer.add_page(page)
                        else:
                            # Se não modificou, copiar página original
                            writer.add_page(page)

                    except Exception as e:
                        # Se houver erro ao processar a página, copiar original
                        # Log do erro mas continua processando outras páginas
                        writer.add_page(page)
                        continue

                # Salvar PDF modificado
                with open(output_path, "wb") as output_file:
                    writer.write(output_file)

                # Verificar preservação de fontes lendo o PDF modificado
                modified_objects = []
                try:
                    if PDFRepository is None:
                        from app.pdf_repo import PDFRepository
                    with PDFRepository(output_path) as repo:
                        modified_objects = repo.extract_text_objects()
                except Exception as e:
                    # Se não conseguir ler, considerar como falha parcial
                    pass

                # Comparar fontes
                font_comparisons = self.detect_font_fallback(
                    original_objects=original_objects,
                    modified_objects=modified_objects,
                    target_object_ids=target_object_ids,
                    search_term=search_term,  # Texto buscado para melhor correspondência
                    new_content=new_content   # Novo conteúdo para validação
                )

                execution_time = (time.time() - start_time) * 1000

                # Verificar se houve sucesso (sem fallback de fonte)
                success = len(font_comparisons) > 0 and not any(
                    comp.font_fallback_detected for comp in font_comparisons
                )

                return EngineResult(
                    engine=EngineType.PYPDF,
                    success=success,
                    output_path=output_path,
                    font_comparisons=font_comparisons,
                    error=None if success else "Algumas fontes podem não ter sido preservadas completamente",
                    execution_time_ms=execution_time
                )

        except ImportError:
            execution_time = (time.time() - start_time) * 1000
            return EngineResult(
                engine=EngineType.PYPDF,
                success=False,
                error="PyPDF2 não está instalado. Instale com: pip install PyPDF2",
                execution_time_ms=execution_time
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return EngineResult(
                engine=EngineType.PYPDF,
                success=False,
                error=f"Erro ao tentar edição com PyPDF2: {str(e)}",
                execution_time_ms=execution_time
            )


def create_audit_log(
    pdf_path: str,
    output_path: str,
    engine_results: List[EngineResult],
    operation_type: str
) -> Dict[str, Any]:
    """
    Função auxiliar para criar log de auditoria completo.

    Args:
        pdf_path: Caminho do PDF original
        output_path: Caminho do PDF modificado
        engine_results: Lista de resultados dos engines tentados
        operation_type: Tipo de operação

    Returns:
        Dicionário com dados de auditoria completos
    """
    engine_manager = EngineManager()

    # Calcular hashes
    input_hash = None
    output_hash = None
    try:
        input_hash = engine_manager.calculate_file_hash(pdf_path)
    except:
        pass
    try:
        if output_path and Path(output_path).exists():
            output_hash = engine_manager.calculate_file_hash(output_path)
    except:
        pass

    # Criar entrada de auditoria
    audit = {
        "timestamp": datetime.now().isoformat(),
        "operation_type": operation_type,
        "input_file": pdf_path,
        "output_file": output_path,
        "input_hash": input_hash,
        "output_hash": output_hash,
        "engine_attempts": [result.to_dict() for result in engine_results],
        "final_engine_used": engine_results[-1].engine.value if engine_results else None,
        "final_success": engine_results[-1].success if engine_results else False,
        "any_font_fallback": any(result.any_font_fallback for result in engine_results),
        "font_preservation_success": (
            engine_results[-1].success and not engine_results[-1].any_font_fallback
            if engine_results else False
        )
    }

    # Adicionar operação ID único
    audit_id_content = f"{pdf_path}{operation_type}{datetime.now().isoformat()}"
    audit["operation_id"] = hashlib.md5(audit_id_content.encode()).hexdigest()

    return audit
