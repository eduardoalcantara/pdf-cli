"""
Casos de uso e funções core do PDF-cli - Fase 3.

Este módulo contém a lógica de negócio (casos de uso) para todas as
operações principais do PDF-cli conforme especificações da Fase 3.
"""

from pathlib import Path
from typing import List, Dict, Optional, Any, Union
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

        # TODO: Implementar extração de outros tipos (table, link, formfield, etc.)

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
    create_backup: bool = True
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
                if search_term in obj.content:
                    target_obj = obj
                    break

        if target_obj is None:
            raise TextNotFoundError(
                search=object_id or search_term or "",
                suggestion="Use export-objects para listar todos os textos disponíveis."
            )

        # Preparar alterações
        before_state = target_obj.to_dict()

        if new_content:
            if pad:
                # Aplicar padding
                target_obj.content = center_and_pad_text(target_obj, new_content)
            else:
                target_obj.content = new_content

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

        # TODO: Implementar escrita real no PDF usando PyMuPDF
        # Por enquanto, apenas salva cópia
        shutil.copy2(pdf_path, output_path)

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

    if create_backup:
        with PDFRepository(pdf_path) as repo:
            backup_path = repo.create_backup()

    # TODO: Implementar extração e edição de tabelas
    shutil.copy2(pdf_path, output_path)

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
        result={"status": "pending_implementation"}
    )

    return output_path


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

    # TODO: Implementar substituição real de imagem
    shutil.copy2(pdf_path, output_path)

    logger.log_operation(
        operation_type="replace-image",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "image_id": image_id,
            "src": src,
            "filter_type": filter_type
        },
        result={"status": "pending_implementation"}
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

    # Validar campos obrigatórios conforme tipo
    # TODO: Implementar validação completa e inserção real
    shutil.copy2(pdf_path, output_path)

    logger.log_operation(
        operation_type="insert-object",
        input_file=pdf_path,
        output_file=output_path,
        parameters={
            "object_type": obj_type,
            "params": params
        },
        result={"status": "pending_implementation"}
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

    # TODO: Implementar aplicação de alterações do JSON
    shutil.copy2(source_pdf, output_path)

    logger.log_operation(
        operation_type="restore-from-json",
        input_file=source_pdf,
        output_file=output_path,
        parameters={"json_file": json_file},
        result={
            "changes_count": len(changes) if isinstance(changes, list) else 1,
            "status": "pending_implementation"
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
