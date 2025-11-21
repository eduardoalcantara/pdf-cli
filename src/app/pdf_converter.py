"""
Módulo PDF Converter - Conversão de PDF para Markdown e HTML.

Este módulo implementa a conversão de arquivos PDF (.pdf) para Markdown (.md)
e HTML (.html), usando bibliotecas multiplataforma que funcionam em Windows e Linux.

Utiliza as funcionalidades existentes do projeto:
- PDFRepository para extrair texto, imagens e posicionamento
- Preserva fontes, tamanhos e posicionamento relativo
- Extrai imagens e converte para base64 no HTML
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import base64
from app.pdf_repo import PDFRepository
from app.logging import get_logger


def _extract_pdf_data(pdf_path: str) -> Dict[str, Any]:
    """
    Extrai dados estruturados do PDF usando o repositório existente.

    Args:
        pdf_path: Caminho do arquivo PDF

    Returns:
        Dicionário com:
            - pages: Lista de dados por página
            - page_dimensions: Dimensões de cada página
    """
    repo = PDFRepository(pdf_path)
    try:
        # Abrir documento para obter dimensões das páginas
        doc = repo.open()
        page_dimensions = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            rect = page.rect
            page_dimensions.append({
                'width': rect.width,
                'height': rect.height
            })

        # Extrair objetos de texto com posicionamento
        text_objects = repo.extract_text_objects()

        # Extrair imagens
        image_objects = repo.extract_image_objects()

        # Agrupar por página
        pages_data = {}
        for text_obj in text_objects:
            page = text_obj.page
            if page not in pages_data:
                pages_data[page] = {
                    'text_objects': [],
                    'image_objects': []
                }
            pages_data[page]['text_objects'].append(text_obj)

        for img_obj in image_objects:
            page = img_obj.page
            if page not in pages_data:
                pages_data[page] = {
                    'text_objects': [],
                    'image_objects': []
                }
            pages_data[page]['image_objects'].append(img_obj)

        # Converter para lista ordenada
        pages_list = []
        for page_num in sorted(pages_data.keys()):
            pages_list.append({
                'page_num': page_num,
                'text_objects': pages_data[page_num]['text_objects'],
                'image_objects': pages_data[page_num]['image_objects'],
                'width': page_dimensions[page_num]['width'],
                'height': page_dimensions[page_num]['height']
            })

        return {
            'pages': pages_list,
            'page_dimensions': page_dimensions
        }
    finally:
        # Fechar documento se estiver aberto
        if hasattr(repo, '_doc') and repo._doc:
            repo._doc.close()


def _convert_to_html(pages_data: Dict[str, Any], pdf_path: str) -> str:
    """
    Converte dados extraídos do PDF para HTML com posicionamento preservado.

    Args:
        pages_data: Dados extraídos do PDF
        pdf_path: Caminho do PDF original

    Returns:
        String HTML completa
    """
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="pt-BR">',
        '<head>',
        '<meta charset="UTF-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
        '<style>',
        'body { margin: 0; padding: 0; background: #fff; font-family: Arial, sans-serif; }',
        '.page-container { position: relative; margin: 0 auto; background: white; }',
        '.text-element { position: absolute; white-space: nowrap; overflow: visible; }',
        '.image-element { position: absolute; }',
        '</style>',
        '</head>',
        '<body>'
    ]

    for page_info in pages_data['pages']:
        page_num = page_info['page_num']
        width = page_info['width']
        height = page_info['height']
        text_objects = page_info['text_objects']
        image_objects = page_info['image_objects']

        # Container da página com dimensões preservadas
        # Escalar para visualização (ex: 1.5x para melhor legibilidade)
        scale = 1.5
        scaled_width = width * scale
        scaled_height = height * scale

        html_parts.append(f'<div class="page-container" style="width: {scaled_width}px; height: {scaled_height}px; margin-bottom: 20px;">')

        # Adicionar imagens primeiro (camada de fundo)
        for img_obj in image_objects:
            # Converter base64 para data URI
            img_data_uri = f"data:{img_obj.mime_type};base64,{img_obj.data_base64}"

            # Posicionamento absoluto escalado
            x = img_obj.x * scale
            y = img_obj.y * scale
            img_width = img_obj.width * scale
            img_height = img_obj.height * scale

            html_parts.append(
                f'<img class="image-element" src="{img_data_uri}" '
                f'style="left: {x}px; top: {y}px; width: {img_width}px; height: {img_height}px;" />'
            )

        # Adicionar textos com posicionamento e formatação preservados
        for text_obj in text_objects:
            if not text_obj.content or not text_obj.content.strip():
                continue

            # Escalar posicionamento
            x = text_obj.x * scale
            y = text_obj.y * scale
            width_scaled = text_obj.width * scale
            height_scaled = text_obj.height * scale

            # Preservar tamanho da fonte (escalado)
            font_size = text_obj.font_size * scale if text_obj.font_size > 0 else 12 * scale

            # Preservar cor
            color = text_obj.color if text_obj.color else '#000000'

            # Escapar HTML
            content = text_obj.content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            # Estilo inline com posicionamento e formatação
            # Não limitar width para evitar quebra de texto
            style = (
                f'left: {x}px; top: {y}px; '
                f'font-size: {font_size}px; '
                f'color: {color}; '
                f'font-family: "{text_obj.font_name}", Arial, sans-serif;'
            )

            html_parts.append(f'<div class="text-element" style="{style}">{content}</div>')

        html_parts.append('</div>')

    html_parts.extend(['</body>', '</html>'])

    return '\n'.join(html_parts)


def _convert_to_markdown(pages_data: Dict[str, Any], pdf_path: str) -> str:
    """
    Converte dados extraídos do PDF para Markdown.
    Versão simplificada sem metadados desnecessários.

    Args:
        pages_data: Dados extraídos do PDF
        pdf_path: Caminho do PDF original

    Returns:
        String Markdown completa
    """
    md_parts = []

    for page_info in pages_data['pages']:
        page_num = page_info['page_num']
        text_objects = page_info['text_objects']

        # Separador de página (exceto primeira)
        if page_num > 0:
            md_parts.append('')
            md_parts.append('---')
            md_parts.append('')

        # Ordenar textos por posição (topo para baixo, esquerda para direita)
        sorted_texts = sorted(text_objects, key=lambda t: (t.y, t.x))

        # Agrupar textos por linha (mesma posição Y, com tolerância)
        # Tolerância para considerar textos na mesma linha (baseado na altura da fonte)
        y_tolerance = 5  # pixels

        current_line = []
        current_y = None
        lines = []

        for text_obj in sorted_texts:
            if not text_obj.content or not text_obj.content.strip():
                continue

            # Verificar se está na mesma linha (Y similar)
            if current_y is not None:
                y_diff = abs(text_obj.y - current_y)
                # Se a diferença de Y for maior que a tolerância, é nova linha
                if y_diff > y_tolerance:
                    # Salvar linha anterior
                    if current_line:
                        lines.append(current_line)
                    current_line = []
                    current_y = text_obj.y
            else:
                current_y = text_obj.y

            current_line.append(text_obj)

        # Adicionar última linha
        if current_line:
            lines.append(current_line)

            # Processar cada linha
        last_font_size = None

        for line_texts in lines:
            # Ordenar textos da linha da esquerda para direita
            line_texts_sorted = sorted(line_texts, key=lambda t: t.x)

            # Juntar textos da mesma linha, considerando espaçamento horizontal
            line_parts = []
            line_font_size = None
            last_x_end = None

            for text_obj in line_texts_sorted:
                content = text_obj.content.strip()
                if not content:
                    continue

                # Calcular fim do texto anterior (x + width)
                if last_x_end is not None:
                    # Calcular espaço entre textos
                    space_between = text_obj.x - last_x_end
                    # Se o espaço for muito grande (mais que 2x a largura do texto atual),
                    # adicionar espaço extra ou quebra
                    if space_between > (text_obj.width * 2):
                        # Espaço significativo - adicionar como separador
                        line_parts.append('  ')  # Dois espaços para indicar separação
                    elif space_between > 0:
                        # Espaço normal - adicionar um espaço
                        line_parts.append(' ')

                line_parts.append(content)
                last_x_end = text_obj.x + text_obj.width

                # Usar o maior tamanho de fonte da linha como referência
                if text_obj.font_size:
                    if line_font_size is None or text_obj.font_size > line_font_size:
                        line_font_size = text_obj.font_size

            if not line_parts:
                continue

            # Juntar conteúdo da linha
            line_text = ''.join(line_parts)

            # Verificar se deve adicionar quebra de linha antes
            # (se mudou muito o tamanho da fonte em relação à linha anterior)
            is_new_paragraph = False
            if last_font_size and line_font_size:
                size_ratio = line_font_size / last_font_size if last_font_size > 0 else 1
                if size_ratio > 1.3 or size_ratio < 0.7:
                    is_new_paragraph = True

            # Detectar se é título
            is_title = False
            if line_font_size and line_font_size > 14:
                is_title = True
            elif len(line_text) < 60 and line_text.isupper() and not line_text.replace(' ', '').replace('.', '').replace('-', '').isdigit():
                is_title = True

            # Adicionar quebra de linha se necessário
            if is_new_paragraph and md_parts:
                md_parts.append('')

            # Adicionar conteúdo
            if is_title:
                md_parts.append(f'## {line_text}')
            else:
                md_parts.append(line_text)

            last_font_size = line_font_size

        # Adicionar linha final se necessário
        if md_parts:
            md_parts.append('')

    return '\n'.join(md_parts)


def convert_pdf_to_html(
    pdf_path: str,
    html_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Converte um arquivo PDF para HTML preservando posicionamento e formatação.

    Args:
        pdf_path: Caminho do arquivo PDF de entrada
        html_path: Caminho do arquivo HTML de saída
        verbose: Se True, exibe informações detalhadas

    Returns:
        dict: Dicionário com informações sobre a conversão

    Raises:
        FileNotFoundError: Se o arquivo PDF não existir
        ValueError: Se os caminhos forem inválidos
    """
    logger = get_logger()

    # Validar arquivo de entrada
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Arquivo PDF nao encontrado: {pdf_path}")

    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Arquivo de entrada deve ser .pdf: {pdf_path}")

    # Validar caminho de saída
    html_file = Path(html_path)
    if not html_file.suffix.lower() in ['.html', '.htm']:
        raise ValueError(f"Arquivo de saida deve ser .html ou .htm: {html_path}")

    # Garantir que o diretório de saída existe
    html_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if verbose:
            print(f"[INFO] Lendo arquivo PDF: {pdf_path}")

        # Extrair dados do PDF
        if verbose:
            print("[INFO] Extraindo texto e imagens do PDF...")

        pages_data = _extract_pdf_data(pdf_path)
        num_pages = len(pages_data['pages'])

        if verbose:
            total_texts = sum(len(p['text_objects']) for p in pages_data['pages'])
            total_images = sum(len(p['image_objects']) for p in pages_data['pages'])
            print(f"[INFO] {num_pages} pagina(s) encontrada(s)")
            print(f"[INFO] {total_texts} objeto(s) de texto extraido(s)")
            print(f"[INFO] {total_images} imagem(ns) extraida(s)")
            print("[INFO] Convertendo para HTML...")

        # Converter para HTML
        html_content = _convert_to_html(pages_data, pdf_path)

        # Salvar HTML
        html_file.write_text(html_content, encoding='utf-8')

        if verbose:
            print(f"[INFO] HTML gerado com sucesso: {html_path}")

        result = {
            'status': 'success',
            'input_file': str(pdf_path),
            'output_file': str(html_path),
            'pages': num_pages
        }

        # Log da operação
        logger.log_operation(
            operation_type='pdf-to-html',
            status='success',
            input_file=str(pdf_path),
            output_file=str(html_path),
            parameters={
                'verbose': verbose
            },
            result={
                'pages': num_pages
            },
            notes=f"Conversao de PDF para HTML concluida com sucesso. Paginas: {num_pages}"
        )

        return result

    except Exception as e:
        error_msg = f"Erro ao converter PDF para HTML: {str(e)}"

        if verbose:
            print(f"[ERRO] {error_msg}")

        result = {
            'status': 'error',
            'input_file': str(pdf_path),
            'output_file': str(html_path),
            'error': str(e)
        }

        # Log do erro
        logger.log_operation(
            operation_type='pdf-to-html',
            status='error',
            input_file=str(pdf_path),
            output_file=str(html_path),
            parameters={
                'verbose': verbose
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        raise


def _convert_to_text(pages_data: Dict[str, Any], pdf_path: str) -> str:
    """
    Converte dados extraídos do PDF para texto puro (.txt).
    Usa a mesma lógica inteligente de detecção de quebras de linha do Markdown,
    mas sem formatação markdown.

    Args:
        pages_data: Dados extraídos do PDF
        pdf_path: Caminho do PDF original

    Returns:
        String de texto puro completa
    """
    txt_parts = []

    for page_info in pages_data['pages']:
        page_num = page_info['page_num']
        text_objects = page_info['text_objects']

        # Separador de página (exceto primeira)
        if page_num > 0:
            txt_parts.append('')
            txt_parts.append('=' * 80)
            txt_parts.append('')

        # Ordenar textos por posição (topo para baixo, esquerda para direita)
        sorted_texts = sorted(text_objects, key=lambda t: (t.y, t.x))

        # Agrupar textos por linha (mesma posição Y, com tolerância)
        y_tolerance = 5  # pixels

        current_line = []
        current_y = None
        lines = []

        for text_obj in sorted_texts:
            if not text_obj.content or not text_obj.content.strip():
                continue

            # Verificar se está na mesma linha (Y similar)
            if current_y is not None:
                y_diff = abs(text_obj.y - current_y)
                # Se a diferença de Y for maior que a tolerância, é nova linha
                if y_diff > y_tolerance:
                    # Salvar linha anterior
                    if current_line:
                        lines.append(current_line)
                    current_line = []
                    current_y = text_obj.y
            else:
                current_y = text_obj.y

            current_line.append(text_obj)

        # Adicionar última linha
        if current_line:
            lines.append(current_line)

        # Processar cada linha
        for line_texts in lines:
            # Ordenar textos da linha da esquerda para direita
            line_texts_sorted = sorted(line_texts, key=lambda t: t.x)

            # Juntar textos da mesma linha, considerando espaçamento horizontal
            line_parts = []
            last_x_end = None

            for text_obj in line_texts_sorted:
                content = text_obj.content.strip()
                if not content:
                    continue

                # Calcular fim do texto anterior (x + width)
                if last_x_end is not None:
                    # Calcular espaço entre textos
                    space_between = text_obj.x - last_x_end
                    # Se o espaço for muito grande (mais que 2x a largura do texto atual),
                    # adicionar espaço extra ou quebra
                    if space_between > (text_obj.width * 2):
                        # Espaço significativo - adicionar como separador
                        line_parts.append('  ')  # Dois espaços para indicar separação
                    elif space_between > 0:
                        # Espaço normal - adicionar um espaço
                        line_parts.append(' ')

                line_parts.append(content)
                last_x_end = text_obj.x + text_obj.width

            if not line_parts:
                continue

            # Juntar conteúdo da linha
            line_text = ''.join(line_parts)
            txt_parts.append(line_text)

    return '\n'.join(txt_parts)


def convert_pdf_to_txt(
    pdf_path: str,
    txt_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Converte um arquivo PDF para texto puro (.txt).

    Args:
        pdf_path: Caminho do arquivo PDF de entrada
        txt_path: Caminho do arquivo de texto de saída
        verbose: Se True, exibe informações detalhadas

    Returns:
        dict: Dicionário com informações sobre a conversão

    Raises:
        FileNotFoundError: Se o arquivo PDF não existir
        ValueError: Se os caminhos forem inválidos
    """
    logger = get_logger()

    # Validar arquivo de entrada
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Arquivo PDF nao encontrado: {pdf_path}")

    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Arquivo de entrada deve ser .pdf: {pdf_path}")

    # Validar caminho de saída
    txt_file = Path(txt_path)
    if not txt_file.suffix.lower() == '.txt':
        raise ValueError(f"Arquivo de saida deve ser .txt: {txt_path}")

    # Garantir que o diretório de saída existe
    txt_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if verbose:
            print(f"[INFO] Lendo arquivo PDF: {pdf_path}")

        # Extrair dados do PDF
        if verbose:
            print("[INFO] Extraindo texto do PDF...")

        pages_data = _extract_pdf_data(pdf_path)
        num_pages = len(pages_data['pages'])

        if verbose:
            total_texts = sum(len(p['text_objects']) for p in pages_data['pages'])
            print(f"[INFO] {num_pages} pagina(s) encontrada(s)")
            print(f"[INFO] {total_texts} objeto(s) de texto extraido(s)")
            print("[INFO] Convertendo para texto puro...")

        # Converter para texto puro
        txt_content = _convert_to_text(pages_data, pdf_path)

        # Salvar texto
        txt_file.write_text(txt_content, encoding='utf-8')

        if verbose:
            print(f"[INFO] Texto gerado com sucesso: {txt_path}")

        result = {
            'status': 'success',
            'input_file': str(pdf_path),
            'output_file': str(txt_path),
            'pages': num_pages
        }

        # Log da operação
        logger.log_operation(
            operation_type='pdf-to-txt',
            status='success',
            input_file=str(pdf_path),
            output_file=str(txt_path),
            parameters={
                'verbose': verbose
            },
            result={
                'pages': num_pages
            },
            notes=f"Conversao de PDF para texto puro concluida com sucesso. Paginas: {num_pages}"
        )

        return result

    except Exception as e:
        error_msg = f"Erro ao converter PDF para texto: {str(e)}"

        if verbose:
            print(f"[ERRO] {error_msg}")

        result = {
            'status': 'error',
            'input_file': str(pdf_path),
            'output_file': str(txt_path),
            'error': str(e)
        }

        # Log do erro
        logger.log_operation(
            operation_type='pdf-to-txt',
            status='error',
            input_file=str(pdf_path),
            output_file=str(txt_path),
            parameters={
                'verbose': verbose
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        raise


def convert_pdf_to_markdown(
    pdf_path: str,
    md_path: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Converte um arquivo PDF para Markdown sem metadados desnecessários.

    Args:
        pdf_path: Caminho do arquivo PDF de entrada
        md_path: Caminho do arquivo Markdown de saída
        verbose: Se True, exibe informações detalhadas

    Returns:
        dict: Dicionário com informações sobre a conversão

    Raises:
        FileNotFoundError: Se o arquivo PDF não existir
        ValueError: Se os caminhos forem inválidos
    """
    logger = get_logger()

    # Validar arquivo de entrada
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"Arquivo PDF nao encontrado: {pdf_path}")

    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Arquivo de entrada deve ser .pdf: {pdf_path}")

    # Validar caminho de saída
    md_file = Path(md_path)
    if not md_file.suffix.lower() == '.md':
        raise ValueError(f"Arquivo de saida deve ser .md: {md_path}")

    # Garantir que o diretório de saída existe
    md_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        if verbose:
            print(f"[INFO] Lendo arquivo PDF: {pdf_path}")

        # Extrair dados do PDF
        if verbose:
            print("[INFO] Extraindo texto do PDF...")

        pages_data = _extract_pdf_data(pdf_path)
        num_pages = len(pages_data['pages'])

        if verbose:
            total_texts = sum(len(p['text_objects']) for p in pages_data['pages'])
            print(f"[INFO] {num_pages} pagina(s) encontrada(s)")
            print(f"[INFO] {total_texts} objeto(s) de texto extraido(s)")
            print("[INFO] Convertendo para Markdown...")

        # Converter para Markdown
        md_content = _convert_to_markdown(pages_data, pdf_path)

        # Salvar Markdown
        md_file.write_text(md_content, encoding='utf-8')

        if verbose:
            print(f"[INFO] Markdown gerado com sucesso: {md_path}")

        result = {
            'status': 'success',
            'input_file': str(pdf_path),
            'output_file': str(md_path),
            'pages': num_pages
        }

        # Log da operação
        logger.log_operation(
            operation_type='pdf-to-md',
            status='success',
            input_file=str(pdf_path),
            output_file=str(md_path),
            parameters={
                'verbose': verbose
            },
            result={
                'pages': num_pages
            },
            notes=f"Conversao de PDF para Markdown concluida com sucesso. Paginas: {num_pages}"
        )

        return result

    except Exception as e:
        error_msg = f"Erro ao converter PDF para Markdown: {str(e)}"

        if verbose:
            print(f"[ERRO] {error_msg}")

        result = {
            'status': 'error',
            'input_file': str(pdf_path),
            'output_file': str(md_path),
            'error': str(e)
        }

        # Log do erro
        logger.log_operation(
            operation_type='pdf-to-md',
            status='error',
            input_file=str(pdf_path),
            output_file=str(md_path),
            parameters={
                'verbose': verbose
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        raise
