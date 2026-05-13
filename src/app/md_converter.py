"""
Módulo MD Converter - Conversão de Markdown para PDF.

Este módulo implementa a conversão de arquivos Markdown (.md) para PDF,
usando markdown2 para MD→HTML e weasyprint/xhtml2pdf para HTML→PDF.

Suporta Windows e Linux com fallback automático:
- WeasyPrint (preferido, melhor qualidade, funciona no Linux com dependências do sistema)
- xhtml2pdf (fallback portável, funciona em Windows e Linux sem dependências externas)

Suporte a Emojis e Símbolos Unicode:
- Detecta automaticamente a plataforma e usa fontes de emoji apropriadas
- Windows: Segoe UI Emoji, Segoe UI Symbol
- macOS: Apple Color Emoji
- Linux: Noto Color Emoji, Noto Emoji
- Fallback para fontes padrão se fontes de emoji não estiverem disponíveis
- Suporte a caracteres box-drawing (├──, └──, │) com fontes monospace; no xhtml2pdf
  são também convertidos para ASCII (+, |, -) para evitar quadrados incorretos

Limitações Conhecidas:
- xhtml2pdf (fallback) tem limitações com Unicode complexo:
  * Emojis coloridos podem aparecer como quadrados; alguns são substituídos por texto (ex.: aviso ⚠️ -> [!])
  * Blocos monospace usam stack com Segoe UI Symbol (Windows) / DejaVu (Linux) para box-drawing
- WeasyPrint oferece melhor suporte a Unicode quando disponível
- Recomendado usar WeasyPrint no Linux para melhor qualidade
"""

from pathlib import Path
from typing import Optional
import markdown2
import platform
import sys
from app.logging import get_logger


# Monkey-patch ANTES de importar WeasyPrint
# Isso captura a mensagem durante a importação das bibliotecas C
class SilentStderr:
    """Stderr que filtra mensagens do WeasyPrint sobre bibliotecas externas."""
    def __init__(self, original):
        self.original = original
        self.buffer = ""
        self.suppressing = False
        self.separator_count = 0

    def write(self, text: str) -> None:
        if not text:
            return

        # Acumular no buffer para processar linha por linha
        self.buffer += text

        # Processar linhas completas
        while '\n' in self.buffer:
            line, self.buffer = self.buffer.split('\n', 1)
            self._process_line(line + '\n')

        # Se buffer ficou muito grande sem quebra de linha, processar mesmo assim
        if len(self.buffer) > 1000:
            self._process_line(self.buffer)
            self.buffer = ""

    def _process_line(self, line: str) -> None:
        """Processa uma linha completa."""
        line_stripped = line.strip()
        line_lower = line.lower()

        # Detectar início do aviso - pode começar com separador ou diretamente com a mensagem
        if line_stripped == "-----":
            # Primeiro separador - pode ser início do aviso
            if not self.suppressing:
                self.suppressing = True
                self.separator_count = 1
            else:
                # Segundo separador - fim do bloco
                self.separator_count += 1
                if self.separator_count >= 2:
                    self.suppressing = False
                    self.separator_count = 0
            return  # Suprimir separadores

        # Detectar início do aviso pela mensagem
        if "weasyprint could not import" in line_lower:
            self.suppressing = True
            self.separator_count = 0
            return  # Suprimir

        # Se estamos suprimindo
        if self.suppressing:
            # Verificar se é linha vazia ou parte do aviso
            if (not line_stripped or
                "doc.courtbouillon.org" in line_lower or
                "installation steps" in line_lower or
                "troubleshooting" in line_lower or
                "first_steps.html" in line_lower or
                "please carefully follow" in line_lower):
                return  # Suprimir

            # Se encontrou nova mensagem (começa com "["), parar de suprimir
            if line_stripped.startswith("[") and not any(
                kw in line_lower for kw in ["http", "courtbouillon", "weasyprint"]
            ):
                self.suppressing = False
                self.separator_count = 0
                self.original.write(line)
                return

            return  # Continuar suprimindo

        # Não está suprimindo, escrever normalmente
        self.original.write(line)

    def flush(self) -> None:
        self.original.flush()
        # Resetar ao fazer flush
        self.buffer = ""
        self.suppressing = False
        self.separator_count = 0

    def __getattr__(self, name):
        return getattr(self.original, name)


# Aplicar o patch ANTES de importar WeasyPrint
_original_stderr = sys.stderr
sys.stderr = SilentStderr(sys.stderr)

# Tentar importar WeasyPrint (preferido, melhor qualidade e suporte a Unicode)
# Tem fallback automático para xhtml2pdf se não estiver disponível
WEASYPRINT_AVAILABLE = False
WEASYPRINT_ERROR = None
try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except (ImportError, OSError) as e:
    WEASYPRINT_ERROR = str(e)
finally:
    # Restaurar stderr original após importação
    sys.stderr = _original_stderr

# Fallback: xhtml2pdf (mais portável, funciona no Windows e Linux)
XHTML2PDF_AVAILABLE = False
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    pass


def _get_default_css() -> str:
    """
    Gera CSS padrão com suporte a emojis e caracteres especiais baseado na plataforma.

    Inclui:
    - Fontes de emoji por plataforma
    - Fontes monospace com suporte a box-drawing characters (├──, └──, │)
    - Suporte a símbolos Unicode especiais

    Returns:
        str: CSS completo com fontes apropriadas para a plataforma
    """
    system = platform.system()

    # Fontes de emoji por plataforma
    if system == 'Windows':
        emoji_fonts = '"Segoe UI Emoji", "Segoe UI Symbol"'
        # Segoe UI Symbol antes de Consolas: cobre box-drawing (├──), setas (←) e símbolos em <pre>
        monospace_fonts = (
            '"Segoe UI Symbol", "Consolas", "Courier New", "Lucida Console", monospace'
        )
    elif system == 'Darwin':  # macOS
        emoji_fonts = '"Apple Color Emoji"'
        monospace_fonts = '"Menlo", "Monaco", "Courier New", monospace'
    else:  # Linux e outros
        emoji_fonts = '"Noto Color Emoji", "Noto Emoji"'
        # Fontes monospace com suporte a box-drawing no Linux
        monospace_fonts = '"DejaVu Sans Mono", "Liberation Mono", "Courier New", monospace'

    # CSS padrão com suporte a emojis e caracteres especiais
    return f"""
@page {{
    size: A4;
    margin: 2cm;
}}

body {{
    font-family: {emoji_fonts}, "DejaVu Sans", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333;
    /* Garantir que Unicode seja preservado */
    unicode-bidi: embed;
}}

h1 {{
    font-size: 24pt;
    color: #2c3e50;
    margin-top: 1em;
    margin-bottom: 0.5em;
    border-bottom: 2px solid #3498db;
    padding-bottom: 0.3em;
}}

h2 {{
    font-size: 20pt;
    color: #34495e;
    margin-top: 0.8em;
    margin-bottom: 0.4em;
    border-bottom: 1px solid #bdc3c7;
    padding-bottom: 0.2em;
}}

h3 {{
    font-size: 16pt;
    color: #34495e;
    margin-top: 0.6em;
    margin-bottom: 0.3em;
}}

h4 {{
    font-size: 14pt;
    color: #34495e;
    margin-top: 0.5em;
    margin-bottom: 0.3em;
}}

h5, h6 {{
    font-size: 12pt;
    color: #34495e;
    margin-top: 0.4em;
    margin-bottom: 0.2em;
}}

p {{
    margin: 0.5em 0;
    text-align: justify;
    /* Preservar caracteres especiais e emojis */
    font-family: {emoji_fonts}, "DejaVu Sans", Arial, sans-serif;
}}

/* Preservar estrutura de diretórios - usar monospace para blocos de texto */
.directory-structure {{
    font-family: {monospace_fonts};
    background-color: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 1em;
    margin: 1em 0;
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    font-size: 9pt;
    line-height: 1.4;
    overflow-x: visible;
}}

ul, ol {{
    margin: 0.5em 0;
    padding-left: 2em;
}}

li {{
    margin: 0.3em 0;
}}

code {{
    font-family: {monospace_fonts};
    font-size: 10pt;
    background-color: #f4f4f4;
    padding: 0.1em 0.3em;
    border-radius: 3px;
    /* Preservar espaços e quebras de linha */
    white-space: pre-wrap;
    word-wrap: break-word;
}}

pre {{
    background-color: #f8f8f8;
    border: 1px solid #ddd;
    border-radius: 5px;
    padding: 1em;
    overflow-x: visible;
    font-family: {monospace_fonts};
    font-size: 9pt;
    line-height: 1.4;
    /* pre-wrap evita corte no PDF; word-wrap para linhas longas (TypeScript etc.) */
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    font-variant-ligatures: none;
}}

pre code {{
    background-color: #f8f8f8;
    padding: 0;
    border-radius: 0;
}}

blockquote {{
    border-left: 4px solid #3498db;
    margin: 1em 0;
    padding-left: 1em;
    color: #7f8c8d;
    font-style: italic;
    /* xhtml2pdf: itálico sem stack de emoji tende a perder glifos (ex.: ⚠️) */
    font-family: {emoji_fonts}, "DejaVu Sans", Arial, sans-serif;
}}

table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    table-layout: fixed;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
    vertical-align: top;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
}}

th {{
    background-color: #3498db;
    color: white;
    font-weight: bold;
}}

tr:nth-child(even) {{
    background-color: #f9f9f9;
}}

img {{
    max-width: 100%;
    height: auto;
    margin: 1em 0;
    display: block;
}}

a {{
    color: #3498db;
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

hr {{
    border: none;
    border-top: 1px solid #ddd;
    margin: 2em 0;
}}
"""

# CSS padrão (mantido para compatibilidade, mas usar _get_default_css() é recomendado)
DEFAULT_CSS = _get_default_css()

_MARKDOWN2_EXTRAS = [
    'fenced-code-blocks',
    'tables',
    'break-on-newline',
    'code-friendly',
    'header-ids',
]


def _substitute_xhtml2pdf_problematic_chars(text: str) -> str:
    """
    Substitui caracteres que o xhtml2pdf/ReportLab costuma renderizar como quadrados
    ou glifos incorretos.

    Mantém o Markdown legível; aplicado só no fluxo xhtml2pdf (WeasyPrint não precisa).
    """
    # Box Drawing (U+2500..U+257F): ReportLab muitas vezes não mapeia bem → ASCII
    box_map = {
        '\u2500': '-',  # ─
        '\u2502': '|',  # │
        '\u251c': '+',  # ├
        '\u2514': '`',  # └
        '\u252c': '+',  # ┬
        '\u2534': '+',  # ┴
        '\u253c': '+',  # ┼
        '\u250c': '+',  # ┌
        '\u2510': '+',  # ┐
        '\u2518': '+',  # ┘
    }
    out: list[str] = []
    for ch in text:
        o = ord(ch)
        if 0x2500 <= o <= 0x257F:
            out.append(box_map.get(ch, '-'))
        else:
            out.append(ch)
    text = ''.join(out)

    replacements = (
        ("\u26a0\ufe0f", "[!]"),  # ⚠️ (U+26A0 + VS16)
        ("\u26a0", "[!]"),      # ⚠ sem seletor de estilo
    )
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def _markdown_to_body_html(md_content: str) -> str:
    """Converte Markdown para fragmento HTML do body (com pós-processamento de box-drawing)."""
    html_content = markdown2.markdown(md_content, extras=_MARKDOWN2_EXTRAS)
    return _process_html_for_special_chars(html_content)


def _wrap_full_html(body_html: str, document_title: str) -> str:
    """Envolve o HTML do body em documento completo para WeasyPrint/xhtml2pdf."""
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF gerado de {document_title}</title>
</head>
<body>
{body_html}
</body>
</html>
"""


def _process_html_for_special_chars(html_content: str) -> str:
    """
    Processa HTML para preservar estruturas de diretórios e caracteres especiais.

    Detecta parágrafos com box-drawing characters (├──, └──, │) e os converte
    em blocos <pre> para garantir renderização correta com fontes monospace.

    Args:
        html_content: Conteúdo HTML gerado do Markdown

    Returns:
        str: HTML processado com estruturas de diretórios preservadas
    """
    import re

    # Caracteres box-drawing comuns em estruturas de diretórios
    box_chars_pattern = r'[├└│─┬┴┼┐┌┘└]'

    # Encontrar parágrafos que contêm estruturas de diretórios
    # Padrão: <p>linha com box-drawing</p> seguido de mais linhas similares
    def replace_directory_blocks(match):
        """Substitui blocos de parágrafos com box-drawing por <pre>"""
        full_match = match.group(0)
        # Extrair apenas o conteúdo (sem tags <p>)
        content = re.sub(r'</?p[^>]*>', '', full_match)
        content = re.sub(r'<br\s*/?>', '\n', content)  # Converter <br> em quebras de linha
        # Limpar espaços extras mas preservar estrutura
        lines = [line.rstrip() for line in content.split('\n') if line.strip()]
        if lines:
            return f'<pre class="directory-structure">\n' + '\n'.join(lines) + '\n</pre>'
        return full_match

    # Padrão para detectar blocos de parágrafos com box-drawing
    # Procura por sequências de <p> que contêm box-drawing characters
    pattern = r'(<p[^>]*>.*?' + box_chars_pattern + r'.*?</p>(?:\s*<p[^>]*>.*?' + box_chars_pattern + r'.*?</p>)*)'

    # Aplicar substituição
    processed = re.sub(pattern, replace_directory_blocks, html_content, flags=re.DOTALL | re.IGNORECASE)

    return processed


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

    # Carregar CSS (customizado ou padrão com suporte a emojis)
    css_content = _get_default_css()
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

        if verbose:
            print("[INFO] Convertendo Markdown para HTML...")

        def build_full_html(md_src: str) -> str:
            body = _markdown_to_body_html(md_src)
            return _wrap_full_html(body, md_file.name)

        # Converter HTML para PDF
        if verbose:
            print("[INFO] Convertendo HTML para PDF...")

        # Resolver caminhos relativos de imagens
        base_url = str(md_file.parent.absolute())

        # Detectar plataforma para mensagens informativas
        is_windows = platform.system() == 'Windows'

        # Tentar usar WeasyPrint primeiro (melhor qualidade, suporte a Unicode/emojis)
        # Tem fallback automático para xhtml2pdf se falhar
        if WEASYPRINT_AVAILABLE:
            full_html = build_full_html(md_content)
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
                        print("[INFO] Usando CSS padrao (WeasyPrint) com suporte a emojis")

                    css_obj = CSS(string=_get_default_css())

                # Gerar PDF (aplicar filtro também durante uso, não apenas importação)
                _original_stderr_use = sys.stderr
                sys.stderr = SilentStderr(sys.stderr)
                try:
                    html_doc = HTML(string=full_html, base_url=base_url)
                    html_doc.write_pdf(pdf_path, stylesheets=[css_obj])
                finally:
                    sys.stderr = _original_stderr_use

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

                # Regenerar HTML com substituições amigáveis ao ReportLab
                full_html = build_full_html(_substitute_xhtml2pdf_problematic_chars(md_content))
                _convert_with_xhtml2pdf(full_html, pdf_path, css_path, base_url, verbose)
        elif XHTML2PDF_AVAILABLE:
            # Usar xhtml2pdf diretamente (WeasyPrint não disponível)
            if verbose:
                if WEASYPRINT_ERROR:
                    print(f"[INFO] WeasyPrint nao disponivel: {WEASYPRINT_ERROR}")
                print("[INFO] Usando xhtml2pdf (portavel, funciona em Windows e Linux)")

            full_html = build_full_html(_substitute_xhtml2pdf_problematic_chars(md_content))
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
