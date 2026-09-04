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
  * Emojis/símbolos (❌ ✅ ⚠️) são convertidos para texto ASCII ([X] [OK] [!])
  * Blocos monospace usam stack com Segoe UI Symbol (Windows) / DejaVu (Linux) para box-drawing
- WeasyPrint oferece melhor suporte a Unicode quando disponível
- Recomendado usar WeasyPrint no Linux para melhor qualidade

Quebra de página manual no Markdown (linha inteira):

- Recomendado: ``<!-- pdf-cli:pagebreak -->`` (invisível no preview Markdown)
- Alternativas: ``\\pagebreak`` | ``[pagebreak]``
- Legado (opt-in via ``--pagebreak-on-hr``): ``---`` (regra horizontal Markdown)

Blocos Mermaid (`` ```mermaid `` ``):
- Renderizados localmente via ``mmdc`` ou ``npx @mermaid-js/mermaid-cli`` para PNG
- Sem envio a APIs online (privacidade); fallback para caixa de código se CLI ausente
- Desligar com ``--no-mermaid``
"""

from pathlib import Path
from typing import List, Optional, Sequence, Tuple
import contextlib
import html as html_module
import markdown2
import os
import platform
import re
import shutil
import subprocess
import sys
from app.logging import get_logger


# Monkey-patch ANTES de importar WeasyPrint
# Isso captura a mensagem durante a importação das bibliotecas C
class SilentStderr:
    """
    Stderr que oculta ruído de bibliotecas nativas (WeasyPrint/GTK/Fontconfig).

    Não deve expor detalhes de implementação (Python, GTK, UWP) ao usuário final.
    """

    _NOISE_SUBSTRINGS = (
        'weasyprint could not import',
        'doc.courtbouillon.org',
        'installation steps',
        'troubleshooting',
        'first_steps.html',
        'please carefully follow',
        'glib-gio-warning',
        'glib-warning',
        'glib-gobject-warning',
        'glib-critical',
        'fontconfig error',
        'fontconfig warning',
        'unexpectedly, uwp app',
        'cannot load default config file',
    )

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

    def _is_noise_line(self, line: str) -> bool:
        """Retorna True se a linha for ruído conhecido de GTK/WeasyPrint/Fontconfig."""
        line_lower = line.lower()
        if any(marker in line_lower for marker in self._NOISE_SUBSTRINGS):
            return True
        # Ex.: (process:21820): GLib-GIO-WARNING **: ...
        if re.match(r'^\(process:\d+\):\s*glib', line_lower.strip()):
            return True
        return False

    def _process_line(self, line: str) -> None:
        """Processa uma linha completa."""
        line_stripped = line.strip()
        line_lower = line.lower()

        if self._is_noise_line(line):
            return

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


@contextlib.contextmanager
def _quiet_native_stderr():
    """
    Redireciona o stderr nativo (fd 2) para NUL.

    Bibliotecas C (GTK/GLib/Fontconfig) escrevem direto no descritor de arquivo,
    contornando ``sys.stderr`` do Python. Este contexto oculta esse ruído.
    """
    try:
        devnull_fd = os.open(os.devnull, os.O_WRONLY)
    except OSError:
        yield
        return

    try:
        saved_fd = os.dup(2)
    except OSError:
        os.close(devnull_fd)
        yield
        return

    try:
        os.dup2(devnull_fd, 2)
        yield
    finally:
        try:
            os.dup2(saved_fd, 2)
        finally:
            os.close(saved_fd)
            os.close(devnull_fd)


# Aplicar o patch ANTES de importar WeasyPrint
_original_stderr = sys.stderr
sys.stderr = SilentStderr(sys.stderr)

# Tentar importar WeasyPrint (preferido, melhor qualidade e suporte a Unicode)
# Tem fallback automático para xhtml2pdf se não estiver disponível
WEASYPRINT_AVAILABLE = False
WEASYPRINT_ERROR = None
try:
    with _quiet_native_stderr():
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


def _get_default_css(landscape: bool = False) -> str:
    """
    Gera CSS padrão com suporte a emojis e caracteres especiais baseado na plataforma.

    Inclui:
    - Fontes de emoji por plataforma
    - Fontes monospace com suporte a box-drawing characters (├──, └──, │)
    - Suporte a símbolos Unicode especiais
    - Orientação retrato (padrão) ou paisagem via parâmetro landscape

    Args:
        landscape: Se True, usa página A4 em paisagem (útil para tabelas largas).

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

    page_size = "A4 landscape" if landscape else "A4"
    page_margin = "1.5cm" if landscape else "2cm"
    # xhtml2pdf/ReportLab: padding em ``em`` quebra tabelas largas em paisagem;
    # padding em ``px``/``pt`` quebra em retrato com muitas tabelas.
    # xhtml2pdf/ReportLab: em paisagem, ``fixed`` + ``2pt`` evita colunas com largura negativa.
    table_layout = "fixed"
    cell_padding = "2pt" if landscape else "0.5em"
    table_font_size = "7pt" if landscape else "8pt"

    # CSS padrão com suporte a emojis e caracteres especiais
    return f"""
@page {{
    size: {page_size};
    margin: {page_margin};
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
    table-layout: {table_layout};
    font-size: {table_font_size};
}}

th, td {{
    border: 1px solid #ddd;
    padding: {cell_padding};
    text-align: left;
    vertical-align: top;
    word-wrap: break-word;
    overflow-wrap: break-word;
    line-height: 1.25;
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

/* Quebra de página manual: use <!-- pdf-cli:pagebreak --> (recomendado), \\pagebreak ou [pagebreak] no .md */
.pdf-cli-page-break {{
    display: block;
    page-break-before: always;
    break-before: page;
    height: 0;
    margin: 0;
    padding: 0;
    border: none;
    visibility: hidden;
}}
"""

# CSS padrão retrato (mantido para compatibilidade; preferir _get_default_css())
DEFAULT_CSS = _get_default_css()

_MARKDOWN2_EXTRAS = [
    'fenced-code-blocks',
    'tables',
    'break-on-newline',
    'code-friendly',
    'header-ids',
]

# Marcadores de quebra de página aceitos no Markdown (linha inteira).
# ``---`` só é considerado com ``pagebreak_on_hr=True`` (--pagebreak-on-hr).
_PAGE_BREAK_LINE_PATTERNS = (
    r'^\s*<!--\s*pdf-cli:pagebreak\s*-->\s*$',
    r'^\s*\\pagebreak\s*$',
    r'^\s*\[pagebreak\]\s*$',
)

_PAGE_BREAK_HR_PATTERN = r'^\s*---\s*$'

_PAGE_BREAK_HTML = '\n<div class="pdf-cli-page-break"></div>\n'

# Blocos fenced ```mermaid ... ``` (linguagem case-insensitive).
_MERMAID_FENCE_RE = re.compile(
    r'^```mermaid[ \t]*\r?\n(.*?)```',
    re.MULTILINE | re.DOTALL | re.IGNORECASE,
)

_MERMAID_WORKDIR_NAME = '.pdf-cli-mermaid'
_MERMAID_CLI_TIMEOUT_SEC = 180
_MERMAID_PNG_WIDTH = 1200

# Substituições de símbolos Unicode → texto ASCII para xhtml2pdf/ReportLab.
_XHTML2PDF_SYMBOL_REPLACEMENTS = (
    ("\u274c\ufe0f", "[X]"),   # ❌ + VS16
    ("\u274c", "[X]"),         # ❌
    ("\u2705\ufe0f", "[OK]"),  # ✅ + VS16
    ("\u2705", "[OK]"),        # ✅
    ("\u2713\ufe0f", "[v]"),   # ✓ + VS16
    ("\u2713", "[v]"),         # ✓
    ("\u2717", "[x]"),         # ✗
    ("\u2718", "[x]"),         # ✘
    ("\u26a0\ufe0f", "[!]"),   # ⚠️
    ("\u26a0", "[!]"),         # ⚠
    ("\u2753\ufe0f", "[?]"),   # ❓ + VS16
    ("\u2753", "[?]"),         # ❓
    ("\U0001f50d\ufe0f", "[~]"),  # 🔍 + VS16
    ("\U0001f50d", "[~]"),        # 🔍
)

# Limites globais de fallback para colunas sem perfil reconhecido.
_COL_WIDTH_MIN_PCT = 6.0
_COL_WIDTH_MAX_PCT = 36.0


def _column_profile_for_header(header: str) -> dict:
    """
    Perfil de largura por tipo de coluna (cabeçalho).

    ``data_only``: mede largura só pelas linhas de dados, não pelo título
    (evita que "Habilitado" estique a coluna; o conteúdo é só ``[X]``).
    """
    h = re.sub(r'[^\w\s-]', '', header.lower()).strip()
    h_norm = h.replace('í', 'i').replace('ó', 'o')

    if 'habilitado' in h or h in ('status', 'ativo'):
        return {'min_pct': 5.0, 'max_pct': 7.5, 'data_only': True}
    if 'simbolo' in h_norm:
        return {'min_pct': 6.0, 'max_pct': 9.0, 'data_only': True}
    if 'significado' in h:
        return {'min_pct': 28.0, 'max_pct': 75.0, 'data_only': False}
    if h == 'nome' or h.startswith('nome'):
        return {'min_pct': 17.0, 'max_pct': 26.0, 'data_only': False}
    if 'cargo' in h:
        return {'min_pct': 11.0, 'max_pct': 20.0, 'data_only': False}
    if 'setor' in h:
        return {'min_pct': 8.0, 'max_pct': 14.0, 'data_only': False}
    if 'mail' in h or h == 'login' or 'e-mail' in h:
        return {'min_pct': 12.0, 'max_pct': 18.0, 'data_only': False}
    if 'grupo' in h:
        return {'min_pct': 8.0, 'max_pct': 12.0, 'data_only': False}
    if 'zona' in h:
        return {'min_pct': 20.0, 'max_pct': 34.0, 'data_only': False}

    return {
        'min_pct': _COL_WIDTH_MIN_PCT,
        'max_pct': _COL_WIDTH_MAX_PCT,
        'data_only': False,
    }


def _preprocess_markdown(md_content: str, pagebreak_on_hr: bool = False) -> str:
    """
    Pré-processa Markdown antes da conversão para HTML.

    Converte marcadores de quebra de página em bloco HTML compatível com
    WeasyPrint e xhtml2pdf.

    Marcadores aceitos (linha inteira no .md):

    - ``<!-- pdf-cli:pagebreak -->`` (recomendado; invisível no preview MD)
    - ``\\pagebreak``
    - ``[pagebreak]``
    - ``---`` somente se ``pagebreak_on_hr=True`` (legado; não afeta ``|------|`` em tabelas)

    Args:
        md_content: Conteúdo Markdown original.
        pagebreak_on_hr: Se True, trata ``---`` em linha isolada como quebra de página.

    Returns:
        str: Markdown com quebras de página materializadas em HTML.
    """
    patterns = list(_PAGE_BREAK_LINE_PATTERNS)
    if pagebreak_on_hr:
        patterns.append(_PAGE_BREAK_HR_PATTERN)

    processed = md_content
    for pattern in patterns:
        processed = re.sub(
            pattern,
            _PAGE_BREAK_HTML,
            processed,
            flags=re.MULTILINE | re.IGNORECASE,
        )
    return processed


def _find_mermaid_cli() -> Optional[List[str]]:
    """
    Localiza o Mermaid CLI no sistema.

    Ordem de preferência:
    1. ``mmdc`` (ou ``mmdc.cmd`` no Windows) no PATH
    2. ``npx --yes @mermaid-js/mermaid-cli``

    Returns:
        Lista de argumentos iniciais do comando, ou None se indisponível.
    """
    for name in ('mmdc', 'mmdc.cmd'):
        found = shutil.which(name)
        if found:
            return [found]

    for name in ('npx', 'npx.cmd'):
        found = shutil.which(name)
        if found:
            return [found, '--yes', '@mermaid-js/mermaid-cli']

    return None


def _run_mmdc(
    cli: Sequence[str],
    input_mmd: Path,
    output_png: Path,
    timeout: int = _MERMAID_CLI_TIMEOUT_SEC,
) -> None:
    """
    Executa o Mermaid CLI para gerar um PNG a partir de um arquivo ``.mmd``.

    Args:
        cli: Comando base (``mmdc`` ou ``npx ...``).
        input_mmd: Caminho do diagrama Mermaid de entrada.
        output_png: Caminho do PNG de saída.
        timeout: Timeout em segundos.

    Raises:
        RuntimeError: Se a renderização falhar ou o PNG não for gerado.
        subprocess.TimeoutExpired: Se exceder o timeout.
    """
    cmd = list(cli) + [
        '-i', str(input_mmd),
        '-o', str(output_png),
        '-b', 'white',
        '-w', str(_MERMAID_PNG_WIDTH),
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or '').strip()
        raise RuntimeError(
            f"Mermaid CLI falhou (codigo {completed.returncode})"
            + (f": {detail}" if detail else "")
        )
    if not output_png.is_file() or output_png.stat().st_size == 0:
        raise RuntimeError(f"PNG Mermaid nao gerado: {output_png}")


def _render_mermaid_blocks(
    md_content: str,
    work_dir: Path,
    verbose: bool = False,
    enabled: bool = True,
) -> Tuple[str, int]:
    """
    Substitui blocos `` ```mermaid `` `` por imagens PNG renderizadas localmente.

    Usa ``mmdc`` ou ``npx @mermaid-js/mermaid-cli``. Em falha parcial ou total,
    mantém o bloco original como código e emite aviso (não aborta a conversão).

    Args:
        md_content: Markdown original.
        work_dir: Diretório para arquivos ``.mmd``/``.png`` temporários.
        verbose: Se True, imprime progresso.
        enabled: Se False, retorna o conteúdo inalterado.

    Returns:
        Tupla ``(markdown_processado, quantidade_de_diagramas_renderizados)``.
    """
    if not enabled:
        return md_content, 0

    matches = list(_MERMAID_FENCE_RE.finditer(md_content))
    if not matches:
        return md_content, 0

    cli = _find_mermaid_cli()
    if cli is None:
        msg = (
            "[AVISO] Blocos Mermaid encontrados, mas mmdc/npx nao esta disponivel. "
            "Mantendo como caixa de codigo. Instale Node.js e "
            "@mermaid-js/mermaid-cli, ou use mmdc no PATH."
        )
        print(msg)
        return md_content, 0

    if verbose:
        print(f"[INFO] Mermaid CLI: {' '.join(cli)}")
        print(f"[INFO] Renderizando {len(matches)} bloco(s) Mermaid...")

    work_dir.mkdir(parents=True, exist_ok=True)
    rendered_count = 0
    parts: List[str] = []
    pos = 0

    for index, match in enumerate(matches, start=1):
        parts.append(md_content[pos:match.start()])
        diagram_src = match.group(1).strip()
        mmd_path = work_dir / f"mermaid-{index}.mmd"
        png_path = work_dir / f"mermaid-{index}.png"
        rel_png = f"{work_dir.name}/mermaid-{index}.png".replace('\\', '/')

        try:
            mmd_path.write_text(diagram_src + '\n', encoding='utf-8')
            _run_mmdc(cli, mmd_path, png_path)
            parts.append(f'\n![Diagrama Mermaid {index}]({rel_png})\n')
            rendered_count += 1
            if verbose:
                print(f"[INFO] Mermaid {index}/{len(matches)} renderizado: {rel_png}")
        except subprocess.TimeoutExpired:
            print(
                f"[AVISO] Timeout ao renderizar Mermaid #{index}; "
                "mantendo bloco como codigo."
            )
            parts.append(match.group(0))
        except Exception as exc:
            print(
                f"[AVISO] Falha ao renderizar Mermaid #{index}: {exc}. "
                "Mantendo bloco como codigo."
            )
            parts.append(match.group(0))

        pos = match.end()

    parts.append(md_content[pos:])
    return ''.join(parts), rendered_count


def _cleanup_mermaid_workdir(work_dir: Optional[Path]) -> None:
    """Remove o diretório temporário de diagramas Mermaid, se existir."""
    if work_dir is None:
        return
    try:
        if work_dir.is_dir():
            shutil.rmtree(work_dir, ignore_errors=True)
    except Exception:
        pass


def _xhtml2pdf_link_callback(base_url: str):
    """
    Resolve URIs de imagens locais para caminhos absolutos no xhtml2pdf.

    Args:
        base_url: Diretório base (pasta do ``.md``).

    Returns:
        Callback compatível com ``pisa.CreatePDF(link_callback=...)``.
    """
    base = Path(base_url)

    def link_callback(uri: str, rel: Optional[str] = None) -> str:
        if not uri:
            return uri
        lower = uri.lower()
        if lower.startswith(('http://', 'https://', 'data:')):
            return uri

        path_str = uri
        if lower.startswith('file:///'):
            path_str = uri[8:]
            if platform.system() == 'Windows' and path_str.startswith('/'):
                path_str = path_str.lstrip('/')
        elif lower.startswith('file://'):
            path_str = uri[7:]

        path = Path(path_str)
        if not path.is_absolute():
            path = base / path_str
        return str(path.resolve())

    return link_callback


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

    for old, new in _XHTML2PDF_SYMBOL_REPLACEMENTS:
        text = text.replace(old, new)

    # Caracteres invisíveis (ex.: U+200B) viram quadrados pretos no ReportLab
    for invisible in ('\u200b', '\u200c', '\u200d', '\ufeff', '\u00ad'):
        text = text.replace(invisible, '')

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


def _fix_pre_line_breaks_for_xhtml2pdf(html_content: str) -> str:
    """
    Converte quebras de linha em blocos ``<pre>`` para ``<br/>``.

    xhtml2pdf/ReportLab não respeita ``white-space: pre`` ou ``pre-wrap``;
    sem isso, blocos fenced (```) aparecem como uma única linha quebrada
    apenas por word-wrap.
    """
    import re

    def replace_pre_block(match) -> str:
        attrs = match.group(1)
        inner = match.group(2)
        inner = inner.replace('\r\n', '\n').replace('\r', '\n')
        inner = re.sub(r'\n', '<br/>\n', inner)
        return f'<pre{attrs}>{inner}</pre>'

    return re.sub(
        r'<pre([^>]*)>(.*?)</pre>',
        replace_pre_block,
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _break_cell_content_for_xhtml2pdf(text: str) -> str:
    """
    Insere ``<br/>`` em pontos seguros para o xhtml2pdf quebrar linhas em células.

    Não usa zero-width space (U+200B): o ReportLab renderiza como quadrado preto.
    """
    if not text or not text.strip():
        return text

    text = text.replace('\u200b', '').replace('\ufeff', '')

    # Zonas eleitorais: quebrar após cada " - "
    if ' - ' in text:
        text = text.replace(' - ', '<br/>- ')

    # E-mails: quebrar só após @ (a largura da coluna cuida do restante)
    if '@' in text:
        text = text.replace('@', '@<br/>')

    return text


def _fix_table_cells_for_xhtml2pdf(html_content: str) -> str:
    """
    Aplica quebras ``<br/>`` no conteúdo textual de células ``<th>``/``<td>``.

    Ignora células com HTML aninhado (links, formatação).
    """
    def replace_cell(match) -> str:
        tag = match.group(1)
        attrs = match.group(2)
        inner = match.group(3)
        if re.search(r'<[a-z]', inner, re.IGNORECASE):
            return match.group(0)
        return f'<{tag}{attrs}>{_break_cell_content_for_xhtml2pdf(inner)}</{tag}>'

    return re.sub(
        r'<(t[hd])([^>]*)>(.*?)</\1>',
        replace_cell,
        html_content,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _strip_html_to_text(cell_html: str) -> str:
    """Extrai texto plano de uma célula HTML para medição de largura."""
    plain = re.sub(r'<[^>]+>', '', cell_html)
    return html_module.unescape(plain).strip()


def _measure_cell_content_width(text: str) -> float:
    """
    Estima a largura de conteúdo de uma célula (análogo ao min-content do HTML).

    Usa o maior token da célula (palavra, e-mail, código) como base, com peso
    extra quando há várias palavras na mesma linha.
    """
    text = re.sub(r'\s+', ' ', text.strip())
    if not text:
        return 0.0

    tokens = [t for t in re.split(r'\s+', text) if t]
    if not tokens:
        return 0.0

    max_token = float(max(len(t) for t in tokens))
    if len(tokens) == 1:
        return max_token

    return max(max_token, len(text) * 0.3)


def _extract_table_matrix(table_html: str) -> List[List[str]]:
    """Extrai matriz [linha][coluna] com texto de cada célula da tabela."""
    rows: List[List[str]] = []
    for tr_match in re.finditer(
        r'<tr[^>]*>(.*?)</tr>', table_html, re.DOTALL | re.IGNORECASE
    ):
        cells: List[str] = []
        for cell_match in re.finditer(
            r'<t[hd]([^>]*)>(.*?)</t[hd]>',
            tr_match.group(1),
            re.DOTALL | re.IGNORECASE,
        ):
            cells.append(_strip_html_to_text(cell_match.group(2)))
        if cells:
            rows.append(cells)
    return rows


def _normalize_table_rows(rows: List[List[str]]) -> List[List[str]]:
    """Garante que todas as linhas tenham o mesmo número de colunas."""
    if not rows:
        return rows
    col_count = max(len(row) for row in rows)
    return [row + [''] * (col_count - len(row)) for row in rows]


def _column_content_measures(rows: List[List[str]]) -> tuple[List[float], List[str]]:
    """
    Para cada coluna, retorna a maior medida de conteúdo relevante.

    Colunas ``data_only`` (ex.: Habilitado) ignoram o título longo e usam
    apenas o conteúdo das linhas de dados (``[X]``, ``[OK]``).
    """
    rows = _normalize_table_rows(rows)
    if not rows:
        return [], []

    headers = rows[0]
    data_rows = rows[1:] if len(rows) > 1 else []
    measures: List[float] = []

    for col_idx, header in enumerate(headers):
        profile = _column_profile_for_header(header)
        if profile['data_only'] and data_rows:
            col_max = max(
                (_measure_cell_content_width(row[col_idx]) for row in data_rows),
                default=3.0,
            )
        else:
            col_max = _measure_cell_content_width(header)
            for row in data_rows:
                col_max = max(col_max, _measure_cell_content_width(row[col_idx]))
        measures.append(max(col_max, 1.0))

    return measures, headers


def _distribute_column_widths_percent(
    measures: List[float],
    headers: List[str],
) -> List[str]:
    """
    Distribui 100% entre colunas proporcionalmente às medidas de conteúdo.

    Usa pisos e tetos por tipo de coluna (nome, cargo, e-mail, habilitado…).
    """
    col_count = len(measures)
    if col_count == 0:
        return []

    if col_count == 1:
        return ['100%']

    profiles = [
        _column_profile_for_header(headers[i]) if i < len(headers) else {
            'min_pct': _COL_WIDTH_MIN_PCT,
            'max_pct': _COL_WIDTH_MAX_PCT,
            'data_only': False,
        }
        for i in range(col_count)
    ]

    weights = [max(m, 1.0) for m in measures]
    total = sum(weights)
    percents = [100.0 * w / total for w in weights]

    for idx in range(col_count):
        percents[idx] = max(percents[idx], profiles[idx]['min_pct'])

    total = sum(percents)
    percents = [p * 100.0 / total for p in percents]

    for _ in range(col_count + 2):
        excess = 0.0
        uncapped: List[int] = []
        changed = False
        for idx, pct in enumerate(percents):
            cap = profiles[idx]['max_pct']
            if pct > cap:
                excess += pct - cap
                percents[idx] = cap
                changed = True
            else:
                uncapped.append(idx)
        if excess <= 0.0 or not uncapped:
            break
        share = excess / len(uncapped)
        for idx in uncapped:
            percents[idx] += share
        if not changed:
            break

    total = sum(percents)
    percents = [p * 100.0 / total for p in percents]
    return [f'{pct:.1f}%' for pct in percents]


def _compute_table_column_widths(table_html: str) -> Optional[List[str]]:
    """
    Calcula larguras percentuais das colunas com base no conteúdo da tabela.

    Returns:
        Lista de larguras CSS ou None se a tabela não puder ser analisada.
    """
    rows = _extract_table_matrix(table_html)
    if not rows:
        return None

    measures, headers = _column_content_measures(rows)
    if not measures:
        return None

    return _distribute_column_widths_percent(measures, headers)


def _merge_html_style_attr(attrs: str, style_additions: str) -> str:
    """Acrescenta declarações CSS ao atributo ``style`` de uma tag HTML."""
    style_additions = style_additions.strip()
    if not style_additions:
        return attrs
    if not style_additions.endswith(';'):
        style_additions += ';'

    style_match = re.search(r'\bstyle="([^"]*)"', attrs, re.IGNORECASE)
    if style_match:
        existing = style_match.group(1).strip()
        if existing and not existing.endswith(';'):
            existing += ';'
        merged = f'{existing}{style_additions}'
        return re.sub(
            r'\bstyle="[^"]*"',
            f'style="{merged}"',
            attrs,
            count=1,
            flags=re.IGNORECASE,
        )
    return f'{attrs} style="{style_additions}"'


def _cell_column_inline_style(width: str, header: str, is_header: bool) -> str:
    """
    Estilo inline por coluna para o xhtml2pdf respeitar larguras.

    O ReportLab costuma ignorar ``<colgroup>``; ``width``/``max-width`` em
    ``th``/``td`` são mais confiáveis com ``table-layout: fixed``.
    """
    profile = _column_profile_for_header(header)
    parts = [f'width:{width}', f'max-width:{width}']
    if profile.get('data_only'):
        parts.append('text-align:center')
        if is_header:
            parts.append('font-size:6pt')
            parts.append('line-height:1.1')
    return ';'.join(parts) + ';'


def _apply_table_column_width_styles(table_html: str, widths: List[str]) -> str:
    """
    Aplica ``width``/``max-width`` inline em cada ``th``/``td`` da tabela.

    Células vazias na coluna Cargo recebem ``&#160;`` para evitar colapso
    da coluna quando o xhtml2pdf ignora percentuais do ``colgroup``.
    """
    matrix = _extract_table_matrix(table_html)
    if not matrix:
        return table_html

    headers = matrix[0]
    header_profiles = [
        _column_profile_for_header(headers[i]) if i < len(headers) else {}
        for i in range(len(widths))
    ]

    def patch_row(row_html: str) -> str:
        col_idx = 0

        def patch_cell(cell_match: re.Match) -> str:
            nonlocal col_idx
            if col_idx >= len(widths):
                return cell_match.group(0)

            tag = cell_match.group(1).lower()
            attrs = cell_match.group(2)
            inner = cell_match.group(3)
            header = headers[col_idx] if col_idx < len(headers) else ''
            profile = header_profiles[col_idx] if col_idx < len(header_profiles) else {}
            style = _cell_column_inline_style(
                widths[col_idx],
                header,
                is_header=(tag == 'th'),
            )
            attrs = _merge_html_style_attr(attrs, style)

            if tag == 'th' and profile.get('data_only'):
                plain = _strip_html_to_text(inner)
                if len(plain) > 5:
                    inner = 'Hab.'

            if (
                tag == 'td'
                and col_idx < len(header_profiles)
                and 'cargo' in header.lower()
                and not _strip_html_to_text(inner)
            ):
                inner = '&#160;'

            col_idx += 1
            return f'<{tag}{attrs}>{inner}</{tag}>'

        return re.sub(
            r'<(th|td)([^>]*)>(.*?)</\1>',
            patch_cell,
            row_html,
            flags=re.DOTALL | re.IGNORECASE,
        )

    def patch_table(match: re.Match) -> str:
        open_tr = match.group(1)
        row_inner = match.group(2)
        close_tr = match.group(3)
        return f'{open_tr}{patch_row(row_inner)}{close_tr}'

    return re.sub(
        r'(<tr[^>]*>)(.*?)(</tr>)',
        patch_table,
        table_html,
        flags=re.DOTALL | re.IGNORECASE,
    )


def _inject_table_colgroups_for_xhtml2pdf(html_content: str) -> str:
    """
    Injeta ``<colgroup>`` com larguras calculadas pelo conteúdo de cada coluna.

    Simula o ``table-layout: auto`` do HTML: cada coluna recebe peso
    proporcional ao seu conteúdo mais largo, com piso e teto percentuais.
    """
    def inject_colgroup(match) -> str:
        table_tag = match.group(1)
        table_body = match.group(2)
        if '<colgroup' in table_body[:400].lower():
            return match.group(0)

        widths = _compute_table_column_widths(table_body)
        if not widths:
            return match.group(0)

        colgroup = '<colgroup>' + ''.join(
            f'<col style="width:{width};" />' for width in widths
        ) + '</colgroup>'
        styled_body = _apply_table_column_width_styles(table_body, widths)
        return f'{table_tag}{colgroup}{styled_body}'

    return re.sub(
        r'(<table[^>]*>)([\s\S]*?</table>)',
        inject_colgroup,
        html_content,
        flags=re.IGNORECASE,
    )


def _prepare_html_for_xhtml2pdf(html_content: str) -> str:
    """Pós-processa HTML para compatibilidade com limitações do xhtml2pdf."""
    html_content = _fix_pre_line_breaks_for_xhtml2pdf(html_content)
    html_content = _inject_table_colgroups_for_xhtml2pdf(html_content)
    return _fix_table_cells_for_xhtml2pdf(html_content)


def _resolve_css_content(
    css_path: Optional[str],
    landscape: bool = False,
) -> str:
    """
    Resolve o CSS final para geração do PDF.

    Args:
        css_path: Caminho opcional para CSS customizado.
        landscape: Se True, força orientação paisagem na regra @page.

    Returns:
        str: Conteúdo CSS a aplicar.
    """
    if css_path:
        css_file = Path(css_path)
        if not css_file.exists():
            raise FileNotFoundError(f"Arquivo CSS nao encontrado: {css_path}")
        css_content = css_file.read_text(encoding='utf-8')
    else:
        css_content = _get_default_css(landscape=landscape)
        return css_content

    if landscape:
        css_content += """

/* Orientacao paisagem (--landscape) */
@page {
    size: A4 landscape;
    margin: 1.5cm;
}

table {
    table-layout: fixed;
    font-size: 7pt;
}

th, td {
    word-wrap: break-word;
    overflow-wrap: break-word;
    padding: 2pt;
}
"""
    return css_content


def _convert_with_xhtml2pdf(
    html_content: str,
    pdf_path: str,
    css_path: Optional[str],
    base_url: str,
    verbose: bool,
    landscape: bool = False,
) -> None:
    """
    Converte HTML para PDF usando xhtml2pdf (fallback para Windows).

    Args:
        html_content: Conteúdo HTML completo
        pdf_path: Caminho do PDF de saída
        css_path: Caminho opcional para CSS customizado
        base_url: URL base para recursos (imagens, etc.)
        verbose: Se True, exibe informações detalhadas
        landscape: Se True, gera páginas em orientação paisagem
    """
    from io import BytesIO

    css_content = _resolve_css_content(css_path, landscape=landscape)
    if css_path and verbose:
        print(f"[INFO] Usando CSS customizado: {css_path}")
    elif verbose:
        orientation = "paisagem" if landscape else "retrato"
        print(f"[INFO] Usando CSS padrao ({orientation})")

    # Inserir CSS no HTML (xhtml2pdf precisa do CSS inline ou em <style>)
    # Extrair apenas o conteúdo do body se existir
    if '<body>' in html_content and '</body>' in html_content:
        body_start = html_content.find('<body>') + 6
        body_end = html_content.find('</body>')
        body_content = html_content[body_start:body_end]
    else:
        # Se não tiver body, usar o conteúdo completo
        body_content = html_content

    body_content = _prepare_html_for_xhtml2pdf(body_content)

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
            link_callback=_xhtml2pdf_link_callback(base_url),
        )

    if pisa_status.err:
        raise RuntimeError(f"Erro ao gerar PDF com xhtml2pdf: {pisa_status.err}")


def convert_md_to_pdf(
    md_path: str,
    pdf_path: str,
    css_path: Optional[str] = None,
    verbose: bool = False,
    landscape: bool = False,
    pagebreak_on_hr: bool = False,
    render_mermaid: bool = True,
) -> dict:
    """
    Converte um arquivo Markdown para PDF.

    Args:
        md_path: Caminho do arquivo Markdown (.md)
        pdf_path: Caminho do arquivo PDF de saída (.pdf)
        css_path: Caminho opcional para arquivo CSS customizado
        verbose: Se True, exibe informações detalhadas
        landscape: Se True, gera páginas em orientação paisagem (recomendado para tabelas largas)
        pagebreak_on_hr: Se True, trata ``---`` em linha isolada como quebra de página (legado)
        render_mermaid: Se True, renderiza blocos `` ```mermaid `` `` via mmdc/npx

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

    mermaid_dir: Optional[Path] = None
    mermaid_rendered = 0

    try:
        # Ler conteúdo do markdown
        if verbose:
            print(f"[INFO] Lendo arquivo markdown: {md_path}")

        md_content = md_file.read_text(encoding='utf-8')

        mermaid_dir = md_file.parent / _MERMAID_WORKDIR_NAME
        md_content, mermaid_rendered = _render_mermaid_blocks(
            md_content,
            work_dir=mermaid_dir,
            verbose=verbose,
            enabled=render_mermaid,
        )
        if verbose and render_mermaid and mermaid_rendered:
            print(f"[INFO] Diagramas Mermaid embutidos: {mermaid_rendered}")

        md_content = _preprocess_markdown(md_content, pagebreak_on_hr=pagebreak_on_hr)

        if verbose:
            print("[INFO] Convertendo Markdown para HTML...")

        def build_full_html(md_src: str) -> str:
            body = _markdown_to_body_html(md_src)
            return _wrap_full_html(body, md_file.name)

        def build_xhtml2pdf_html(md_src: str) -> str:
            """HTML para xhtml2pdf com símbolos substituídos por equivalentes ASCII."""
            return build_full_html(_substitute_xhtml2pdf_problematic_chars(md_src))

        # Converter HTML para PDF
        if verbose:
            print("[INFO] Convertendo HTML para PDF...")

        # Resolver caminhos relativos de imagens (inclui PNGs Mermaid em .pdf-cli-mermaid/)
        base_url = str(md_file.parent.absolute())

        # Detectar plataforma para mensagens informativas
        is_windows = platform.system() == 'Windows'

        # Tentar usar WeasyPrint primeiro (melhor qualidade, suporte a Unicode/emojis)
        # Tem fallback automático para xhtml2pdf se falhar
        if WEASYPRINT_AVAILABLE:
            full_html = build_full_html(md_content)
            try:
                css_content_str = _resolve_css_content(css_path, landscape=landscape)
                if css_path:
                    if verbose:
                        print(f"[INFO] Usando CSS customizado: {css_path}")
                elif verbose:
                    orientation = "paisagem" if landscape else "retrato"
                    print(f"[INFO] Usando CSS padrao ({orientation}) com suporte a emojis")

                css_obj = CSS(string=css_content_str)

                # Ocultar ruído GTK/GLib/Fontconfig (stderr Python + nativo)
                _original_stderr_use = sys.stderr
                sys.stderr = SilentStderr(sys.stderr)
                try:
                    with _quiet_native_stderr():
                        html_doc = HTML(string=full_html, base_url=base_url)
                        html_doc.write_pdf(pdf_path, stylesheets=[css_obj])
                finally:
                    sys.stderr = _original_stderr_use

                if verbose:
                    print("[INFO] PDF gerado com motor de alta qualidade")

            except Exception as weasy_error:
                # WeasyPrint falhou, tentar fallback
                if verbose:
                    print("[AVISO] Motor primario indisponivel; usando fallback portavel...")

                # Fallback para xhtml2pdf
                if not XHTML2PDF_AVAILABLE:
                    error_msg = (
                        "Nao foi possivel gerar o PDF: falta suporte de renderizacao no sistema.\n"
                        f"Detalhe tecnico: {str(weasy_error)}\n"
                    )
                    if is_windows:
                        error_msg += (
                            "No Windows, instale o GTK3 Runtime ou use o fallback portavel "
                            "(xhtml2pdf via pip install xhtml2pdf)."
                        )
                    else:
                        error_msg += (
                            "No Linux, instale as dependencias do sistema (pango/cairo) "
                            "ou xhtml2pdf: pip install xhtml2pdf"
                        )
                    raise RuntimeError(error_msg)

                # Regenerar HTML com substituições amigáveis ao ReportLab
                full_html = build_xhtml2pdf_html(md_content)
                _convert_with_xhtml2pdf(
                    full_html, pdf_path, css_path, base_url, verbose, landscape=landscape
                )
        elif XHTML2PDF_AVAILABLE:
            # Usar xhtml2pdf diretamente (WeasyPrint não disponível)
            if verbose:
                print("[INFO] Usando motor portavel de conversao")
                print("[INFO] Alguns simbolos especiais podem ser simplificados no PDF")

            full_html = build_xhtml2pdf_html(md_content)
            _convert_with_xhtml2pdf(
                full_html, pdf_path, css_path, base_url, verbose, landscape=landscape
            )
        else:
            # Nenhuma biblioteca disponível
            error_msg = (
                "Nao foi possivel gerar o PDF: nenhum motor de conversao esta disponivel.\n"
                "Instale as dependencias do pdf-cli (requirements.txt) e, no Windows, "
                "o GTK3 Runtime para melhor qualidade tipografica."
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
            'pages': num_pages,
            'mermaid_rendered': mermaid_rendered,
        }

        # Log da operação
        logger.log_operation(
            operation_type='md-to-pdf',
            status='success',
            input_file=str(md_path),
            output_file=str(pdf_path),
            parameters={
                'css_path': css_path,
                'landscape': landscape,
                'verbose': verbose,
                'render_mermaid': render_mermaid,
                'mermaid_rendered': mermaid_rendered,
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
                'landscape': landscape,
                'verbose': verbose,
                'render_mermaid': render_mermaid,
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        return result
    finally:
        _cleanup_mermaid_workdir(mermaid_dir)
