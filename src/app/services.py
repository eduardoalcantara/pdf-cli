"""
Casos de uso e funções core do PDF-cli - Fase 3.

Este módulo contém a lógica de negócio (casos de uso) para todas as
operações principais do PDF-cli conforme especificações da Fase 3.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple, Callable
import json
import shutil
import time
from datetime import datetime

from core.models import (
    TextObject, ImageObject, TableObject, LinkObject,
    FormFieldObject, CheckboxFieldObject, RadioButtonFieldObject, SignatureFieldObject,
    LineObject, RectangleObject, EllipseObject, PolylineObject, BezierCurveObject,
    HighlightAnnotation, CommentAnnotation, MarkerAnnotation,
    LayerObject, FilterObject
)
from core.exceptions import (
    PDFFileNotFoundError, PDFMalformedError, TextNotFoundError,
    InvalidPageError, PaddingError, PDFCliException
)
from core.font_manager import FontManager, FontMatchQuality
from core.engine_manager import EngineManager
from core.engine_manager import EngineManager, EngineResult, EngineType, create_audit_log
import fitz  # PyMuPDF
from app.pdf_repo import PDFRepository
from app.logging import get_logger


# ============================================================================
# EXTRAÇÃO DE OBJETOS
# ============================================================================

def _normalize_font_name(font_name: str) -> str:
    """
    Normaliza o nome da fonte removendo prefixos de subset.

    Os PDFs com fontes subset usam prefixos como "EAAAAB+SegoeUI-Bold",
    mas os objetos de texto extraídos usam apenas "SegoeUI-Bold".
    Esta função remove o prefixo para permitir correspondência correta.

    Args:
        font_name: Nome da fonte (pode conter prefixo de subset)

    Returns:
        str: Nome da fonte sem prefixo de subset

    Exemplos:
        "EAAAAB+SegoeUI-Bold" -> "SegoeUI-Bold"
        "ABCDEF+Times-Roman" -> "Times-Roman"
        "ArialMT" -> "ArialMT"
        "Courier" -> "Courier"
    """
    if not font_name:
        return font_name

    # Padrão: prefixo de subset é sempre seguido de "+"
    # Formato típico: "EAAAAB+SegoeUI-Bold" ou "ABCDEF+FontName"
    if '+' in font_name:
        # Pegar tudo depois do "+"
        parts = font_name.split('+', 1)
        if len(parts) > 1:
            return parts[1]

    return font_name


def export_objects(
    pdf_path: str,
    output_path: str,
    types: Optional[List[str]] = None,
    include_fonts: bool = False
) -> Dict[str, Any]:
    """
    Extrai e exporta objetos do PDF para JSON.

    Conforme Fase 3: export-objects
    Permite especificar quais tipos de objetos exportar via parâmetro --types.

    Args:
        pdf_path: Caminho para o arquivo PDF.
        output_path: Caminho de saída para o JSON.
        types: Lista de tipos a exportar (text, image, table, etc.). Se None, exporta todos.

    Returns:
        dict: Estatísticas da extração (contadores por tipo/página).
    """
    logger = get_logger()

    with PDFRepository(pdf_path) as repo:
        all_objects: Dict[str, List[Any]] = {
            "text": [],
            "image": [],
            "table": [],
            "link": [],
            "formfield": [],
            "graphic": [],
            "annotation": [],
            "layer": [],
            "filter": []
        }

        # Extrair textos
        if types is None or "text" in types:
            text_objects = repo.extract_text_objects()
            all_objects["text"] = [obj.to_dict() for obj in text_objects]

        # Extrair imagens
        if types is None or "image" in types:
            image_objects = repo.extract_image_objects()
            all_objects["image"] = [obj.to_dict() for obj in image_objects]

        # Extrair links
        if types is None or "link" in types:
            try:
                link_objects = repo.extract_link_objects()
                all_objects["link"] = [obj.to_dict() for obj in link_objects]
            except Exception:
                pass  # Links podem não estar disponíveis em todos PDFs

        # Extrair anotações
        if types is None or "annotation" in types:
            try:
                annotation_objects = repo.extract_annotation_objects()
                all_objects["annotation"] = [obj.to_dict() for obj in annotation_objects]
            except Exception:
                pass

        # Table, formfield, graphic, layer, filter requerem algoritmos mais complexos
        # de detecção e parsing. Podem ser implementados em fases futuras conforme necessidade.

        # Extrair fontes se solicitado
        fonts_info = None
        if include_fonts:
            fonts_dict = repo.extract_fonts()
            text_objects_for_stats = repo.extract_text_objects()

            # Estatísticas de uso por fonte (normalizar nomes para correspondência)
            font_stats = {}
            for text_obj in text_objects_for_stats:
                font_name = text_obj.font_name
                # Normalizar nome para garantir correspondência
                normalized_name = _normalize_font_name(font_name)
                if normalized_name not in font_stats:
                    font_stats[normalized_name] = {
                        "pages": set(),
                        "sizes": set(),
                        "occurrences": 0
                    }
                font_stats[normalized_name]["pages"].add(text_obj.page)
                font_stats[normalized_name]["sizes"].add(text_obj.font_size)
                font_stats[normalized_name]["occurrences"] += 1

            # Preparar informações de fontes
            fonts_list = []
            for font_key, font_data in fonts_dict.items():
                # Normalizar nome da fonte extraída para corresponder às estatísticas
                normalized_font_name = _normalize_font_name(font_data.name)
                usage = font_stats.get(normalized_font_name, {})
                name_upper = font_data.name.upper() if font_data.name else ""
                variants = []
                if font_data.is_bold:
                    variants.append("Bold")
                if font_data.is_italic:
                    variants.append("Italic")
                if "NARROW" in name_upper:
                    variants.append("Narrow")
                if "CONDENSED" in name_upper:
                    variants.append("Condensed")
                if "LIGHT" in name_upper:
                    variants.append("Light")
                if "BLACK" in name_upper:
                    variants.append("Black")

                fonts_list.append({
                    "name": font_data.name,  # Nome original (com prefixo se houver)
                    "base_font": font_data.base_font,
                    "normalized_name": normalized_font_name,  # Nome sem prefixo
                    "variants": variants,
                    "embedded": font_data.font_file_path is not None,
                    "encoding": getattr(font_data, 'encoding', ''),
                    "usage": {
                        "occurrences": usage.get("occurrences", 0),
                        "pages": sorted(list(usage.get("pages", set()))),
                        "sizes": sorted(list(usage.get("sizes", set())))
                    }
                })

            fonts_info = {
                "total_fonts": len(fonts_list),
                "fonts": sorted(fonts_list, key=lambda x: x["name"] or "")
            }

        # Agrupar por página
        grouped = {}
        for obj_type, objects in all_objects.items():
            if objects:
                for obj in objects:
                    page = obj.get("page", 0)
                    if page not in grouped:
                        grouped[page] = {}
                    if obj_type not in grouped[page]:
                        grouped[page][obj_type] = []
                    grouped[page][obj_type].append(obj)

        # Preparar dados para salvar
        output_data = grouped.copy()
        if include_fonts and fonts_info:
            output_data["_fonts"] = fonts_info

        # Salvar JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        # Estatísticas
        stats = {
            "total_objects": sum(len(objs) for objs in all_objects.values()),
            "by_type": {t: len(objs) for t, objs in all_objects.items()},
            "by_page": {str(p): sum(len(objs) for objs in types.values()) for p, types in grouped.items()}
        }

        if include_fonts and fonts_info:
            stats["fonts"] = fonts_info

        # Log da operação
        logger.log_operation(
            operation_type="export-objects",
            input_file=pdf_path,
            output_file=output_path,
            parameters={"types": types},
            result=stats
        )

        return stats


# ============================================================================
# EDIÇÃO DE OBJETOS
# ============================================================================

def _edit_text_all_occurrences(
    pdf_path: str,
    output_path: str,
    search_term: str,
    new_content: str,
    align: Optional[str] = None,
    pad: bool = False,
    font_name: Optional[str] = None,
    font_size: Optional[int] = None,
    color: Optional[str] = None,
    rotation: Optional[float] = None,
    create_backup: bool = True,
    feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    prefer_engine: str = "pymupdf",
    strict_fonts: bool = False
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Função auxiliar para editar todas as ocorrências de um texto.

    Processa todas as ocorrências do search_term no PDF e substitui por new_content,
    preservando o texto completo quando search_term é uma substring.

    Conforme Fase 5: Integra engine manager para detecção de fallback de fonte.

    Args:
        feedback_callback: Função opcional chamada após cada ocorrência processada.
                          Recebe um dict com: id, page, coordinates, original_content,
                          new_content, font_original, font_used, font_fallback, changes
        prefer_engine: Engine preferido ("pymupdf" ou "pypdf")

    Returns:
        tuple[str, List[Dict]]: (caminho_do_arquivo, lista_de_detalhes_das_ocorrências)
    """
    logger = get_logger()

    # Inicializar engine manager (Fase 5)
    engine_manager = EngineManager(prefer_engine=prefer_engine)

    # Inicializar font manager para rastrear fontes
    font_manager = FontManager()

    # Criar backup se solicitado
    backup_path = None
    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # Extrair objetos de texto ORIGINAIS antes da edição (para comparação de fontes)
    original_text_objects = []
    with PDFRepository(pdf_path) as repo:
        original_text_objects = repo.extract_text_objects()

    # Filtrar apenas objetos que contêm o search_term (serão modificados)
    target_objects = [obj for obj in original_text_objects if search_term in obj.content]
    target_object_ids = [obj.id for obj in target_objects]

    # Sempre usar arquivo temporário para evitar problemas de lock no Windows
    # PyMuPDF com incremental=False não pode salvar no mesmo arquivo que foi aberto
    import tempfile
    output_path_obj = Path(output_path)

    # Criar dois arquivos temporários: um para trabalhar e outro para salvar
    working_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=output_path_obj.parent)
    working_temp.close()
    working_temp_path = working_temp.name

    save_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=output_path_obj.parent)
    save_temp.close()
    save_temp_path = save_temp.name

    final_output_path = str(output_path_obj)

    # Copiar arquivo para arquivo temporário de trabalho
    shutil.copy(pdf_path, working_temp_path)

    # Contador de ocorrências processadas
    occurrences_processed = 0
    processed_ids = []
    occurrences_details = []  # Lista de detalhes de cada ocorrência processada

    # Abrir documento UMA VEZ e processar todas as ocorrências
    # Isso evita problemas de lock de arquivo no Windows e é mais eficiente (DRY)
    with PDFRepository(working_temp_path) as repo:
        doc = repo.open()

        # OPÇÃO 1 + 2: Extrair fontes originais do PDF antes da edição
        # Isso permite usar fontes embeddadas e fazer mapeamento inteligente
        fonts_dict = repo.extract_fonts()
        logger.log_operation(
            operation_type="extract-fonts",
            input_file=pdf_path,
            output_file=None,
            parameters={"fonts_found": len(fonts_dict)},
            result={"font_names": list(fonts_dict.keys())},
            status="info",
            notes=f"Extraídas {len(fonts_dict)} fontes do PDF original para preservação"
        )

        # Cache de fontes carregadas (para reutilização)
        font_cache = {}

        # Preparar cor (reutilizável)
        color_rgb = (0, 0, 0)
        if color:
            hex_color = color.lstrip("#")
            if len(hex_color) == 6:
                color_rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

        # Processar ocorrências em loop até não encontrar mais
        while True:
            # Extrair textos (necessário recarregar para ver mudanças após redaction)
            text_objects = repo.extract_text_objects()

            # Encontrar próxima ocorrência
            target_obj = None
            for obj in text_objects:
                # Ignorar objetos já processados (por ID)
                if obj.id in processed_ids:
                    continue
                # Buscar ocorrência que contém o search_term
                if search_term in obj.content:
                    target_obj = obj
                    break

            # Se não encontrou mais ocorrências, parar
            if target_obj is None:
                break

            # Marcar como processado
            processed_ids.append(target_obj.id)
            occurrences_processed += 1

            # Determinar conteúdo final (substituição parcial ou completa)
            original_content = target_obj.content
            if search_term in original_content and search_term != original_content:
                # Substituição parcial: preservar texto completo, substituir apenas substring
                final_content = original_content.replace(search_term, new_content, 1)
            else:
                # Substituição completa
                final_content = new_content

            # Determinar propriedades finais
            final_font = target_obj.font_name if not font_name else font_name
            # IMPORTANTE: Preservar tamanho visual, não apenas tamanho em pontos
            # Se font_size não foi especificado, usar o tamanho original
            # Mas também considerar altura visual do texto original
            original_height = target_obj.height
            original_font_size = target_obj.font_size
            final_font_size = target_obj.font_size if font_size is None else font_size
            final_rotation = target_obj.rotation if rotation is None else rotation

            # OPÇÃO 1 + 2: Carregar fonte usando extração e embeddagem
            font_loaded = None
            font_source = "unknown"
            font_fallback_occurred = False

            # Tentar obter fonte do cache primeiro
            if final_font and final_font in font_cache:
                font_loaded = font_cache[final_font]
                font_source = "cache"
            else:
                # Usar nova função que tenta múltiplas estratégias
                font_loaded, font_source = repo.get_font_for_text_object(final_font, fonts_dict)

                if font_loaded:
                    # Detectar se é fonte embeddada (melhor opção)
                    if final_font in fonts_dict and fonts_dict[final_font].font_file_path:
                        font_source = "embedded"

                    # Cachear fonte para reutilização
                    if final_font:
                        font_cache[final_font] = font_loaded

                    # Verificar se houve fallback e registrar no font_manager
                    # Se a fonte usada não corresponde exatamente à original, houve fallback
                    if font_source in ["system", "extracted", "fallback", "cache"] and final_font:
                        # Verificar se nome da fonte carregada corresponde
                        loaded_font_name = font_loaded.name if hasattr(font_loaded, 'name') else ""
                        font_name_matches = (loaded_font_name.lower() in final_font.lower() or
                                           final_font.lower() in loaded_font_name.lower())

                        # Determinar qualidade da correspondência para font_manager
                        if font_source == "extracted" or font_source == "embedded":
                            match_quality = FontMatchQuality.EXACT
                        elif font_name_matches and font_source in ["system", "cache"]:
                            match_quality = FontMatchQuality.EXACT
                        elif font_source in ["system", "cache"] and not font_name_matches:
                            # Fonte do sistema mas nome não corresponde = variante
                            match_quality = FontMatchQuality.VARIANT
                        elif font_source == "fallback":
                            # Fallback explícito = fonte faltante
                            match_quality = FontMatchQuality.FALLBACK
                        else:
                            match_quality = FontMatchQuality.SIMILAR

                        # Registrar no font_manager apenas se não for correspondência exata
                        if match_quality != FontMatchQuality.EXACT:
                            font_manager.add_requirement(
                                font_name=final_font,
                                found_font=loaded_font_name,
                                match_quality=match_quality,
                                system_path=getattr(font_loaded, '_fontfile', None),
                                page=target_obj.page
                            )

                        if not font_name_matches:
                            # Nome não corresponde - indica fallback
                            if font_source != "embedded":
                                font_fallback_occurred = True
                                if font_source not in ["fallback"]:
                                    font_source = "fallback"  # Marcar como fallback se nome não corresponde
                else:
                    # Falha total
                    font_source = "none"
                    font_fallback_occurred = True
                    # Registrar fonte faltante
                    font_manager.add_requirement(
                        font_name=final_font,
                        found_font=None,
                        match_quality=FontMatchQuality.MISSING,
                        page=target_obj.page
                    )

            # IMPORTANTE: Ajustar tamanho da fonte para preservar altura visual
            # Se a fonte mudou (fallback ou sistema), pode ter métricas diferentes
            # Calcular tamanho necessário baseado na altura original real
            # Ajuste será aplicado se:
            # 1. Fonte mudou (system ou fallback) OU
            # 2. Fonte foi carregada mas nome não corresponde (indica fallback)
            font_changed = (font_source in ["system", "fallback"]) or (font_loaded and font_fallback_occurred)

            if font_changed and original_font_size > 0:
                try:
                    # Calcular proporção real da altura original em relação ao tamanho da fonte
                    # Isso nos diz o quão "alta" essa fonte específica é
                    height_ratio = original_height / original_font_size if original_font_size > 0 else 1.3

                    # Para preservar altura visual, calcular tamanho necessário
                    # Estratégia: preservar altura absoluta (original_height) ao invés de tamanho em pontos
                    # Se queremos altura H e nova fonte tem proporção padrão (1.2), tamanho = H / 1.2
                    standard_ratio = 1.2  # Proporção padrão altura/tamanho

                    # Calcular tamanho necessário para preservar altura original
                    adjusted_size = original_height / standard_ratio

                    # Se proporção original é significativamente diferente (>15%), usar proporção original
                    # Isso é mais preciso para fontes com métricas especiais
                    if abs(height_ratio - standard_ratio) > 0.15:
                        adjusted_size = original_height / height_ratio

                    # Limitar ajuste para não ser muito extremo (entre 0.8x e 1.3x do original)
                    # Isso previne ajustes muito grandes que podem quebrar layout
                    if adjusted_size < original_font_size * 0.8:
                        adjusted_size = original_font_size * 0.9  # Redução moderada
                    elif adjusted_size > original_font_size * 1.3:
                        adjusted_size = original_font_size * 1.15  # Aumento moderado

                    # Aplicar ajuste
                    final_font_size = max(1.0, round(adjusted_size, 1))  # Mínimo 1pt, 1 casa decimal
                except Exception as e:
                    # Se falhar, usar tamanho original
                    pass

            # Obter nome da fonte para uso no insert_text (sem espaços, sem caracteres especiais)
            if font_loaded and hasattr(font_loaded, 'name'):
                font_loaded_name = font_loaded.name
                # Remover espaços e caracteres especiais do nome para usar no insert_text
                # PyMuPDF não aceita espaços no fontname
                fontname_to_use = font_loaded_name.replace(' ', '').replace('-', '')
            else:
                fontname_to_use = final_font.replace(' ', '').replace('-', '') if final_font else "helv"

            # Preparar nome seguro para fonte (sem espaços) - será usado no insert_font
            safe_font_name = final_font.replace(' ', '').replace('-', '').replace('_', '') if final_font else fontname_to_use.replace(' ', '').replace('-', '')
            embedded_font_name = None  # Será definido após embeddagem na página

            # Determinar fonte usada para log/feedback
            display_font_name = font_loaded.name if font_loaded and hasattr(font_loaded, 'name') else (final_font or "helv")
            if font_source == "embedded":
                font_used_source = f"embeddada do PDF ({final_font})"
            elif font_source == "extracted":
                font_used_source = f"extraída ({final_font})"
            elif font_source == "system":
                font_used_source = f"sistema ({display_font_name}) - embeddada no PDF"
            elif font_source == "fallback":
                font_used_source = f"fallback padrão (Helvetica)"
                font_fallback_occurred = True
            else:
                font_used_source = f"original ({final_font})"

            # Coletar detalhes da ocorrência
            occurrence_details = {
                "id": target_obj.id,
                "page": target_obj.page,
                "coordinates": {
                    "x": round(target_obj.x, 2),
                    "y": round(target_obj.y, 2),
                    "width": round(target_obj.width, 2),
                    "height": round(target_obj.height, 2)
                },
                "original_content": original_content,
                "new_content": final_content,
                "font_original": final_font,
                "font_used": display_font_name if font_loaded and hasattr(font_loaded, 'name') else fontname_to_use,
                "font_fallback": font_fallback_occurred,
                "font_source": font_used_source,
                "font_size": final_font_size,
                "substitution_type": "parcial" if search_term in original_content and search_term != original_content else "completa",
                "changes": []
            }

            # Detectar mudanças específicas
            if original_content != final_content:
                occurrence_details["changes"].append(f"Conteúdo: '{original_content[:50]}...' → '{final_content[:50]}...'")
            if font_name and font_name != target_obj.font_name:
                occurrence_details["changes"].append(f"Fonte: {target_obj.font_name} → {font_name}")
            if font_size is not None and font_size != target_obj.font_size:
                occurrence_details["changes"].append(f"Tamanho: {target_obj.font_size}pt → {font_size}pt")
            if color and color != target_obj.color:
                occurrence_details["changes"].append(f"Cor: {target_obj.color} → {color}")
            if align and align != target_obj.align:
                occurrence_details["changes"].append(f"Alinhamento: {target_obj.align or 'default'} → {align}")

            occurrences_details.append(occurrence_details)

            # Chamar callback de feedback se fornecido
            if feedback_callback:
                feedback_callback(occurrence_details)

            # Aplicar edição no PDF
            page = doc[target_obj.page]

            # Embeddar fonte na página ANTES de usar (se for fonte do sistema)
            # IMPORTANTE: safe_font_name já foi definido acima usando final_font
            # Precisamos embeddar usando esse nome e depois usar o MESMO nome no insert_text
            if font_loaded and font_source in ["system"] and hasattr(font_loaded, '_fontfile') and font_loaded._fontfile:
                try:
                    # Embeddar usando o nome seguro (final_font sem espaços/hífens)
                    # Isso garante que o nome usado no insert_font seja o mesmo do insert_text
                    embedded_font_name = repo.embed_font(page, font_loaded, final_font)
                    # Se embeddagem foi bem-sucedida, usar o nome retornado (que é o safe_font_name)
                    if embedded_font_name:
                        safe_font_name = embedded_font_name  # Usar nome embeddado
                    # Se não retornou nome mas embeddagem pode ter funcionado, manter safe_font_name
                except Exception as e:
                    # Se falhar ao embeddar, continuar com nome seguro original
                    pass

            # Remover texto antigo usando redaction
            bbox = fitz.Rect(target_obj.x, target_obj.y, target_obj.x + target_obj.width, target_obj.y + target_obj.height)
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # SOLUÇÃO DEFINITIVA: Usar TextWriter ao invés de insert_text
            # TextWriter suporta fontes customizadas diretamente via objeto Font
            # Isso preserva a fonte original sem fallback para Helvetica
            try:
                # Criar TextWriter para a página
                tw = fitz.TextWriter(page.rect)

                # IMPORTANTE: Calcular posição correta
                # TextWriter usa coordenadas (x, y) onde y é a baseline do texto
                # target_obj.y é o topo da bounding box
                # Baseline ≈ topo + (altura * 0.82) para fontes padrão
                baseline_y = target_obj.y + (original_height * 0.82)

                # Usar objeto Font diretamente (não nome!)
                # Isso é a chave para preservar fontes customizadas
                if font_loaded:
                    # Usar fonte carregada (do sistema ou extraída)
                    # TextWriter.append() não aceita 'color' e 'rotate' diretamente
                    # Usar apenas: pos, text, font, fontsize
                    tw.append(
                        pos=(target_obj.x, baseline_y),
                        text=final_content,
                        font=font_loaded,  # Objeto Font, não string!
                        fontsize=final_font_size
                    )
                    # Aplicar cor após append se necessário
                    # TextWriter usa fill_color separadamente
                    tw.fill_opacity = 1.0
                else:
                    # Fallback: usar fonte padrão Helvetica
                    fallback_font = fitz.Font("helv")
                    tw.append(
                        pos=(target_obj.x, baseline_y),
                        text=final_content,
                        font=fallback_font,
                        fontsize=final_font_size
                    )
                    font_fallback_occurred = True
                    font_source = "fallback"
                    font_used_source = "fallback padrão (Helvetica)"

                # Escrever texto na página
                tw.write_text(page)

            except Exception as e:
                # Se TextWriter falhar, tentar insert_text como último recurso
                # Logger não tem método error, usar log_operation com status error
                try:
                    baseline_y = target_obj.y + (original_height * 0.82)
                    page.insert_text(
                        point=(target_obj.x, baseline_y),
                        text=final_content,
                        fontsize=final_font_size,
                        fontname="helv",  # Fallback seguro
                        color=color_rgb,
                        rotate=final_rotation
                    )
                    font_fallback_occurred = True
                    font_source = "fallback"
                    font_used_source = "fallback padrão (Helvetica) - TextWriter falhou"
                except Exception as e2:
                    raise Exception(f"Erro crítico ao inserir texto: {e2}")

        # Salvar PDF APENAS UMA VEZ após todas as edições (em arquivo temporário diferente do que foi aberto)
        # PyMuPDF requer salvar em arquivo diferente quando incremental=False
        doc.save(save_temp_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        # O context manager fechará o documento automaticamente ao sair do bloco 'with'

    # Limpar arquivo temporário de trabalho e mover arquivo salvo para o nome final
    try:
        # Remover arquivo temporário de trabalho
        if Path(working_temp_path).exists():
            Path(working_temp_path).unlink()

        # Mover arquivo salvo para o nome final
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        if output_path_obj.exists():
            output_path_obj.unlink()
        shutil.move(save_temp_path, final_output_path)
        output_path = final_output_path
    except Exception as e:
        # Se não conseguir mover, logar erro mas continuar com arquivo temporário
        logger.log_operation(
            operation_type="edit-text",
            input_file=pdf_path,
            output_file=save_temp_path,
            parameters={"warning": f"Arquivo temporário não pôde ser movido para {final_output_path}: {str(e)}"},
            status="warning"
        )
        output_path = save_temp_path
        # Tentar limpar arquivo temporário de trabalho
        try:
            if Path(working_temp_path).exists():
                Path(working_temp_path).unlink()
        except:
            pass

    # Fase 5: Detectar fallback de fonte após edição e aplicar fallback automático
    engine_results = []
    start_time_pymupdf = time.time()

    try:
        # Extrair objetos MODIFICADOS após edição para comparação
        modified_text_objects = []
        with PDFRepository(output_path) as repo:
            modified_text_objects = repo.extract_text_objects()

        # Verificar preservação de fontes após edição com PyMuPDF
        font_comparisons = engine_manager.detect_font_fallback(
            original_objects=original_text_objects,
            modified_objects=modified_text_objects,
            target_object_ids=target_object_ids,
            search_term=search_term,  # Texto buscado para melhor correspondência
            new_content=new_content   # Novo conteúdo para validação
        )

        fallback_detected = any(comp.font_fallback_detected for comp in font_comparisons)
        execution_time_pymupdf = (time.time() - start_time_pymupdf) * 1000

        # Criar resultado do PyMuPDF
        pymupdf_result = EngineResult(
            engine=EngineType.PYMUPDF,
            success=True,
            output_path=output_path,
            font_comparisons=font_comparisons,
            execution_time_ms=execution_time_pymupdf
        )
        engine_manager.attempts.append(pymupdf_result)
        engine_results.append(pymupdf_result)

        # Se houve fallback e prefer_engine é pymupdf, tentar pypdf automaticamente
        if fallback_detected and prefer_engine.lower() == "pymupdf":
            logger.log_operation(
                operation_type="edit-text-font-fallback-detected",
                input_file=pdf_path,
                output_file=output_path,
                parameters={
                    "fallback_detected": True,
                    "occurrences_with_fallback": sum(1 for comp in font_comparisons if comp.font_fallback_detected),
                    "attempting_fallback_to": "pypdf"
                },
                status="info",
                notes=f"Fallback de fonte detectado. Tentando com pypdf automaticamente..."
            )

            # Tentar edição com pypdf
            pypdf_result = engine_manager.edit_text_with_pypdf(
                pdf_path=pdf_path,
                output_path=f"{output_path}.pypdf",  # Arquivo temporário para pypdf
                search_term=search_term,
                new_content=new_content,
                target_object_ids=target_object_ids,
                original_objects=original_text_objects
            )
            engine_manager.attempts.append(pypdf_result)
            engine_results.append(pypdf_result)

            # Se pypdf teve sucesso e preservou fontes, usar esse resultado
            if pypdf_result.success and not pypdf_result.any_font_fallback:
                # Mover arquivo do pypdf para o destino final
                try:
                    if Path(output_path).exists():
                        Path(output_path).unlink()
                    if Path(f"{output_path}.pypdf").exists():
                        shutil.move(f"{output_path}.pypdf", output_path)
                        logger.log_operation(
                            operation_type="edit-text-engine-fallback-success",
                            input_file=pdf_path,
                            output_file=output_path,
                            parameters={"engine_used": "pypdf", "font_preserved": True},
                            status="success",
                            notes="Fallback para pypdf preservou fontes com sucesso"
                        )
                except Exception as e:
                    logger.log_operation(
                        operation_type="edit-text-engine-fallback-move-error",
                        input_file=pdf_path,
                        output_file=output_path,
                        parameters={"error": str(e)},
                        status="warning",
                        notes=f"Erro ao mover arquivo do pypdf: {str(e)}"
                    )
            elif not pypdf_result.success:
                # Log de falha do pypdf
                logger.log_operation(
                    operation_type="edit-text-fallback-failed",
                    input_file=pdf_path,
                    output_file=output_path,
                    parameters={"fallback_attempted": True, "engine": "pypdf"},
                    result={"success": False, "error": pypdf_result.error},
                    status="warning",
                    notes=f"Fallback para pypdf falhou: {pypdf_result.error}"
                )
                # Limpar arquivo temporário do pypdf se existir
                try:
                    if Path(f"{output_path}.pypdf").exists():
                        Path(f"{output_path}.pypdf").unlink()
                except:
                    pass
    except Exception as e:
        # Se houver erro na detecção, continuar sem fallback
        logger.log_operation(
            operation_type="edit-text-font-detection",
            input_file=pdf_path,
            output_file=output_path,
            parameters={"error": str(e)},
            status="warning",
            notes=f"Erro ao detectar fallback de fonte: {str(e)}"
        )

    # Log da operação principal
    logger.log_operation(
        operation_type="edit-text",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "search_term": search_term,
            "new_content": new_content,
            "all_occurrences": True,
            "prefer_engine": prefer_engine,
            "align": align,
            "pad": pad,
            "font_name": font_name,
            "font_size": font_size,
            "color": color,
            "rotation": rotation
        },
        result={
            "status": "success",
            "occurrences_processed": occurrences_processed,
            "occurrences_details": occurrences_details,
            "engine_results": [r.to_dict() for r in engine_results] if engine_results else [],
            "backup": backup_path
        },
        notes=f"Processadas {occurrences_processed} ocorrências do texto '{search_term}'"
    )

    # Criar log de auditoria (Fase 5)
    if engine_results:
        audit_log = create_audit_log(
            pdf_path=pdf_path,
            output_path=output_path,
            engine_results=engine_results,
            operation_type="edit-text-all-occurrences"
        )
        # Salvar log de auditoria em arquivo separado
        audit_log_path = Path("logs") / f"audit_{audit_log['operation_id']}.json"
        audit_log_path.parent.mkdir(exist_ok=True)
        with open(audit_log_path, "w", encoding="utf-8") as f:
            json.dump(audit_log, f, ensure_ascii=False, indent=2)

    # Verificar se deve bloquear operação em modo strict
    if strict_fonts and font_manager.should_block_operation(strict_mode=True):
        # Remover arquivo de saída se bloqueado
        if os.path.exists(output_path):
            os.remove(output_path)

        # Gerar mensagem de erro com fontes faltantes
        error_msg = font_manager.get_missing_fonts_summary()
        raise PDFCliException(
            f"Operação bloqueada em modo --strict-fonts.\n{error_msg}"
        )

    # Exibir aviso sobre fontes faltantes (se houver)
    # NOTA: A confirmação será solicitada no CLI antes de chamar esta função
    if font_manager.has_missing_fonts():
        print(font_manager.get_missing_fonts_summary())

    details_dict = {
        "occurrences_processed": occurrences_processed,
        "details": occurrences_details,
        "total_occurrences": len(occurrences_details),
        "engine_used": engine_results[-1].engine.value if engine_results else "pymupdf",
        "font_fallback_detected": any(r.any_font_fallback for r in engine_results) if engine_results else False,
        "font_warnings": font_manager.get_summary_dict()
    }
    return output_path, details_dict


def edit_text(
    pdf_path: str,
    output_path: str,
    object_id: Optional[str] = None,
    content: Optional[str] = None,
    search_content: Optional[str] = None,
    new_content: str = "",
    align: Optional[str] = None,
    pad: bool = False,
    x: Optional[float] = None,
    y: Optional[float] = None,
    font_name: Optional[str] = None,
    font_size: Optional[int] = None,
    color: Optional[str] = None,
    rotation: Optional[float] = None,
    create_backup: bool = True,
    all_occurrences: bool = False,
    prefer_engine: str = "pymupdf",
    feedback_callback: Optional[Callable] = None,
    strict_fonts: bool = False
) -> Union[str, Tuple[str, Dict[str, Any]]]:
    """
    Edita um objeto de texto no PDF.

    Conforme Fase 3: edit-text
    Permite alteração via ID único ou busca por conteúdo.

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        output_path: Caminho de saída do PDF modificado.
        object_id: ID único do objeto a editar.
        content: Conteúdo do objeto a buscar (se object_id não fornecido).
        search_content: Alias para content.
        new_content: Novo conteúdo do texto.
        align: Alinhamento (left, center, right, justify).
        pad: Se True, aplica padding para manter largura visual.
        x: Nova posição X.
        y: Nova posição Y.
        font_name: Nova fonte.
        font_size: Novo tamanho da fonte.
        color: Nova cor (formato hex).
        rotation: Nova rotação em graus.
        create_backup: Se True, cria backup antes de modificar.
        all_occurrences: Se True, substitui todas as ocorrências encontradas (apenas com content/search_content).

    Returns:
        str: Caminho do PDF modificado.

    Raises:
        TextNotFoundError: Se o texto não for encontrado.
        PaddingError: Se o padding não puder ser aplicado.
    """
    logger = get_logger()
    search_term = content or search_content

    # Criar backup se solicitado
    backup_path = None
    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # Se all_occurrences está ativo e search_term foi fornecido, processar todas as ocorrências
    if all_occurrences and search_term and not object_id:
        result_path, occurrences_details_dict = _edit_text_all_occurrences(
            pdf_path=pdf_path,
            output_path=output_path,
            search_term=search_term,
            new_content=new_content,
            align=align,
            pad=pad,
            font_name=font_name,
            font_size=font_size,
            color=color,
            rotation=rotation,
            create_backup=False,  # Já criamos o backup acima
            prefer_engine=prefer_engine,
            feedback_callback=feedback_callback,
            strict_fonts=strict_fonts
        )
        # Retornar tuple com caminho e detalhes
        details = {
            "occurrences_processed": occurrences_details_dict.get("occurrences_processed", len(occurrences_details_dict.get("details", []))),
            "details": occurrences_details_dict.get("details", occurrences_details_dict if isinstance(occurrences_details_dict, list) else []),
            "total_occurrences": len(occurrences_details_dict.get("details", occurrences_details_dict if isinstance(occurrences_details_dict, list) else []))
        }
        return result_path, details

    with PDFRepository(pdf_path) as repo:
        # Extrair textos
        text_objects = repo.extract_text_objects()

        # Encontrar objeto a editar
        target_obj = None
        if object_id:
            for obj in text_objects:
                if obj.id == object_id:
                    target_obj = obj
                    break
        elif search_term:
            for obj in text_objects:
                # Busca por substring - se encontrar, usar o texto completo como base
                if search_term in obj.content:
                    target_obj = obj
                    break

        if target_obj is None:
            raise TextNotFoundError(
                search=object_id or search_term or "",
                suggestion="Use export-objects para listar todos os textos disponíveis."
            )

        # Preparar alterações - salvar estado original antes de modificar
        before_state = target_obj.to_dict()
        original_content = target_obj.content

        # Lógica de substituição de conteúdo
        if new_content:
            # IMPORTANTE: Se o search_term é uma substring do texto original,
            # substituir APENAS a parte correspondente, preservando o resto do texto
            if search_term and search_term.strip() and search_term in original_content and search_term != original_content:
                # Substituição parcial: preservar o texto original, substituindo apenas a substring encontrada
                target_obj.content = original_content.replace(search_term, new_content, 1)
                # Usar o conteúdo parcial substituído para as próximas operações (pad, etc.)
                final_content_for_ops = target_obj.content
            else:
                # Substituição completa: substituir todo o conteúdo
                # Isso acontece quando:
                # - search_term é None (busca por ID)
                # - search_term == original_content (texto completo idêntico)
                # - search_term não está no original_content
                if pad:
                    # Aplicar padding
                    target_obj.content = center_and_pad_text(target_obj, new_content)
                else:
                    target_obj.content = new_content
                final_content_for_ops = target_obj.content

            # Atualizar final_content para usar na inserção no PDF
            final_content = target_obj.content

        if align:
            target_obj.align = align
        if x is not None:
            target_obj.x = x
        if y is not None:
            target_obj.y = y
        if font_name:
            target_obj.font_name = font_name
        if font_size is not None:
            target_obj.font_size = font_size
        if color:
            target_obj.color = color
        if rotation is not None:
            target_obj.rotation = rotation

        # Implementar escrita real no PDF usando PyMuPDF
        doc = repo.open()
        page = doc[target_obj.page]

        # Preparar novo conteúdo (new_content é obrigatório, senão não há nada para editar)
        if not new_content:
            raise ValueError("Parâmetro 'new_content' é obrigatório para edição de texto")

        # final_content já foi definido acima (linha 243) com a substituição parcial ou completa
        # Se não foi definido (não entrou no if new_content), usar new_content diretamente
        if 'final_content' not in locals():
            final_content = new_content

        # Determinar posição (usar coordenadas do objeto ou novas coordenadas)
        final_x = target_obj.x if x is None else x
        final_y = target_obj.y if y is None else y

        # Converter cor hex para RGB (formato PyMuPDF)
        color_rgb = (0, 0, 0)  # Preto padrão
        if color:
            hex_color = color.lstrip("#")
            if len(hex_color) == 6:
                color_rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

        # Determinar fonte e tamanho
        final_font = target_obj.font_name if not font_name else font_name
        final_font_size = target_obj.font_size if font_size is None else font_size

        # Buscar e remover texto antigo usando redaction
        bbox = fitz.Rect(target_obj.x, target_obj.y, target_obj.x + target_obj.width, target_obj.y + target_obj.height)
        page.add_redact_annot(bbox, fill=(1, 1, 1))  # Preencher com branco
        page.apply_redactions()

        # Inserir novo texto
        # Determinar alinhamento
        align_val = 0  # left
        if align:
            if align == "center":
                align_val = 1
            elif align == "right":
                align_val = 2
            elif align == "justify":
                align_val = 3

        # Inserir texto com formatação
        text_rect = fitz.Rect(final_x, final_y, final_x + target_obj.width, final_y + target_obj.height)

        # Tentar carregar fonte original, com fallback para fontes padrão similares
        # PyMuPDF não consegue carregar todas as fontes do sistema, então tentamos fontes padrão similares
        font_loaded = None

        # Mapear fontes comuns para fontes padrão do PyMuPDF
        font_mapping = {
            "ArialMT": "helv",
            "Arial": "helv",
            "ArialNarrow": "helv",
            "ArialNarrow-Bold": "hebo",  # Helvetica-Bold
            "Times": "tiro",
            "Times-Roman": "tiro",
            "Courier": "cour",
        }

        # Tentar usar mapeamento primeiro
        mapped_font = font_mapping.get(final_font) if final_font else None
        if mapped_font:
            try:
                font_loaded = fitz.Font(mapped_font)
            except:
                pass

        # Se não funcionou, tentar fonte original
        if font_loaded is None and final_font:
            try:
                font_loaded = fitz.Font(final_font)
            except:
                pass

        # Fallback final para helv (Helvetica)
        if font_loaded is None:
            font_loaded = fitz.Font("helv")

        # Para fontes em negrito, tentar usar versão bold se disponível
        fontname_to_use = font_loaded.name
        if final_font and "bold" in final_font.lower() and "hebo" not in fontname_to_use.lower():
            try:
                bold_font = fitz.Font("hebo")  # Helvetica-Bold
                fontname_to_use = bold_font.name
            except:
                pass  # Usar fonte normal se bold não disponível

        page.insert_text(
            point=(final_x, final_y + final_font_size),  # Ajustar Y para baseline
            text=final_content,
            fontsize=final_font_size,
            fontname=fontname_to_use,
            color=color_rgb,
            rotate=target_obj.rotation if rotation is None else rotation
        )

        # Salvar PDF modificado
        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        # Não fechar manualmente - o context manager fará isso

        after_state = target_obj.to_dict()

        # Log da operação
        logger.log_operation(
            operation_type="edit-text",
            input_file=pdf_path,
            output_file=output_path,
            parameters={
                "object_id": object_id,
                "search_content": search_term,
                "new_content": new_content,
                "align": align,
                "pad": pad
            },
            result={
                "before": before_state,
                "after": after_state,
                "backup": backup_path
            },
            notes="Modificação de texto realizada."
        )

    return output_path


def edit_table(
    pdf_path: str,
    output_path: str,
    table_id: str,
    row: Optional[int] = None,
    col: Optional[int] = None,
    value: Optional[str] = None,
    header: Optional[str] = None,
    create_backup: bool = True
) -> str:
    """
    Edita uma célula de tabela no PDF.

    Conforme Fase 3: edit-table

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        output_path: Caminho de saída do PDF modificado.
        table_id: ID único da tabela.
        row: Índice da linha (0-indexed).
        col: Índice da coluna (0-indexed).
        value: Novo valor da célula.
        header: Novo cabeçalho (se row for None, edita header).
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.
    """
    logger = get_logger()

    backup_path = None
    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # Edição de tabelas requer detecção de estrutura de tabelas no PDF,
    # que é uma operação complexa dependendo da estrutura do PDF.
    # Por enquanto, esta funcionalidade precisa de algoritmo de detecção de tabelas.
    # NOTA: Esta é uma limitação técnica conhecida que requer desenvolvimento futuro.

    # Log da tentativa
    logger.log_operation(
        operation_type="edit-table",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "table_id": table_id,
            "row": row,
            "col": col,
            "value": value,
            "header": header
        },
        result={"status": "not_implemented", "backup": backup_path},
        status="error",
        error="Edição de tabelas requer implementação de detecção de estrutura de tabelas. Esta funcionalidade será implementada em fase futura."
    )

    raise NotImplementedError(
        "Edição de tabelas requer implementação de detecção de estrutura de tabelas. "
        "Esta funcionalidade será implementada em fase futura após desenvolvimento do algoritmo de detecção."
    )


def replace_image(
    pdf_path: str,
    output_path: str,
    image_id: str,
    src: str,
    filter_type: Optional[str] = None,
    create_backup: bool = True
) -> str:
    """
    Substitui uma imagem no PDF.

    Conforme Fase 3: replace-image

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        output_path: Caminho de saída do PDF modificado.
        image_id: ID único da imagem.
        src: Caminho da nova imagem.
        filter_type: Tipo de filtro a aplicar (grayscale, blur, invert).
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.
    """
    logger = get_logger()

    if not Path(src).exists():
        raise PDFFileNotFoundError(src)

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # Implementar substituição real de imagem
    with PDFRepository(pdf_path) as repo:
        # Extrair imagens para encontrar a que será substituída
        image_objects = repo.extract_image_objects()

        # Encontrar imagem pelo ID
        target_image = None
        for img_obj in image_objects:
            if img_obj.id == image_id:
                target_image = img_obj
                break

        if target_image is None:
            raise PDFFileNotFoundError(f"Imagem com ID {image_id} não encontrada no PDF")

        doc = repo.open()
        page = doc[target_image.page]

        # Buscar a imagem no PDF para remover
        image_list = page.get_images()
        xref_to_remove = None

        for img_index, img in enumerate(image_list):
            xref = img[0]
            image_rects = page.get_image_rects(xref)
            for rect in image_rects:
                if abs(rect.x0 - target_image.x) < 1 and abs(rect.y0 - target_image.y) < 1:
                    xref_to_remove = xref
                    break
            if xref_to_remove:
                break

        # Remover imagem antiga usando redaction
        if xref_to_remove:
            bbox = fitz.Rect(target_image.x, target_image.y,
                           target_image.x + target_image.width,
                           target_image.y + target_image.height)
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

        # Inserir nova imagem
        rect = fitz.Rect(target_image.x, target_image.y,
                        target_image.x + target_image.width,
                        target_image.y + target_image.height)

        # Aplicar filtro se especificado
        img_data = Path(src).read_bytes()
        if filter_type == "grayscale":
            # Converter para grayscale usando PIL
            try:
                from PIL import Image as PILImage
                import io
                img = PILImage.open(io.BytesIO(img_data))
                if img.mode != "L":
                    img = img.convert("L")
                img_io = io.BytesIO()
                img.save(img_io, format=img.format if hasattr(img, 'format') else 'PNG')
                img_data = img_io.getvalue()
            except ImportError:
                pass  # Se PIL não disponível, insere sem filtro
        elif filter_type == "invert":
            try:
                from PIL import Image as PILImage
                import io
                img = PILImage.open(io.BytesIO(img_data))
                if img.mode == "RGB":
                    img = img.point(lambda x: 255 - x)
                elif img.mode == "L":
                    img = img.point(lambda x: 255 - x)
                img_io = io.BytesIO()
                img.save(img_io, format=img.format if hasattr(img, 'format') else 'PNG')
                img_data = img_io.getvalue()
            except ImportError:
                pass

        # Inserir imagem
        page.insert_image(rect, stream=img_data)

        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

    logger.log_operation(
        operation_type="replace-image",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "image_id": image_id,
            "src": src,
            "filter_type": filter_type
        },
        result={"status": "success", "backup": backup_path}
    )

    return output_path


# ============================================================================
# INSERÇÃO DE OBJETOS
# ============================================================================

def insert_object(
    pdf_path: str,
    output_path: str,
    obj_type: str,
    params: Union[Dict[str, Any], str],
    create_backup: bool = True
) -> str:
    """
    Insere um novo objeto no PDF.

    Conforme Fase 3: insert-object

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        output_path: Caminho de saída do PDF modificado.
        obj_type: Tipo do objeto (text, image, table, etc.).
        params: Parâmetros do objeto (dict ou JSON string).
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.
    """
    logger = get_logger()

    # Parse params se for string
    if isinstance(params, str):
        params = json.loads(params)

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # Validar campos obrigatórios conforme tipo e inserir objeto real
    with PDFRepository(pdf_path) as repo:
        doc = repo.open()

        if obj_type == "text":
            # Validar campos obrigatórios
            required_fields = ["page", "content", "x", "y"]
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"Campo obrigatório '{field}' não fornecido para objeto tipo 'text'")

            page_num = params["page"]
            if page_num < 0 or page_num >= len(doc):
                raise InvalidPageError(page_num, len(doc))

            page = doc[page_num]
            content = params.get("content", "")
            x = params.get("x", 0.0)
            y = params.get("y", 0.0)
            font_size = params.get("font_size", 12)
            font_name = params.get("font_name", "helv")
            color = params.get("color", "#000000")
            rotation = params.get("rotation", 0.0)

            # Converter cor hex para RGB
            color_rgb = (0, 0, 0)
            hex_color = color.lstrip("#")
            if len(hex_color) == 6:
                color_rgb = tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))

            # Carregar fonte
            try:
                font = fitz.Font(font_name)
            except:
                font = fitz.Font("helv")

            # Inserir texto
            page.insert_text(
                point=(x, y + font_size),
                text=content,
                fontsize=font_size,
                fontname=font.name,
                color=color_rgb,
                rotate=rotation
            )

        elif obj_type == "image":
            # Validar campos obrigatórios
            required_fields = ["page", "src", "x", "y"]
            for field in required_fields:
                if field not in params:
                    raise ValueError(f"Campo obrigatório '{field}' não fornecido para objeto tipo 'image'")

            page_num = params["page"]
            if page_num < 0 or page_num >= len(doc):
                raise InvalidPageError(page_num, len(doc))

            img_src = params["src"]
            if not Path(img_src).exists():
                raise PDFFileNotFoundError(img_src)

            page = doc[page_num]
            x = params.get("x", 0.0)
            y = params.get("y", 0.0)
            width = params.get("width", 100.0)
            height = params.get("height", 100.0)

            rect = fitz.Rect(x, y, x + width, y + height)
            img_data = Path(img_src).read_bytes()
            page.insert_image(rect, stream=img_data)

        else:
            # Outros tipos (table, link, etc.) requerem implementação mais complexa
            # Por enquanto, validação básica
            if "page" not in params:
                raise ValueError(f"Campo obrigatório 'page' não fornecido para objeto tipo '{obj_type}'")

            # Outros tipos (table, link, graphic, etc.) requerem implementação específica
            # para cada tipo. Por enquanto, apenas text e image estão totalmente implementados.
            doc.close()
            raise NotImplementedError(
                f"Inserção de objetos do tipo '{obj_type}' ainda não está implementada. "
                f"Tipos suportados: text, image"
            )

        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

    logger.log_operation(
        operation_type="insert-object",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "object_type": obj_type,
            "params": params
        },
        result={"status": "success", "backup": backup_path}
    )

    return output_path


# ============================================================================
# RESTAURAÇÃO VIA JSON
# ============================================================================

def restore_from_json(
    source_pdf: str,
    json_file: str,
    output_path: str,
    create_backup: bool = True
) -> str:
    """
    Restaura/reaplica alterações de um JSON ao PDF.

    Conforme Fase 3: restore-from-json

    Args:
        source_pdf: Caminho do PDF original.
        json_file: Caminho do arquivo JSON com alterações.
        output_path: Caminho de saída do PDF modificado.
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.
    """
    logger = get_logger()

    # Validar JSON
    with open(json_file, "r", encoding="utf-8") as f:
        changes = json.load(f)

    if create_backup:
        with PDFRepository(source_pdf) as repo:
            backup_path = repo.create_backup()

    # Implementar aplicação de alterações do JSON
    with PDFRepository(source_pdf) as repo:
        doc = repo.open()

        # Validar estrutura do JSON
        if not isinstance(changes, dict):
            raise ValueError("JSON deve ser um dicionário agrupado por página")

        # Processar cada página
        for page_num_str, page_objects in changes.items():
            try:
                page_num = int(page_num_str)
            except ValueError:
                continue

            if page_num < 0 or page_num >= len(doc):
                continue

            page = doc[page_num]

            # Processar objetos por tipo
            for obj_type, objects in page_objects.items():
                if not isinstance(objects, list):
                    continue

                for obj_data in objects:
                    if obj_type == "text":
                        # Aplicar edição de texto
                        obj_id = obj_data.get("id")
                        new_content = obj_data.get("content")
                        if obj_id and new_content:
                            # Buscar e editar texto
                            text_objects = repo.extract_text_objects()
                            for text_obj in text_objects:
                                if text_obj.id == obj_id and text_obj.page == page_num:
                                    # Editar texto
                                    bbox = fitz.Rect(text_obj.x, text_obj.y,
                                                   text_obj.x + text_obj.width,
                                                   text_obj.y + text_obj.height)
                                    page.add_redact_annot(bbox, fill=(1, 1, 1))
                                    page.apply_redactions()

                                    color_rgb = (0, 0, 0)
                                    color_hex = obj_data.get("color", "#000000").lstrip("#")
                                    if len(color_hex) == 6:
                                        color_rgb = tuple(int(color_hex[i:i+2], 16) / 255.0 for i in (0, 2, 4))

                                    font_size = obj_data.get("font_size", text_obj.font_size)
                                    try:
                                        font = fitz.Font(obj_data.get("font_name", text_obj.font_name) or "helv")
                                    except:
                                        font = fitz.Font("helv")

                                    page.insert_text(
                                        point=(text_obj.x, text_obj.y + font_size),
                                        text=new_content,
                                        fontsize=font_size,
                                        fontname=font.name,
                                        color=color_rgb
                                    )
                                    break

                    elif obj_type == "image":
                        # Restore de imagens via JSON pode ser feito usando replace_image()
                        # se necessário. Por enquanto, restore-from-json foca em textos.
                        pass

        doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        doc.close()

    logger.log_operation(
        operation_type="restore-from-json",
        input_file=source_pdf,
        output_file=output_path,
        parameters={"json_file": json_file},
        result={
            "changes_count": len(changes) if isinstance(changes, list) else 1,
            "status": "success",
            "backup": backup_path
        }
    )

    return output_path


# ============================================================================
# EDIÇÃO DE METADADOS
# ============================================================================

def edit_metadata(
    pdf_path: str,
    output_path: str,
    title: Optional[str] = None,
    author: Optional[str] = None,
    subject: Optional[str] = None,
    keywords: Optional[str] = None,
    creator: Optional[str] = None,
    producer: Optional[str] = None,
    create_backup: bool = True
) -> str:
    """
    Edita metadados do PDF.

    Conforme Fase 3: edit-metadata

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        output_path: Caminho de saída do PDF modificado.
        title: Novo título.
        author: Novo autor.
        subject: Novo assunto.
        keywords: Nova palavras-chave (separadas por vírgula).
        creator: Novo criador.
        producer: Novo produtor.
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.
    """
    logger = get_logger()

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    with PDFRepository(pdf_path) as repo:
        # Obter metadados atuais
        current_metadata = repo.get_metadata()
        before_metadata = current_metadata.copy()

        # Aplicar alterações
        new_metadata = {}
        if title:
            new_metadata["title"] = title
        if author:
            new_metadata["author"] = author
        if subject:
            new_metadata["subject"] = subject
        if keywords:
            new_metadata["keywords"] = keywords
        if creator:
            new_metadata["creator"] = creator
        if producer:
            new_metadata["producer"] = producer

        # Atualizar metadados
        repo.set_metadata(new_metadata)
        repo.save(output_path)

    logger.log_operation(
        operation_type="edit-metadata",
        input_file=pdf_path,
        output_file=output_path,
        parameters=new_metadata,
        result={
            "before": before_metadata,
            "after": new_metadata
        }
    )

    return output_path


# ============================================================================
# MANIPULAÇÃO ESTRUTURAL
# ============================================================================

def merge_pdf(pdf_paths: List[str], output_path: str) -> str:
    """
    Une múltiplos arquivos PDF em um único documento.

    Conforme Fase 3: merge

    Args:
        pdf_paths: Lista de caminhos para os PDFs a serem unidos.
        output_path: Caminho de saída para o PDF resultante.

    Returns:
        str: Caminho do PDF resultante.

    Raises:
        PDFFileNotFoundError: Se algum PDF não for encontrado.
    """
    logger = get_logger()

    if not pdf_paths:
        raise ValueError("Lista de PDFs vazia")

    # Usar o primeiro PDF como base e incluir todos na união
    base_repo = PDFRepository(pdf_paths[0])
    merged_doc = base_repo.merge_pdfs(pdf_paths)

    merged_doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
    merged_doc.close()
    base_repo.close()

    logger.log_operation(
        operation_type="merge",
        input_file=",".join(pdf_paths),
        output_file=output_path,
        parameters={"pdf_count": len(pdf_paths)},
        result={"status": "success"}
    )

    return output_path


def delete_pages(
    pdf_path: str,
    page_numbers: List[int],
    output_path: Optional[str] = None,
    create_backup: bool = True
) -> str:
    """
    Exclui páginas específicas de um PDF.

    Conforme Fase 3: delete-pages

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        page_numbers: Lista de números de páginas a excluir (1-indexed para compatibilidade CLI).
        output_path: Caminho de saída. Se None, sobrescreve original (requer --force).
        create_backup: Se True, cria backup.

    Returns:
        str: Caminho do PDF modificado.

    Raises:
        InvalidPageError: Se algum número de página for inválido.
    """
    logger = get_logger()

    # Converter de 1-indexed para 0-indexed (CLI usa 1-indexed)
    page_numbers_0indexed = [p - 1 for p in page_numbers if p > 0]

    if output_path is None:
        output_path = str(pdf_path)

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    with PDFRepository(pdf_path) as repo:
        modified_doc = repo.delete_pages(page_numbers_0indexed)
        modified_doc.save(output_path, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
        modified_doc.close()

    logger.log_operation(
        operation_type="delete-pages",
        input_file=pdf_path,
        output_file=output_path,
        parameters={"pages": page_numbers},
        result={"pages_deleted": len(page_numbers)}
    )

    return output_path


def split_pdf(
    pdf_path: str,
    ranges: List[tuple],
    output_prefix: str,
    create_backup: bool = True
) -> List[str]:
    """
    Divide o PDF em múltiplos arquivos conforme faixas de páginas.

    Conforme Fase 3: split

    Args:
        pdf_path: Caminho para o arquivo PDF de entrada.
        ranges: Lista de tuplas (start, end) indicando faixas (1-indexed).
        output_prefix: Prefixo para os arquivos de saída.
        create_backup: Se True, cria backup.

    Returns:
        List[str]: Lista de caminhos dos PDFs criados.

    Raises:
        InvalidPageError: Se alguma faixa for inválida.
    """
    logger = get_logger()

    # Converter de 1-indexed para 0-indexed
    ranges_0indexed = [(start - 1, end - 1) for start, end in ranges]

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    output_files = []
    with PDFRepository(pdf_path) as repo:
        split_docs = repo.split_pages(ranges_0indexed)

        for i, doc in enumerate(split_docs):
            output_file = f"{output_prefix}{i+1}.pdf"
            doc.save(output_file, incremental=False, encryption=fitz.PDF_ENCRYPT_KEEP)
            doc.close()
            output_files.append(output_file)

    logger.log_operation(
        operation_type="split",
        input_file=pdf_path,
        output_file=",".join(output_files),
        parameters={"ranges": ranges, "prefix": output_prefix},
        result={"files_created": len(output_files)}
    )

    return output_files


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def center_and_pad_text(text_object: TextObject, new_text: str) -> str:
    """
    Ajusta um novo texto para centralizá-lo mantendo o espaço visual original.

    Calcula os espaços necessários antes e depois do texto para mantê-lo
    visualmente centralizado dentro da área original do objeto de texto.

    Args:
        text_object: Objeto de texto original.
        new_text: Novo texto a ser centralizado.

    Returns:
        str: Texto ajustado com espaços para centralização.

    Raises:
        PaddingError: Se o novo texto for maior que o espaço disponível.
    """
    # Calcular largura estimada do novo texto
    # Estimativa simples: assumir mesmo tamanho de fonte
    char_width_estimate = text_object.width / len(text_object.content) if text_object.content else 1
    new_width_estimate = len(new_text) * char_width_estimate

    if new_width_estimate > text_object.width * 1.2:  # 20% de tolerância
        raise PaddingError(
            edit_id=text_object.id,
            original_content=text_object.content,
            new_content=new_text,
            width_original=text_object.width,
            width_new=new_width_estimate,
            suggestion="Reduza o texto ou aumente tamanho do bloco/font."
        )

    # Calcular espaços para centralização
    total_chars = int(text_object.width / char_width_estimate)
    spaces_needed = total_chars - len(new_text)
    spaces_before = spaces_needed // 2
    spaces_after = spaces_needed - spaces_before

    return " " * spaces_before + new_text + " " * spaces_after


def parse_page_numbers(page_string: str) -> List[int]:
    """
    Parse uma string de números de página (ex: "1,3,5" ou "1-5").

    Args:
        page_string: String com números de página.

    Returns:
        List[int]: Lista de números de página (1-indexed).
    """
    pages = []
    for part in page_string.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return sorted(set(pages))


def parse_page_ranges(ranges_string: str) -> List[tuple]:
    """
    Parse uma string de faixas de páginas (ex: "1-3,4-6").

    Args:
        ranges_string: String com faixas de páginas.

    Returns:
        List[tuple]: Lista de tuplas (start, end) (1-indexed).
    """
    ranges = []
    for part in ranges_string.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            ranges.append((start, end))
        else:
            # Página única
            page = int(part)
            ranges.append((page, page))
    return ranges
