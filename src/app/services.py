"""
Casos de uso e funções core do PDF-cli - Fase 3.

Este módulo contém a lógica de negócio (casos de uso) para todas as
operações principais do PDF-cli conforme especificações da Fase 3.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Union, Tuple, Callable
import json
import shutil
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
    InvalidPageError, PaddingError
)
import fitz  # PyMuPDF
from app.pdf_repo import PDFRepository
from app.logging import get_logger


# ============================================================================
# EXTRAÇÃO DE OBJETOS
# ============================================================================

def export_objects(
    pdf_path: str,
    output_path: str,
    types: Optional[List[str]] = None
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

        # Salvar JSON
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(grouped, f, indent=2, ensure_ascii=False)

        # Estatísticas
        stats = {
            "total_objects": sum(len(objs) for objs in all_objects.values()),
            "by_type": {t: len(objs) for t, objs in all_objects.items()},
            "by_page": {str(p): sum(len(objs) for objs in types.values()) for p, types in grouped.items()}
        }

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
    feedback_callback: Optional[Callable[[Dict[str, Any]], None]] = None
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Função auxiliar para editar todas as ocorrências de um texto.

    Processa todas as ocorrências do search_term no PDF e substitui por new_content,
    preservando o texto completo quando search_term é uma substring.

    Args:
        feedback_callback: Função opcional chamada após cada ocorrência processada.
                          Recebe um dict com: id, page, coordinates, original_content,
                          new_content, font_original, font_used, font_fallback, changes

    Returns:
        tuple[str, List[Dict]]: (caminho_do_arquivo, lista_de_detalhes_das_ocorrências)
    """
    logger = get_logger()

    # Criar backup se solicitado
    backup_path = None
    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

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

        # Preparar fonte e cor uma única vez (reutilizar para todas as ocorrências)
        font_mapping = {
            "ArialMT": "helv",
            "Arial": "helv",
            "ArialNarrow": "helv",
            "ArialNarrow-Bold": "hebo",
            "Times": "tiro",
            "Times-Roman": "tiro",
            "Courier": "cour",
        }

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
            final_font_size = target_obj.font_size if font_size is None else font_size
            final_rotation = target_obj.rotation if rotation is None else rotation

            # Mapear e carregar fonte
            font_loaded = None
            mapped_font = font_mapping.get(final_font) if final_font else None
            if mapped_font:
                try:
                    font_loaded = fitz.Font(mapped_font)
                except:
                    pass

            if font_loaded is None and final_font:
                try:
                    font_loaded = fitz.Font(final_font)
                except:
                    pass

            if font_loaded is None:
                font_loaded = fitz.Font("helv")

            fontname_to_use = font_loaded.name
            font_fallback_occurred = False

            # Detectar se houve fallback de fonte
            if mapped_font:
                # Fonte foi mapeada (fallback)
                font_fallback_occurred = True
                font_used_source = f"mapeada ({final_font} → {mapped_font})"
            elif font_loaded.name == "Helvetica" and final_font and final_font != "helv":
                # Fonte original não encontrada, caiu para Helvetica padrão
                font_fallback_occurred = True
                font_used_source = f"fallback padrão (Helvetica)"
            else:
                # Fonte original foi usada
                font_used_source = f"original ({final_font})"

            if final_font and "bold" in final_font.lower() and "hebo" not in fontname_to_use.lower():
                try:
                    bold_font = fitz.Font("hebo")
                    fontname_to_use = bold_font.name
                    if not font_fallback_occurred:
                        font_fallback_occurred = True
                        font_used_source += " → bold aplicado"
                except:
                    pass

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
                "font_used": fontname_to_use,
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

            # Remover texto antigo usando redaction
            bbox = fitz.Rect(target_obj.x, target_obj.y, target_obj.x + target_obj.width, target_obj.y + target_obj.height)
            page.add_redact_annot(bbox, fill=(1, 1, 1))
            page.apply_redactions()

            # Inserir novo texto com formatação preservada
            page.insert_text(
                point=(target_obj.x, target_obj.y + final_font_size),
                text=final_content,
                fontsize=final_font_size,
                fontname=fontname_to_use,
                color=color_rgb,
                rotate=final_rotation
            )

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

    # Log da operação
    logger.log_operation(
        operation_type="edit-text",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "search_term": search_term,
            "new_content": new_content,
            "all_occurrences": True,
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
            "backup": backup_path
        },
        notes=f"Processadas {occurrences_processed} ocorrências do texto '{search_term}'"
    )

    return output_path, occurrences_details


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
    all_occurrences: bool = False
) -> str:
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
        result_path, occurrences_details = _edit_text_all_occurrences(
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
            create_backup=False  # Já criamos o backup acima
        )
        # Armazenar detalhes em atributo da função para acesso externo
        edit_text._last_occurrences_details = occurrences_details
        return result_path

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
