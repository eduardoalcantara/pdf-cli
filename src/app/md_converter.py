"""
Módulo MD Converter - Conversão de Markdown para PDF.

Este módulo implementa a conversão de arquivos Markdown (.md) para PDF,
usando markdown2 para MD→HTML e weasyprint/xhtml2pdf para HTML→PDF.

Suporta Windows e Linux com fallback automático:
- WeasyPrint (preferido, melhor qualidade, funciona no Linux com dependências do sistema)
- xhtml2pdf (fallback portável, funciona em Windows e Linux sem dependências externas)
"""

from pathlib import Path
from typing import Optional
import markdown2
import platform
from app.logging import get_logger

# Tentar importar WeasyPrint (preferido, mas pode falhar no Windows sem dependências)
WEASYPRINT_AVAILABLE = False
WEASYPRINT_ERROR = None
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_ERROR = str(e)

# Fallback: xhtml2pdf (mais portável, funciona no Windows e Linux)
XHTML2PDF_AVAILABLE = False
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    pass


# CSS padrão para formatação do PDF
DEFAULT_CSS = """
@page {
    size: A4;
    margin: 2cm;
}

body {
    font-family: "DejaVu Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
}

h1 {
    font-size: 24pt;
    color: #2c3e50;
    margin-top: 1em;
    margin-bottom: 0.5em;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.3em;
}

h2 {
    font-size: 20pt;
    color: #34495e;
    margin-top: 0.8em;
    margin-bottom: 0.4em;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 0.2em;
}

h3 {
    font-size: 16pt;
    color: #34495e;
    margin-top: 0.6em;
    margin-bottom: 0.3em;
}

h4 {
    font-size: 14pt;
    color: #34495e;
    margin-top: 0.5em;
    margin-bottom: 0.3em;
}

h5, h6 {
    font-size: 12pt;
    color: #34495e;
    margin-top: 0.4em;
    margin-bottom: 0.2em;
}

p {
    margin: 0.5em 0;
    text-align: justify;
}

ul, ol {
    margin: 0.5em 0;
    padding-left: 2em;
}

li {
    margin: 0.3em 0;
}

code {
    font-family: "Courier New", monospace;
    font-size: 10pt;
    background-color: #f4f4f4;
    padding: 0.1em 0.3em;
    border-radius: 3px;
}

pre {
    background-color: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 1em;
    overflow-x: auto;
    font-family: "Courier New", monospace;
    font-size: 9pt;
    line-height: 1.4;
}

pre code {
    background-color: #f8f8f8;
    padding: 0;
    border-radius: 0;
}

blockquote {
    border-left: 4px solid #3498db;
    margin: 1em 0;
    padding-left: 1em;
    color: #7f8c8d;
    font-style: italic;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}

th, td {
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
}

th {
    background-color: #3498db;
    color: white;
    font-weight: bold;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

img {
    max-width: 100%;
    height: auto;
    margin: 1em 0;
    display: block;
}

a {
    color: #3498db;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

hr {
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}
"""


def _convert_with_xhtml2pdf(
    html_content: str,
    pdf_path: str,
    css_path: Optional[str],
    base_url: str,
    verbose: bool
) -> None:
    """
    Converte HTML para PDF usando xhtml2pdf (fallback para Windows).

    Args:
        html_content: Conteúdo HTML completo
        pdf_path: Caminho do PDF de saída
        css_path: Caminho opcional para CSS customizado
        base_url: URL base para recursos (imagens, etc.)
        verbose: Se True, exibe informações detalhadas
    """
    from io import BytesIO

    # Carregar CSS (customizado ou padrão)
    css_content = DEFAULT_CSS
    if css_path:
        css_file = Path(css_path)
        if not css_file.exists():
            raise FileNotFoundError(f"Arquivo CSS nao encontrado: {css_path}")

        if verbose:
            print(f"[INFO] Usando CSS customizado: {css_path}")

        css_content = css_file.read_text(encoding='utf-8')
    else:
        if verbose:
            print("[INFO] Usando CSS padrao (xhtml2pdf)")

    # Inserir CSS no HTML (xhtml2pdf precisa do CSS inline ou em <style>)
    # Extrair apenas o conteúdo do body se existir
    if '<body>' in html_content and '</body>' in html_content:
        body_start = html_content.find('<body>') + 6
        body_end = html_content.find('</body>')
        body_content = html_content[body_start:body_end]
    else:
        # Se não tiver body, usar o conteúdo completo
        body_content = html_content

    html_with_css = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <style>
{css_content}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""

    # Converter usando xhtml2pdf
    # Usar pathlib para garantir compatibilidade multiplataforma
    pdf_path_obj = Path(pdf_path)
    pdf_path_obj.parent.mkdir(parents=True, exist_ok=True)

    with open(pdf_path, 'wb') as result_file:
        pisa_status = pisa.CreatePDF(
            BytesIO(html_with_css.encode('utf-8')),
            dest=result_file,
            encoding='utf-8',
            link_callback=None  # Para imagens, precisaria de callback customizado
        )

    if pisa_status.err:
        raise RuntimeError(f"Erro ao gerar PDF com xhtml2pdf: {pisa_status.err}")


def convert_md_to_pdf(
    md_path: str,
    pdf_path: str,
    css_path: Optional[str] = None,
    verbose: bool = False
) -> dict:
    """
    Converte um arquivo Markdown para PDF.

    Args:
        md_path: Caminho do arquivo Markdown (.md)
        pdf_path: Caminho do arquivo PDF de saída (.pdf)
        css_path: Caminho opcional para arquivo CSS customizado
        verbose: Se True, exibe informações detalhadas

    Returns:
        dict: Dicionário com informações sobre a conversão:
            - status: "success" ou "error"
            - input_file: Caminho do arquivo de entrada
            - output_file: Caminho do arquivo de saída
            - pages: Número de páginas geradas (se sucesso)
            - error: Mensagem de erro (se falhou)

    Raises:
        FileNotFoundError: Se o arquivo markdown não existir
        ValueError: Se os caminhos forem inválidos
    """
    logger = get_logger()

    # Validar arquivo de entrada
    md_file = Path(md_path)
    if not md_file.exists():
        raise FileNotFoundError(f"Arquivo markdown nao encontrado: {md_path}")

    if not md_file.suffix.lower() == '.md':
        raise ValueError(f"Arquivo de entrada deve ser .md: {md_path}")

    # Validar caminho de saída
    pdf_file = Path(pdf_path)
    if not pdf_file.suffix.lower() == '.pdf':
        raise ValueError(f"Arquivo de saida deve ser .pdf: {pdf_path}")

    # Garantir que o diretório de saída existe
    pdf_file.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Ler conteúdo do markdown
        if verbose:
            print(f"[INFO] Lendo arquivo markdown: {md_path}")

        md_content = md_file.read_text(encoding='utf-8')

        # Converter Markdown para HTML
        if verbose:
            print("[INFO] Convertendo Markdown para HTML...")

        # Usar markdown2 com extensões para melhor suporte
        html_content = markdown2.markdown(
            md_content,
            extras=[
                'fenced-code-blocks',  # Blocos de código com ```
                'tables',              # Tabelas
                'break-on-newline',    # Quebras de linha
                'code-friendly',       # Código mais amigável
                'header-ids',          # IDs nos cabeçalhos
            ]
        )

        # Criar HTML completo com CSS
        full_html = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF gerado de {md_file.name}</title>
</head>
<body>
{html_content}
</body>
</html>
"""

        # Converter HTML para PDF
        if verbose:
            print("[INFO] Convertendo HTML para PDF...")

        # Resolver caminhos relativos de imagens
        base_url = str(md_file.parent.absolute())

        # Detectar plataforma para mensagens informativas
        is_windows = platform.system() == 'Windows'

        # Tentar usar WeasyPrint primeiro (melhor qualidade, funciona bem no Linux)
        if WEASYPRINT_AVAILABLE:
            try:
                # Carregar CSS (customizado ou padrão)
                if css_path:
                    css_file = Path(css_path)
                    if not css_file.exists():
                        raise FileNotFoundError(f"Arquivo CSS nao encontrado: {css_path}")

                    if verbose:
                        print(f"[INFO] Usando CSS customizado: {css_path}")

                    css_content = css_file.read_text(encoding='utf-8')
                    css_obj = CSS(string=css_content)
                else:
                    if verbose:
                        print("[INFO] Usando CSS padrao (WeasyPrint)")

                    css_obj = CSS(string=DEFAULT_CSS)

                html_doc = HTML(string=full_html, base_url=base_url)
                html_doc.write_pdf(pdf_path, stylesheets=[css_obj])

                if verbose:
                    print("[INFO] PDF gerado usando WeasyPrint")

            except Exception as weasy_error:
                # WeasyPrint falhou, tentar fallback
                if verbose:
                    print(f"[AVISO] WeasyPrint falhou: {str(weasy_error)}")
                    if is_windows:
                        print("[INFO] No Windows, WeasyPrint requer bibliotecas do sistema (GTK).")
                    print("[INFO] Tentando usar xhtml2pdf como fallback...")

                # Fallback para xhtml2pdf
                if not XHTML2PDF_AVAILABLE:
                    error_msg = (
                        f"WeasyPrint falhou e xhtml2pdf nao esta disponivel.\n"
                        f"Erro WeasyPrint: {str(weasy_error)}\n"
                    )
                    if is_windows:
                        error_msg += (
                            "No Windows, WeasyPrint requer bibliotecas GTK instaladas.\n"
                            "Recomendacao: Instale xhtml2pdf (portavel): pip install xhtml2pdf\n"
                            "Ou instale as dependencias do WeasyPrint para Windows."
                        )
                    else:
                        error_msg += (
                            "No Linux, instale as dependencias do sistema para WeasyPrint:\n"
                            "  Ubuntu/Debian: sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0\n"
                            "Ou instale xhtml2pdf como alternativa: pip install xhtml2pdf"
                        )
                    raise RuntimeError(error_msg)

                # Usar xhtml2pdf
                _convert_with_xhtml2pdf(full_html, pdf_path, css_path, base_url, verbose)
        elif XHTML2PDF_AVAILABLE:
            # Usar xhtml2pdf diretamente (WeasyPrint não disponível)
            if verbose:
                if WEASYPRINT_ERROR:
                    print(f"[INFO] WeasyPrint nao disponivel: {WEASYPRINT_ERROR}")
                print("[INFO] Usando xhtml2pdf (portavel, funciona em Windows e Linux)")

            _convert_with_xhtml2pdf(full_html, pdf_path, css_path, base_url, verbose)
        else:
            # Nenhuma biblioteca disponível
            error_msg = (
                "Nenhuma biblioteca de conversao HTML->PDF disponivel.\n"
                "Instale uma das opcoes:\n"
                "  - xhtml2pdf (recomendado, portavel): pip install xhtml2pdf\n"
            )
            if not is_windows:
                error_msg += (
                    "  - weasyprint (melhor qualidade, requer dependencias do sistema): pip install weasyprint\n"
                    "    Depois instale: sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0"
                )
            else:
                error_msg += (
                    "  - weasyprint (requer GTK no Windows): pip install weasyprint\n"
                    "    Consulte: https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#windows"
                )
            raise RuntimeError(error_msg)

        # Obter número de páginas do PDF gerado
        try:
            import fitz
            pdf_doc = fitz.open(pdf_path)
            num_pages = len(pdf_doc)
            pdf_doc.close()
        except Exception:
            num_pages = None

        if verbose:
            print(f"[INFO] PDF gerado com sucesso: {pdf_path}")
            if num_pages:
                print(f"[INFO] Numero de paginas: {num_pages}")

        result = {
            'status': 'success',
            'input_file': str(md_path),
            'output_file': str(pdf_path),
            'pages': num_pages
        }

        # Log da operação
        logger.log_operation(
            operation_type='md-to-pdf',
            status='success',
            input_file=str(md_path),
            output_file=str(pdf_path),
            parameters={
                'css_path': css_path,
                'verbose': verbose
            },
            result={
                'pages': num_pages
            },
            notes=f"Conversao de Markdown para PDF concluida com sucesso. Paginas: {num_pages or 'N/A'}"
        )

        return result

    except Exception as e:
        error_msg = f"Erro ao converter markdown para PDF: {str(e)}"

        if verbose:
            print(f"[ERRO] {error_msg}")

        result = {
            'status': 'error',
            'input_file': str(md_path),
            'output_file': str(pdf_path),
            'error': str(e)
        }

        # Log do erro
        logger.log_operation(
            operation_type='md-to-pdf',
            status='error',
            input_file=str(md_path),
            output_file=str(pdf_path),
            parameters={
                'css_path': css_path,
                'verbose': verbose
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        raise
