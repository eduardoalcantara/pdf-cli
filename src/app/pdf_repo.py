"""
Camada de infraestrutura para operações com arquivos PDF.

Este módulo encapsula todas as operações de baixo nível com PDFs,
utilizando PyMuPDF (fitz) e PyPDF2 para manipulação, leitura e escrita
de arquivos PDF. Serve como camada de abstração entre a lógica de negócio
e as bibliotecas específicas de PDF.
"""

from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import fitz  # PyMuPDF
import base64
import shutil
import hashlib
import os
import platform
from dataclasses import dataclass
from core.exceptions import PDFFileNotFoundError, PDFMalformedError, InvalidPageError
from core.models import (
    TextObject, ImageObject, TableObject, LinkObject,
    FormFieldObject, CheckboxFieldObject, RadioButtonFieldObject, SignatureFieldObject,
    LineObject, RectangleObject, EllipseObject, PolylineObject, BezierCurveObject,
    HighlightAnnotation, CommentAnnotation, MarkerAnnotation,
    LayerObject, FilterObject
)


@dataclass
class ExtractedFont:
    """Representa uma fonte extraída do PDF."""
    name: str  # Nome da fonte (ex: "ArialMT")
    base_font: Optional[str] = None  # Nome base (ex: "Arial")
    is_bold: bool = False
    is_italic: bool = False
    font_buffer: Optional[bytes] = None  # Buffer da fonte embeddada (se disponível)
    font_file_path: Optional[str] = None  # Caminho temporário para arquivo de fonte extraída
    xref: Optional[int] = None  # Referência do objeto no PDF
    encoding: Optional[str] = None  # Encoding da fonte (ex: "WinAnsiEncoding")



class PDFRepository:
    """
    Repositório para operações de infraestrutura com arquivos PDF.

    Esta classe encapsula todas as interações de baixo nível com bibliotecas
    de manipulação de PDF, fornecendo uma interface limpa para a camada de
    serviços de aplicação.
    """

    def __init__(self, pdf_path: str):
        """
        Inicializa o repositório com um arquivo PDF.

        Args:
            pdf_path: Caminho para o arquivo PDF.

        Raises:
            PDFFileNotFoundError: Se o arquivo não for encontrado.
            PDFMalformedError: Se o arquivo estiver corrompido.
        """
        self.pdf_path = Path(pdf_path)
        self._validate_pdf_path()
        self._doc: Optional[fitz.Document] = None

    def _validate_pdf_path(self) -> None:
        """
        Valida se o caminho do PDF existe e é um arquivo válido.

        Raises:
            PDFFileNotFoundError: Se o arquivo não for encontrado.
        """
        if not self.pdf_path.exists():
            raise PDFFileNotFoundError(
                str(self.pdf_path)
            )
        if not self.pdf_path.is_file():
            raise PDFFileNotFoundError(
                str(self.pdf_path)
            )

    def open(self) -> fitz.Document:
        """
        Abre o documento PDF e retorna a instância do PyMuPDF.

        Returns:
            fitz.Document: Documento PDF aberto.

        Raises:
            PDFMalformedError: Se o PDF estiver corrompido.
        """
        try:
            if self._doc is None:
                self._doc = fitz.open(str(self.pdf_path))
            return self._doc
        except Exception as e:
            raise PDFMalformedError(
                str(self.pdf_path),
                f"Erro ao abrir: {str(e)}"
            ) from e

    def close(self) -> None:
        """Fecha o documento PDF, liberando recursos."""
        if self._doc is not None:
            self._doc.close()
            self._doc = None

    def get_page_count(self) -> int:
        """
        Retorna o número de páginas do PDF.

        Returns:
            int: Número de páginas.
        """
        doc = self.open()
        return len(doc)

    def get_metadata(self) -> dict:
        """
        Retorna os metadados do PDF.

        Returns:
            dict: Dicionário com metadados do PDF.
        """
        doc = self.open()
        return doc.metadata

    def set_metadata(self, metadata: Dict[str, str]) -> None:
        """
        Define metadados do PDF.

        Args:
            metadata: Dicionário com metadados a serem definidos.
        """
        doc = self.open()
        doc.set_metadata(metadata)

    def extract_text_objects(self) -> List[TextObject]:
        """
        Extrai todos os objetos de texto do PDF.

        Returns:
            List[TextObject]: Lista de objetos de texto extraídos.
        """
        doc = self.open()
        text_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")

            # Contador para objetos na mesma posição (para evitar colisões de ID)
            position_counter = {}

            for block in blocks.get("blocks", []):
                if block.get("type") == 0:  # Text block
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            content = span.get("text", "").strip()
                            bbox = span.get("bbox", [0, 0, 0, 0])
                            x = bbox[0]
                            y = bbox[1]
                            width = bbox[2] - bbox[0]
                            height = bbox[3] - bbox[1]

                            # Gerar ID determinístico baseado em características estáveis
                            # Usar página, posição arredondada e tamanho para que IDs sejam consistentes
                            # mesmo após edição do texto. Arredondar posições para evitar variações pequenas.
                            x_rounded = round(x)
                            y_rounded = round(y)
                            width_rounded = round(width)
                            height_rounded = round(height)

                            # Usar posição + tamanho para diferenciar objetos na mesma posição
                            pos_key = f"{page_num}_{x_rounded}_{y_rounded}_{width_rounded}_{height_rounded}"

                            # Contar quantos objetos já tiveram essa posição/tamanho
                            if pos_key not in position_counter:
                                position_counter[pos_key] = 0
                            position_counter[pos_key] += 1
                            index = position_counter[pos_key]

                            # Incluir índice para objetos na mesma posição/tamanho
                            id_content = f"{pos_key}_{index}"
                            stable_id = hashlib.md5(id_content.encode('utf-8')).hexdigest()

                            text_obj = TextObject(
                                id=stable_id,  # ID determinístico baseado em características estáveis
                                page=page_num,
                                content=content,
                                x=x,
                                y=y,
                                width=width,
                                height=height,
                                font_name=span.get("font", ""),
                                font_size=int(span.get("size", 0)),
                                color=f"#{span.get('color', 0):06x}" if isinstance(span.get("color"), int) else "#000000",
                                rotation=0.0
                            )
                            if text_obj.content:
                                text_objects.append(text_obj)

        return text_objects

    def extract_fonts(self) -> Dict[str, ExtractedFont]:
        """
        Extrai todas as fontes usadas no PDF com suas propriedades.

        Returns:
            Dict[str, ExtractedFont]: Dicionário mapeando nome da fonte para ExtractedFont.
        """
        doc = self.open()
        fonts_dict = {}

        # Iterar sobre todas as páginas
        for page_num in range(len(doc)):
            page = doc[page_num]

            # Obter lista de fontes usadas na página
            # get_fonts(full=True) retorna lista de dicionários
            try:
                font_list = page.get_fonts(full=True)
            except:
                # Fallback para get_fonts() simples
                font_list = page.get_fonts()

            for font_info in font_list:
                # font_info pode ser dict (full=True) ou tupla (full=False)
                if isinstance(font_info, dict):
                    # Formato dict quando full=True
                    xref = font_info.get('xref', 0)
                    base_font = font_info.get('basefont', font_info.get('name', ""))
                    font_name = font_info.get('name', base_font)
                    encoding = font_info.get('encoding', "")
                    is_embedded = font_info.get('embedded', False)
                    is_subset = font_info.get('subset', False)
                    ext = font_info.get('ext', "")
                    font_type = font_info.get('type', "")
                elif isinstance(font_info, (list, tuple)):
                    # Formato tupla: (xref, ext, type, basefont, name, encoding, embedded)
                    # Com full=True: tupla de 7 elementos
                    # Sem full: tupla de 6 elementos (sem embedded)
                    if len(font_info) >= 6:
                        xref = font_info[0]
                        ext = font_info[1] if len(font_info) > 1 else ""
                        font_type = font_info[2] if len(font_info) > 2 else ""
                        base_font = font_info[3] if font_info[3] else ""
                        # name aqui é o nome da referência no PDF (ex: F8), não o nome da fonte
                        font_ref_name = font_info[4] if font_info[4] else ""
                        encoding = font_info[5] if font_info[5] else ""
                        # embedded é o 7º elemento (índice 6) se full=True
                        is_embedded = bool(font_info[6]) if len(font_info) > 6 else False
                        is_subset = False  # Não temos essa informação na tupla
                        # Usar basefont como font_name (nome real da fonte)
                        font_name = base_font if base_font else font_ref_name
                    else:
                        continue
                else:
                    continue

                # Se já extraímos esta fonte (por xref ou base_font), pular
                # Usar base_font como chave ao invés de font_name para evitar duplicatas
                font_key = base_font if base_font else font_name
                if not font_key or font_key in fonts_dict:
                    continue

                # Detectar se é bold/italic pelo nome
                name_upper = font_name.upper()
                is_bold = "BOLD" in name_upper or "-BOLD" in font_name or "BOLD" in base_font.upper()
                is_italic = "ITALIC" in name_upper or "-ITALIC" in font_name or "ITALIC" in base_font.upper() or "OBLIQUE" in name_upper

                # Tentar extrair buffer da fonte se estiver embeddada
                font_buffer = None
                font_file_path = None

                if is_embedded and xref > 0:
                    try:
                        # Tentar extrair fonte embeddada
                        font_data = doc.xref_stream(xref)
                        if font_data:
                            font_buffer = font_data
                            # Salvar em arquivo temporário para uso posterior
                            import tempfile
                            temp_font = tempfile.NamedTemporaryFile(delete=False, suffix='.ttf', dir=tempfile.gettempdir())
                            temp_font.write(font_data)
                            temp_font.close()
                            font_file_path = temp_font.name
                    except Exception as e:
                        # Se não conseguir extrair, continuar sem buffer
                        pass

                fonts_dict[font_key] = ExtractedFont(
                    name=font_name,
                    base_font=base_font if base_font != font_name else None,
                    is_bold=is_bold,
                    is_italic=is_italic,
                    font_buffer=font_buffer,
                    font_file_path=font_file_path,
                    xref=xref,
                    encoding=encoding
                )

        return fonts_dict

    def _find_system_font(self, font_name: str) -> List[str]:
        """
        Busca arquivo de fonte no sistema operacional.

        Args:
            font_name: Nome da fonte (ex: "ArialMT", "ArialNarrow-Bold")

        Returns:
            List[str]: Lista de caminhos de arquivos de fonte encontrados
        """
        font_paths = []

        # Normalizar nome da fonte para busca
        font_base = font_name.split('-')[0].split()[0]  # "ArialNarrow-Bold" -> "ArialNarrow"
        font_base_simple = font_base.replace('MT', '').replace('Narrow', '').strip()  # "ArialMT" -> "Arial"

        # Detectar sistema operacional
        system = platform.system()

        # Diretórios comuns de fontes
        font_dirs = []

        if system == "Windows":
            # Windows: %WINDIR%\Fonts
            windir = os.environ.get('WINDIR', 'C:\\Windows')
            font_dirs.append(os.path.join(windir, 'Fonts'))
            # Também verificar %LOCALAPPDATA%\Microsoft\Windows\Fonts
            localappdata = os.environ.get('LOCALAPPDATA', '')
            if localappdata:
                font_dirs.append(os.path.join(localappdata, 'Microsoft', 'Windows', 'Fonts'))
        elif system == "Darwin":  # macOS
            font_dirs.extend([
                '/Library/Fonts',
                '/System/Library/Fonts',
                os.path.expanduser('~/Library/Fonts')
            ])
        elif system == "Linux":
            font_dirs.extend([
                '/usr/share/fonts',
                '/usr/local/share/fonts',
                os.path.expanduser('~/.fonts'),
                os.path.expanduser('~/.local/share/fonts')
            ])

        # Extensões de arquivo de fonte
        font_extensions = ['.ttf', '.otf', '.ttc', '.woff', '.woff2']

        # Buscar arquivos de fonte
        for font_dir in font_dirs:
            if not os.path.isdir(font_dir):
                continue

            try:
                for file in os.listdir(font_dir):
                    file_lower = file.lower()

                    # Verificar se é arquivo de fonte
                    if not any(file_lower.endswith(ext) for ext in font_extensions):
                        continue

                    # Verificar se nome corresponde (case-insensitive)
                    file_base = Path(file).stem
                    file_base_lower = file_base.lower()
                    file_full_lower = file_lower

                    # Normalizar nomes para comparação (remover espaços, hífens, underscores)
                    font_name_normalized = font_name.lower().replace(' ', '').replace('-', '').replace('_', '')
                    font_base_normalized = font_base.lower().replace(' ', '').replace('-', '').replace('_', '')
                    font_base_simple_normalized = font_base_simple.lower().replace(' ', '').replace('-', '').replace('_', '')
                    file_base_normalized = file_base_lower.replace(' ', '').replace('-', '').replace('_', '')

                    # Prioridade 1: Correspondência exata (mais específica)
                    if font_name_normalized == file_base_normalized:
                        font_path = os.path.join(font_dir, file)
                        if os.path.isfile(font_path):
                            font_paths.insert(0, font_path)  # Inserir no início (prioridade)
                            continue

                    # Prioridade 2: Correspondência com base nome (ex: ArialMT → arialmt)
                    if font_base_normalized == file_base_normalized:
                        font_path = os.path.join(font_dir, file)
                        if os.path.isfile(font_path):
                            if font_path not in font_paths:
                                font_paths.append(font_path)
                            continue

                    # Prioridade 3: Busca específica para fontes Arial
                    if 'arial' in font_name_normalized:
                        # ArialMT deve corresponder a arquivos com "mt" mas não "narrow" ou "bold"
                        if 'mt' in font_name_normalized and 'narrow' not in font_name_normalized:
                            if 'mt' in file_base_normalized and 'narrow' not in file_base_normalized and 'bold' not in file_base_normalized:
                                font_path = os.path.join(font_dir, file)
                                if os.path.isfile(font_path) and font_path not in font_paths:
                                    font_paths.append(font_path)
                                    continue
                        # ArialNarrow-Bold deve corresponder a arquivos com "narrow" E "bold"
                        elif 'narrow' in font_name_normalized and 'bold' in font_name_normalized:
                            if 'narrow' in file_base_normalized and ('bold' in file_base_normalized or 'bd' in file_base_normalized or 'black' in file_base_normalized):
                                font_path = os.path.join(font_dir, file)
                                if os.path.isfile(font_path) and font_path not in font_paths:
                                    font_paths.insert(0, font_path)  # Prioridade alta
                                    continue
                            # Também tentar buscar arquivo específico "arial_narrow_bold" ou similar
                            if 'narrow' in file_base_normalized and 'bold' in file_base_normalized:
                                font_path = os.path.join(font_dir, file)
                                if os.path.isfile(font_path) and font_path not in font_paths:
                                    font_paths.insert(0, font_path)
                                    continue
                        # ArialNarrow (sem bold) deve corresponder a arquivos com "narrow" mas SEM "bold"
                        elif 'narrow' in font_name_normalized and 'bold' not in font_name_normalized:
                            if 'narrow' in file_base_normalized and 'bold' not in file_base_normalized:
                                font_path = os.path.join(font_dir, file)
                                if os.path.isfile(font_path) and font_path not in font_paths:
                                    font_paths.append(font_path)
                                    continue

                    # Prioridade 4: Correspondência parcial (menos específica)
                    for pattern in [font_name_normalized, font_base_normalized, font_base_simple_normalized]:
                        if pattern and (pattern in file_base_normalized or file_base_normalized in pattern):
                            font_path = os.path.join(font_dir, file)
                            if os.path.isfile(font_path) and font_path not in font_paths:
                                font_paths.append(font_path)
                                break
            except (PermissionError, OSError):
                # Ignorar erros de permissão ou acesso
                continue

        return font_paths

    def get_font_for_text_object(self, font_name: str, fonts_dict: Dict[str, ExtractedFont]) -> Tuple[Optional[fitz.Font], str]:
        """
        Tenta obter uma fonte PyMuPDF para um objeto de texto, usando fontes extraídas.

        Tenta múltiplas estratégias:
        1. Usar fonte embeddada do PDF original se disponível
        2. Tentar carregar fonte do sistema usando nome extraído
        3. Tentar mapeamento inteligente para fontes padrão
        4. Fallback para Helvetica apenas como último recurso

        Args:
            font_name: Nome da fonte original (ex: "ArialMT")
            fonts_dict: Dicionário de fontes extraídas do PDF

        Returns:
            Tuple[Optional[fitz.Font], str]: (Fonte carregada ou None, fonte source: "extracted"/"system"/"fallback")
        """
        extracted_font = fonts_dict.get(font_name)

        # Estratégia 1: Usar fonte embeddada do PDF se disponível
        if extracted_font and extracted_font.font_file_path:
            try:
                # Tentar carregar fonte do arquivo extraído
                font = fitz.Font(fontfile=extracted_font.font_file_path)
                return font, "extracted"
            except Exception:
                # Se falhar, tentar próximo método
                pass

        # Estratégia 2: Tentar carregar fonte do sistema usando busca de arquivos
        if font_name:
            # PyMuPDF não acessa diretamente fontes do sistema via nome
            # Precisamos buscar arquivos de fonte no sistema
            font_paths = self._find_system_font(font_name)
            for font_path in font_paths:
                try:
                    # Tentar carregar fonte do arquivo
                    # Isso permitirá embeddagem posterior
                    font = fitz.Font(fontfile=font_path)
                    # Marcar caminho do arquivo para embeddagem posterior
                    # PyMuPDF não armazena caminho automaticamente, precisamos guardar
                    font._fontfile = font_path  # Atributo customizado para nosso uso
                    font._original_fontfile_path = font_path  # Backup
                    return font, "system"
                except Exception:
                    continue

            # Se não encontrou arquivo, tentar diretamente com nome (pode funcionar em alguns casos)
            # Mas isso geralmente não funciona para fontes customizadas
            try:
                font = fitz.Font(fontname=font_name)
                return font, "system"
            except Exception:
                pass

        # Estratégia 3: Mapeamento inteligente baseado no nome da fonte
        font_mapping = {
            # Arial family
            "ArialMT": ("helv", False),  # Arial -> Helvetica
            "Arial": ("helv", False),
            "ArialNarrow": ("helv", False),
            "Arial-Bold": ("hebo", True),
            "ArialNarrow-Bold": ("hebo", True),
            "Arial-Black": ("hebo", True),
            # Times family
            "Times": ("tiro", False),
            "Times-Roman": ("tiro", False),
            "TimesNewRoman": ("tiro", False),
            "Times-Bold": ("tibd", True),
            "Times-BoldItalic": ("tibii", True),
            "Times-Italic": ("tiit", True),
            # Courier family
            "Courier": ("cour", False),
            "Courier-Bold": ("cobo", True),
            "Courier-Oblique": ("coit", True),
            "Courier-BoldOblique": ("cobit", True),
        }

        # Tentar mapeamento direto
        if font_name in font_mapping:
            mapped_name, needs_bold = font_mapping[font_name]
            try:
                font = fitz.Font(mapped_name)
                # Se precisa bold, aplicar (nota: PyMuPDF não permite modificar is_bold diretamente)
                # O mapeamento já escolhe a fonte correta (ex: hebo para bold)
                if needs_bold and hasattr(font, 'is_bold'):
                    # PyMuPDF pode não suportar aplicar bold diretamente
                    # Tentar versão bold se disponível
                    try:
                        if mapped_name == "helv":
                            font = fitz.Font("hebo")  # Helvetica Bold
                    except:
                        pass
                return font, "fallback"
            except Exception:
                pass

        # Estratégia 4: Mapeamento baseado em padrões no nome
        name_upper = font_name.upper()

        # Detectar família Arial
        if "ARIAL" in name_upper:
            if "BOLD" in name_upper or "BLACK" in name_upper:
                try:
                    return fitz.Font("hebo"), "fallback"  # Helvetica Bold
                except:
                    pass
            try:
                return fitz.Font("helv"), "fallback"  # Helvetica
            except:
                pass

        # Detectar família Times
        if "TIMES" in name_upper:
            if "BOLD" in name_upper and "ITALIC" in name_upper:
                try:
                    return fitz.Font("tibii"), "fallback"  # Times Bold Italic
                except:
                    pass
            if "BOLD" in name_upper:
                try:
                    return fitz.Font("tibd"), "fallback"  # Times Bold
                except:
                    pass
            if "ITALIC" in name_upper:
                try:
                    return fitz.Font("tiit"), "fallback"  # Times Italic
                except:
                    pass
            try:
                return fitz.Font("tiro"), "fallback"  # Times Roman
            except:
                pass

        # Detectar família Courier
        if "COURIER" in name_upper:
            if "BOLD" in name_upper and "OBLIQUE" in name_upper or "ITALIC" in name_upper:
                try:
                    return fitz.Font("cobit"), "fallback"  # Courier Bold Oblique
                except:
                    pass
            if "BOLD" in name_upper:
                try:
                    return fitz.Font("cobo"), "fallback"  # Courier Bold
                except:
                    pass
            if "OBLIQUE" in name_upper or "ITALIC" in name_upper:
                try:
                    return fitz.Font("coit"), "fallback"  # Courier Oblique
                except:
                    pass
            try:
                return fitz.Font("cour"), "fallback"  # Courier
            except:
                pass

        # Último recurso: Helvetica (fallback mínimo)
        try:
            return fitz.Font("helv"), "fallback"
        except:
            return None, "none"

    def embed_font(self, page: fitz.Page, font: fitz.Font, font_name: str) -> Optional[str]:
        """
        Embedda uma fonte na página do PDF usando insert_font.

        PyMuPDF embedda automaticamente fontes quando usadas via insert_text,
        mas podemos usar insert_font na página para garantir embeddagem prévia.

        Args:
            page: Página do PDF (fitz.Page) onde a fonte será usada
            font: Fonte PyMuPDF já carregada
            font_name: Nome da fonte para referência

        Returns:
            Optional[str]: Nome seguro da fonte para usar no insert_text, ou None se não conseguir
        """
        try:
            # Obter caminho do arquivo da fonte se disponível
            font_file_path = None
            if hasattr(font, '_fontfile') and font._fontfile:
                font_file_path = font._fontfile
            elif hasattr(font, '_original_fontfile_path') and font._original_fontfile_path:
                font_file_path = font._original_fontfile_path

            # Se temos caminho de arquivo válido, usar insert_font para embeddar
            if font_file_path and os.path.isfile(font_file_path):
                try:
                    # Nome seguro para uso no PDF (sem espaços, caracteres especiais)
                    safe_font_name = font_name.replace(' ', '').replace('-', '').replace('_', '')
                    # Usar insert_font na página para embeddar a fonte
                    # Retorna xref (número) do objeto de fonte, não o nome
                    # O nome que passamos (safe_font_name) é o que usaremos no insert_text
                    xref = page.insert_font(fontname=safe_font_name, fontfile=font_file_path)
                    if xref:
                        # Retornar o nome seguro (que passamos), não o xref
                        return safe_font_name
                    return safe_font_name
                except Exception as e:
                    # Se falhar (ex: fonte já embeddada), PyMuPDF tentará embeddar automaticamente ao usar
                    pass

            # Se não tem arquivo, PyMuPDF embedda automaticamente ao usar a fonte no insert_text
            # Retornar None para indicar que precisa usar embeddagem automática
            return None
        except Exception:
            # Se falhar completamente, PyMuPDF fará embeddagem automática ao usar a fonte
            return None

    def extract_image_objects(self) -> List[ImageObject]:
        """
        Extrai todas as imagens do PDF.

        Returns:
            List[ImageObject]: Lista de imagens extraídas.
        """
        doc = self.open()
        image_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Buscar posição da imagem na página
                image_rects = page.get_image_rects(xref)

                for rect in image_rects:
                    img_obj = ImageObject(
                        page=page_num,
                        mime_type=f"image/{image_ext}",
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        data_base64=base64.b64encode(image_bytes).decode("utf-8")
                    )
                    image_objects.append(img_obj)

        return image_objects

    def extract_link_objects(self) -> List[LinkObject]:
        """
        Extrai todos os links do PDF.

        Returns:
            List[LinkObject]: Lista de links extraídos.
        """
        doc = self.open()
        link_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            links = page.get_links()

            for link in links:
                link_obj = LinkObject(
                    page=page_num,
                    url=link.get("uri", ""),
                    x=link.get("from", fitz.Rect(0, 0, 0, 0)).x0,
                    y=link.get("from", fitz.Rect(0, 0, 0, 0)).y0,
                    width=link.get("from", fitz.Rect(0, 0, 0, 0)).width,
                    height=link.get("from", fitz.Rect(0, 0, 0, 0)).height,
                    link_type="uri"
                )
                link_objects.append(link_obj)

        return link_objects

    def extract_annotation_objects(self) -> List:
        """
        Extrai todas as anotações do PDF.

        Returns:
            List: Lista de anotações extraídas (HighlightAnnotation, CommentAnnotation, etc.).
        """
        doc = self.open()
        annotation_objects = []

        for page_num in range(len(doc)):
            page = doc[page_num]
            annots = page.annots()

            for annot in annots:
                annot_type = annot.type[1] if annot.type else ""
                info = annot.info
                rect = annot.rect

                if annot_type == "Highlight":
                    annot_obj = HighlightAnnotation(
                        page=page_num,
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        color=info.get("color", "#FFFF00"),
                        text=info.get("content", "")
                    )
                    annotation_objects.append(annot_obj)
                elif annot_type == "Text" or annot_type == "FreeText":
                    annot_obj = CommentAnnotation(
                        page=page_num,
                        x=rect.x0,
                        y=rect.y0,
                        width=rect.width,
                        height=rect.height,
                        author=info.get("title", ""),
                        content=info.get("content", ""),
                        date=info.get("modDate", "")
                    )
                    annotation_objects.append(annot_obj)

        return annotation_objects

    def save(self, output_path: Optional[str] = None) -> str:
        """
        Salva o documento PDF modificado.

        Args:
            output_path: Caminho de saída. Se None, sobrescreve o original.

        Returns:
            str: Caminho do arquivo salvo.
        """
        doc = self.open()
        if output_path is None:
            output_path = str(self.pdf_path)
        else:
            output_path = str(Path(output_path))

        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        return output_path

    def merge_pdfs(self, pdf_paths: List[str]) -> fitz.Document:
        """
        Une múltiplos PDFs em um único documento.

        Args:
            pdf_paths: Lista de caminhos para os PDFs a serem unidos.

        Returns:
            fitz.Document: Documento PDF resultante da união.

        Raises:
            PDFFileNotFoundError: Se algum PDF não for encontrado.
        """
        # Validar todos os PDFs
        for pdf_path in pdf_paths:
            if not Path(pdf_path).exists():
                raise PDFFileNotFoundError(str(pdf_path))

        # Abrir PDF de base (este)
        merged_doc = fitz.open(str(self.pdf_path))

        # Inserir páginas dos outros PDFs
        for pdf_path in pdf_paths:
            if str(pdf_path) != str(self.pdf_path):
                other_doc = fitz.open(str(pdf_path))
                merged_doc.insert_pdf(other_doc)
                other_doc.close()

        return merged_doc

    def delete_pages(self, page_numbers: List[int]) -> fitz.Document:
        """
        Exclui páginas específicas do PDF.

        Args:
            page_numbers: Lista de números de páginas a serem excluídas (0-indexed).

        Returns:
            fitz.Document: Documento PDF modificado.

        Raises:
            InvalidPageError: Se algum número de página for inválido.
        """
        doc = self.open()
        max_pages = len(doc)

        # Validar páginas
        for page_num in page_numbers:
            if page_num < 0 or page_num >= max_pages:
                raise InvalidPageError(page_num, max_pages)

        # Ordenar páginas em ordem decrescente para deletar corretamente
        sorted_pages = sorted(set(page_numbers), reverse=True)

        # Criar novo documento com páginas mantidas
        new_doc = fitz.open()
        pages_to_keep = [i for i in range(max_pages) if i not in set(page_numbers)]

        for page_num in pages_to_keep:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

        doc.close()
        self._doc = new_doc
        return new_doc

    def split_pages(self, ranges: List[tuple]) -> List[fitz.Document]:
        """
        Divide o PDF em múltiplos documentos conforme faixas de páginas.

        Args:
            ranges: Lista de tuplas (start, end) indicando faixas de páginas (0-indexed).

        Returns:
            List[fitz.Document]: Lista de documentos PDF resultantes.
        """
        doc = self.open()
        result_docs = []

        for start, end in ranges:
            if start < 0 or end >= len(doc) or start > end:
                raise InvalidPageError(start, len(doc))

            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=start, to_page=end)
            result_docs.append(new_doc)

        return result_docs

    def create_backup(self, backup_path: Optional[str] = None) -> str:
        """
        Cria um backup do arquivo PDF original.

        Args:
            backup_path: Caminho do backup. Se None, usa nome automático.

        Returns:
            str: Caminho do arquivo de backup criado.
        """
        if backup_path is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = str(self.pdf_path.parent / f"{self.pdf_path.stem}_backup_{timestamp}.pdf")

        shutil.copy2(str(self.pdf_path), backup_path)
        return backup_path

    def __enter__(self):
        """Context manager: abre o documento."""
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: fecha o documento."""
        self.close()
