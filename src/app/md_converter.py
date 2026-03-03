"""
Módulo MD Converter - Conversão de Markdown para PDF.

Este módulo implementa a conversão de arquivos Markdown (.md) para PDF,
usando markdown2 para MD→HTML e weasyprint/xhtml2pdf para HTML→PDF.

Suporte a Mermaid.js:
- Detecta blocos de código ```mermaid``` no Markdown
- Renderiza cada diagrama como imagem PNG usando Mermaid CLI (mmdc)
- Injeta as imagens no Markdown como data URI para preservar portabilidade
- Erra de forma explícita quando houver Mermaid no documento sem renderer disponível

Suporte a PlantUML:
- Detecta blocos de código ```plantuml``` e ```plantxml``` no Markdown
- Renderiza referências de imagem para arquivos `.plantuml`/`.puml` locais
- Converte diagramas para PNG e embute como data URI no Markdown processado
- Erra de forma explícita quando houver PlantUML sem renderer disponível

Suporta Windows e Linux com fallback automático:
- WeasyPrint (preferido, melhor qualidade, funciona no Linux com dependências do sistema)
- xhtml2pdf (fallback portável, funciona em Windows e Linux sem dependências externas)

Suporte a Emojis e Símbolos Unicode:
- Detecta automaticamente a plataforma e usa fontes de emoji apropriadas
- Windows: Segoe UI Emoji, Segoe UI Symbol
- macOS: Apple Color Emoji
- Linux: Noto Color Emoji, Noto Emoji
- Fallback para fontes padrão se fontes de emoji não estiverem disponíveis
- Suporte a caracteres box-drawing (├──, └──, │) com fontes monospace

Limitações Conhecidas:
- xhtml2pdf (fallback) tem limitações com Unicode complexo:
  * Emojis podem aparecer como quadrados pretos
  * Caracteres box-drawing podem ser renderizados incorretamente
- WeasyPrint oferece melhor suporte a Unicode quando disponível
- Recomendado usar WeasyPrint no Linux para melhor qualidade
"""

import base64
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
from typing import List, Optional, Tuple
import markdown2
import platform
from app.logging import get_logger
from core.exceptions import (
    MermaidRendererNotAvailableError,
    MermaidRenderingError,
    PlantUMLRendererNotAvailableError,
    PlantUMLRenderingError,
)

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


_MERMAID_BLOCK_PATTERN = re.compile(
    r"^[ \t]*```[ \t]*mermaid[^\n]*\n(?P<code>.*?)(?:\n^[ \t]*```[ \t]*$)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

_PLANTUML_BLOCK_PATTERN = re.compile(
    r"^[ \t]*```[ \t]*(?:plantuml|plantxml|puml|uml)[^\n]*\n(?P<code>.*?)(?:\n^[ \t]*```[ \t]*$)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL
)

_MARKDOWN_IMAGE_PATTERN = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<target>[^)]+)\)")

_PLANTUML_FILE_EXTENSIONS = {".plantuml", ".puml", ".pu", ".iuml"}


def _resolve_mermaid_renderer_command() -> List[str]:
    """
    Resolve o comando externo para renderizar diagramas Mermaid.

    Ordem de prioridade:
    1. Variável de ambiente `PDF_CLI_MERMAID_COMMAND` (comando completo)
    2. Binário `mmdc` disponível no PATH
    3. Fallback via `npx -y @mermaid-js/mermaid-cli`

    Returns:
        List[str]: Comando tokenizado para uso com subprocess.run

    Raises:
        MermaidRendererNotAvailableError: Se nenhum renderer estiver disponível
    """
    custom_command = os.getenv("PDF_CLI_MERMAID_COMMAND", "").strip()
    if custom_command:
        parsed_command = shlex.split(custom_command)
        if parsed_command:
            return parsed_command

    mmdc_path = shutil.which("mmdc")
    if mmdc_path:
        return [mmdc_path]

    npx_path = shutil.which("npx")
    if npx_path:
        return [npx_path, "-y", "@mermaid-js/mermaid-cli"]

    raise MermaidRendererNotAvailableError()


def _render_mermaid_diagram_to_data_uri(
    mermaid_code: str,
    diagram_index: int,
    working_dir: Path,
    mermaid_command: List[str],
    mermaid_theme: str,
) -> str:
    """
    Renderiza um diagrama Mermaid para PNG e retorna data URI.

    Args:
        mermaid_code: Código Mermaid (sem fences)
        diagram_index: Índice do diagrama no documento (1-based)
        working_dir: Diretório temporário para arquivos intermediários
        mermaid_command: Comando do renderer Mermaid
        mermaid_theme: Tema do Mermaid (default, dark, forest, neutral)

    Returns:
        str: Data URI no formato data:image/png;base64,...

    Raises:
        MermaidRenderingError: Se o renderer falhar ou não gerar arquivo de saída
    """
    input_file = working_dir / f"mermaid_diagram_{diagram_index}.mmd"
    output_file = working_dir / f"mermaid_diagram_{diagram_index}.png"

    input_file.write_text(mermaid_code, encoding="utf-8")

    command = [
        *mermaid_command,
        "-i", str(input_file),
        "-o", str(output_file),
        "-t", mermaid_theme,
    ]

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        error_detail = (completed.stderr or completed.stdout or "").strip()
        if not error_detail:
            error_detail = "sem detalhes adicionais do renderer."
        raise MermaidRenderingError(
            f"Falha ao renderizar diagrama Mermaid #{diagram_index}: {error_detail}"
        )

    if not output_file.exists():
        raise MermaidRenderingError(
            f"O renderer Mermaid nao gerou o arquivo esperado para o diagrama #{diagram_index}."
        )

    image_bytes = output_file.read_bytes()
    if not image_bytes:
        raise MermaidRenderingError(
            f"O renderer Mermaid gerou arquivo vazio para o diagrama #{diagram_index}."
        )

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def _render_mermaid_blocks_in_markdown(
    md_content: str,
    verbose: bool = False,
    mermaid_theme: str = "default",
) -> Tuple[str, int]:
    """
    Converte todos os blocos ```mermaid``` em imagens embutidas no Markdown.

    Args:
        md_content: Conteúdo Markdown original
        verbose: Se True, imprime logs de progresso
        mermaid_theme: Tema aplicado na renderização Mermaid

    Returns:
        Tuple[str, int]:
            - Markdown transformado (blocos Mermaid substituídos por imagens)
            - Quantidade de blocos Mermaid renderizados

    Raises:
        MermaidRendererNotAvailableError: Quando há Mermaid sem renderer instalado
        MermaidRenderingError: Se qualquer diagrama falhar na renderização
    """
    matches = list(_MERMAID_BLOCK_PATTERN.finditer(md_content))
    if not matches:
        return md_content, 0

    mermaid_command = _resolve_mermaid_renderer_command()
    if verbose:
        print(f"[INFO] Renderer Mermaid detectado: {' '.join(mermaid_command)}")
        print(f"[INFO] Blocos Mermaid encontrados: {len(matches)}")

    transformed_parts: List[str] = []
    last_end = 0

    with tempfile.TemporaryDirectory(prefix="pdf_cli_mermaid_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        for index, match in enumerate(matches, start=1):
            transformed_parts.append(md_content[last_end:match.start()])
            mermaid_code = match.group("code").strip()

            if not mermaid_code:
                raise MermaidRenderingError(
                    f"Bloco Mermaid #{index} esta vazio. Verifique o Markdown de entrada."
                )

            if verbose:
                print(f"[INFO] Renderizando diagrama Mermaid #{index}...")

            image_data_uri = _render_mermaid_diagram_to_data_uri(
                mermaid_code=mermaid_code,
                diagram_index=index,
                working_dir=temp_dir,
                mermaid_command=mermaid_command,
                mermaid_theme=mermaid_theme,
            )
            transformed_parts.append(f"\n![Diagrama Mermaid {index}]({image_data_uri})\n")
            last_end = match.end()

    transformed_parts.append(md_content[last_end:])
    return "".join(transformed_parts), len(matches)


def _resolve_plantuml_renderer_command() -> List[str]:
    """
    Resolve o comando externo para renderizar diagramas PlantUML.

    Ordem de prioridade:
    1. Variável de ambiente `PDF_CLI_PLANTUML_COMMAND` (comando completo)
    2. Binário `plantuml` disponível no PATH

    Returns:
        List[str]: Comando tokenizado para uso com subprocess.run

    Raises:
        PlantUMLRendererNotAvailableError: Se nenhum renderer estiver disponível
    """
    custom_command = os.getenv("PDF_CLI_PLANTUML_COMMAND", "").strip()
    if custom_command:
        parsed_command = shlex.split(custom_command)
        if parsed_command:
            return parsed_command

    plantuml_path = shutil.which("plantuml")
    if plantuml_path:
        return [plantuml_path]

    raise PlantUMLRendererNotAvailableError()


def _extract_markdown_target_path(markdown_target: str) -> str:
    """
    Extrai o caminho principal de um alvo Markdown de imagem/link.

    Exemplos de alvos:
    - `diagram.puml`
    - `diagram.puml "Titulo"`
    - `<diagram.puml>`

    Args:
        markdown_target: Conteúdo interno de `( ... )` no Markdown

    Returns:
        str: Caminho extraído (pode ser relativo, absoluto ou URL)
    """
    normalized_target = markdown_target.strip()
    if not normalized_target:
        return ""

    if normalized_target.startswith("<") and normalized_target.endswith(">"):
        return normalized_target[1:-1].strip()

    try:
        tokens = shlex.split(normalized_target)
    except ValueError:
        tokens = normalized_target.split()

    if not tokens:
        return ""
    return tokens[0].strip()


def _is_url_or_data_uri(target_path: str) -> bool:
    """
    Verifica se um alvo representa URL remota ou data URI.

    Args:
        target_path: Caminho/URL a ser validado

    Returns:
        bool: True para URL remota ou data URI
    """
    lowered = target_path.lower()
    return "://" in lowered or lowered.startswith("data:")


def _ensure_plantuml_wrapped_source(source_code: str, plantuml_theme: Optional[str]) -> str:
    """
    Garante que o código PlantUML tenha delimitadores e tema consistentes.

    Regras aplicadas:
    - Adiciona `@startuml` e `@enduml` se o usuário não incluiu
    - Injeta `!theme <tema>` após `@startuml` quando tema foi informado
      e ainda não existe diretiva de tema no código

    Args:
        source_code: Código PlantUML bruto
        plantuml_theme: Tema opcional para o diagrama

    Returns:
        str: Código pronto para renderização no PlantUML

    Raises:
        PlantUMLRenderingError: Se o código estiver vazio
    """
    normalized = source_code.strip()
    if not normalized:
        raise PlantUMLRenderingError("Diagrama PlantUML vazio no Markdown de entrada.")

    lowered = normalized.lower()
    if "@startuml" not in lowered:
        normalized = f"@startuml\n{normalized}\n@enduml"

    lines = normalized.splitlines()
    if plantuml_theme and plantuml_theme.strip():
        theme_line_exists = any(line.strip().lower().startswith("!theme") for line in lines)
        if not theme_line_exists:
            start_index = 0
            for index, line in enumerate(lines):
                if line.strip().lower().startswith("@startuml"):
                    start_index = index
                    break
            lines.insert(start_index + 1, f"!theme {plantuml_theme.strip()}")

    wrapped = "\n".join(lines).strip()
    if not wrapped.endswith("\n"):
        wrapped += "\n"
    return wrapped


def _render_plantuml_source_to_data_uri(
    source_code: str,
    diagram_index: int,
    working_dir: Path,
    plantuml_command: List[str],
    plantuml_theme: Optional[str],
) -> str:
    """
    Renderiza um diagrama PlantUML para PNG e retorna data URI.

    Args:
        source_code: Código PlantUML do diagrama
        diagram_index: Índice sequencial do diagrama no documento (1-based)
        working_dir: Diretório temporário para arquivos intermediários
        plantuml_command: Comando do renderer PlantUML
        plantuml_theme: Tema opcional aplicado ao diagrama

    Returns:
        str: Data URI no formato data:image/png;base64,...

    Raises:
        PlantUMLRenderingError: Se houver falha no processo de renderização
    """
    input_file = working_dir / f"plantuml_diagram_{diagram_index}.puml"
    output_file = input_file.with_suffix(".png")

    prepared_source = _ensure_plantuml_wrapped_source(source_code, plantuml_theme)
    input_file.write_text(prepared_source, encoding="utf-8")

    command = [
        *plantuml_command,
        "-charset", "UTF-8",
        "-tpng",
        str(input_file),
    ]

    completed = subprocess.run(command, capture_output=True, check=False)
    if completed.returncode != 0:
        error_bytes = completed.stderr or completed.stdout or b""
        error_detail = error_bytes.decode("utf-8", errors="replace").strip()
        if not error_detail:
            error_detail = "sem detalhes adicionais do renderer."
        raise PlantUMLRenderingError(
            f"Falha ao renderizar diagrama PlantUML #{diagram_index}: {error_detail}"
        )

    image_bytes: Optional[bytes] = None
    if output_file.exists():
        image_bytes = output_file.read_bytes()
    elif completed.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        # Compatibilidade com comandos customizados que usem modo pipe
        image_bytes = completed.stdout

    if not image_bytes:
        raise PlantUMLRenderingError(
            f"O renderer PlantUML nao gerou PNG valido para o diagrama #{diagram_index}."
        )

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded_image}"


def _render_plantuml_file_references(
    md_content: str,
    md_base_dir: Path,
    working_dir: Path,
    plantuml_command: List[str],
    plantuml_theme: Optional[str],
    verbose: bool = False,
    initial_index: int = 0,
) -> Tuple[str, int]:
    """
    Renderiza referências Markdown de imagem para arquivos `.plantuml`/`.puml`.

    Args:
        md_content: Markdown atual
        md_base_dir: Diretório base do markdown de entrada (para resolver relativos)
        working_dir: Diretório temporário para PNGs intermediários
        plantuml_command: Comando do renderer PlantUML
        plantuml_theme: Tema opcional aplicado aos diagramas
        verbose: Se True, exibe logs de progresso
        initial_index: Índice inicial para numeração de diagramas

    Returns:
        Tuple[str, int]:
            - Markdown com referências `.plantuml` convertidas em data URI
            - Quantidade de referências renderizadas

    Raises:
        PlantUMLRenderingError: Se arquivo `.plantuml` não existir ou renderização falhar
    """
    rendered_count = 0
    current_index = initial_index

    def replace_image_reference(match: re.Match) -> str:
        nonlocal rendered_count, current_index

        target = match.group("target")
        alt_text = match.group("alt") or "Diagrama PlantUML"
        source_path = _extract_markdown_target_path(target)
        if not source_path:
            return match.group(0)

        suffix = Path(source_path).suffix.lower()
        if suffix not in _PLANTUML_FILE_EXTENSIONS:
            return match.group(0)

        if _is_url_or_data_uri(source_path):
            # Mantém comportamento atual para links remotos/data URI.
            return match.group(0)

        source_file = Path(source_path)
        if not source_file.is_absolute():
            source_file = (md_base_dir / source_file).resolve()

        if not source_file.exists():
            raise PlantUMLRenderingError(
                f"Arquivo PlantUML referenciado nao encontrado: {source_file}"
            )

        try:
            source_code = source_file.read_text(encoding="utf-8")
        except Exception as exc:
            raise PlantUMLRenderingError(
                f"Nao foi possivel ler arquivo PlantUML '{source_file}': {str(exc)}"
            ) from exc

        current_index += 1
        rendered_count += 1
        if verbose:
            print(f"[INFO] Renderizando arquivo PlantUML #{current_index}: {source_file}")

        image_data_uri = _render_plantuml_source_to_data_uri(
            source_code=source_code,
            diagram_index=current_index,
            working_dir=working_dir,
            plantuml_command=plantuml_command,
            plantuml_theme=plantuml_theme,
        )
        return f"![{alt_text}]({image_data_uri})"

    rendered_markdown = _MARKDOWN_IMAGE_PATTERN.sub(replace_image_reference, md_content)
    return rendered_markdown, rendered_count


def _render_plantuml_blocks_in_markdown(
    md_content: str,
    md_base_dir: Path,
    verbose: bool = False,
    plantuml_theme: Optional[str] = None,
) -> Tuple[str, int]:
    """
    Renderiza PlantUML no Markdown (blocos fenced e referências a arquivos).

    Suportes:
    - Blocos ```plantuml```, ```plantxml```, ```puml``` e ```uml```
    - Referências de imagem para arquivos locais `.plantuml`, `.puml`, `.pu`, `.iuml`

    Args:
        md_content: Conteúdo markdown original
        md_base_dir: Diretório do markdown de entrada
        verbose: Se True, imprime logs de progresso
        plantuml_theme: Tema opcional a ser aplicado nos diagramas

    Returns:
        Tuple[str, int]:
            - Markdown transformado com diagramas em data URI
            - Quantidade total de diagramas PlantUML renderizados

    Raises:
        PlantUMLRendererNotAvailableError: Se houver PlantUML sem renderer disponível
        PlantUMLRenderingError: Se qualquer diagrama falhar na renderização
    """
    block_matches = list(_PLANTUML_BLOCK_PATTERN.finditer(md_content))
    image_matches = list(_MARKDOWN_IMAGE_PATTERN.finditer(md_content))

    has_plantuml_file_reference = False
    for image_match in image_matches:
        target_path = _extract_markdown_target_path(image_match.group("target"))
        if (
            Path(target_path).suffix.lower() in _PLANTUML_FILE_EXTENSIONS
            and not _is_url_or_data_uri(target_path)
        ):
            has_plantuml_file_reference = True
            break

    if not block_matches and not has_plantuml_file_reference:
        return md_content, 0

    plantuml_command = _resolve_plantuml_renderer_command()
    if verbose:
        print(f"[INFO] Renderer PlantUML detectado: {' '.join(plantuml_command)}")
        print(f"[INFO] Blocos PlantUML encontrados: {len(block_matches)}")
        if has_plantuml_file_reference:
            print("[INFO] Referencias para arquivos .plantuml detectadas no Markdown.")

    rendered_blocks = 0
    transformed_content = md_content

    with tempfile.TemporaryDirectory(prefix="pdf_cli_plantuml_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)

        if block_matches:
            transformed_parts: List[str] = []
            last_end = 0
            for index, match in enumerate(block_matches, start=1):
                transformed_parts.append(md_content[last_end:match.start()])
                plantuml_code = match.group("code").strip()

                if verbose:
                    print(f"[INFO] Renderizando diagrama PlantUML #{index}...")

                image_data_uri = _render_plantuml_source_to_data_uri(
                    source_code=plantuml_code,
                    diagram_index=index,
                    working_dir=temp_dir,
                    plantuml_command=plantuml_command,
                    plantuml_theme=plantuml_theme,
                )
                transformed_parts.append(f"\n![Diagrama PlantUML {index}]({image_data_uri})\n")
                last_end = match.end()

            transformed_parts.append(md_content[last_end:])
            transformed_content = "".join(transformed_parts)
            rendered_blocks = len(block_matches)

        transformed_content, rendered_file_refs = _render_plantuml_file_references(
            md_content=transformed_content,
            md_base_dir=md_base_dir,
            working_dir=temp_dir,
            plantuml_command=plantuml_command,
            plantuml_theme=plantuml_theme,
            verbose=verbose,
            initial_index=rendered_blocks,
        )

    return transformed_content, rendered_blocks + rendered_file_refs


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
        # Fontes monospace com suporte a box-drawing no Windows
        monospace_fonts = '"Consolas", "Courier New", "Lucida Console", monospace'
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
    white-space: pre;
    font-size: 9pt;
    line-height: 1.4;
    overflow-x: auto;
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
    overflow-x: auto;
    font-family: {monospace_fonts};
    font-size: 9pt;
    line-height: 1.4;
    /* Preservar formatação e caracteres especiais */
    white-space: pre;
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
}}

table {{
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
}}

th, td {{
    border: 1px solid #ddd;
    padding: 0.5em;
    text-align: left;
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
    verbose: bool = False,
    plantuml_theme: Optional[str] = None,
    enable_plantuml: bool = True,
    mermaid_theme: str = "default",
    enable_mermaid: bool = True,
) -> dict:
    """
    Converte um arquivo Markdown para PDF.

    Args:
        md_path: Caminho do arquivo Markdown (.md)
        pdf_path: Caminho do arquivo PDF de saída (.pdf)
        css_path: Caminho opcional para arquivo CSS customizado
        verbose: Se True, exibe informações detalhadas
        plantuml_theme: Tema opcional para diagramas PlantUML
        enable_plantuml: Se True, renderiza blocos PlantUML e arquivos .plantuml
        mermaid_theme: Tema Mermaid para blocos ```mermaid``` (default, dark, forest, neutral)
        enable_mermaid: Se True, renderiza blocos Mermaid como imagens

    Returns:
        dict: Dicionário com informações sobre a conversão:
            - status: "success" ou "error"
            - input_file: Caminho do arquivo de entrada
            - output_file: Caminho do arquivo de saída
            - pages: Número de páginas geradas (se sucesso)
            - plantuml_diagrams: Quantidade de diagramas PlantUML renderizados
            - mermaid_diagrams: Quantidade de diagramas Mermaid renderizados
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

        # Pré-processar PlantUML antes da conversão Markdown -> HTML
        plantuml_diagrams = 0
        if enable_plantuml:
            md_content, plantuml_diagrams = _render_plantuml_blocks_in_markdown(
                md_content=md_content,
                md_base_dir=md_file.parent,
                verbose=verbose,
                plantuml_theme=plantuml_theme,
            )
            if verbose and plantuml_diagrams > 0:
                print(f"[INFO] Diagramas PlantUML renderizados: {plantuml_diagrams}")
        elif verbose:
            print("[INFO] Renderizacao PlantUML desabilitada via parametro.")

        # Pré-processar Mermaid antes da conversão Markdown -> HTML
        mermaid_diagrams = 0
        if enable_mermaid:
            md_content, mermaid_diagrams = _render_mermaid_blocks_in_markdown(
                md_content=md_content,
                verbose=verbose,
                mermaid_theme=mermaid_theme,
            )
            if verbose and mermaid_diagrams > 0:
                print(f"[INFO] Diagramas Mermaid renderizados: {mermaid_diagrams}")
        elif verbose:
            print("[INFO] Renderizacao Mermaid desabilitada via parametro.")

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

        # Processar HTML para preservar estruturas de diretórios e caracteres especiais
        html_content = _process_html_for_special_chars(html_content)

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
                        print("[INFO] Usando CSS padrao (WeasyPrint) com suporte a emojis")

                    css_obj = CSS(string=_get_default_css())

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
            'pages': num_pages,
            'plantuml_diagrams': plantuml_diagrams,
            'mermaid_diagrams': mermaid_diagrams,
        }

        # Log da operação
        logger.log_operation(
            operation_type='md-to-pdf',
            status='success',
            input_file=str(md_path),
            output_file=str(pdf_path),
            parameters={
                'css_path': css_path,
                'verbose': verbose,
                'plantuml_theme': plantuml_theme,
                'enable_plantuml': enable_plantuml,
                'mermaid_theme': mermaid_theme,
                'enable_mermaid': enable_mermaid,
            },
            result={
                'pages': num_pages,
                'plantuml_diagrams': plantuml_diagrams,
                'mermaid_diagrams': mermaid_diagrams,
            },
            notes=(
                "Conversao de Markdown para PDF concluida com sucesso. "
                f"Paginas: {num_pages or 'N/A'}. "
                f"Diagramas PlantUML: {plantuml_diagrams}. "
                f"Diagramas Mermaid: {mermaid_diagrams}."
            )
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
                'verbose': verbose,
                'plantuml_theme': plantuml_theme,
                'enable_plantuml': enable_plantuml,
                'mermaid_theme': mermaid_theme,
                'enable_mermaid': enable_mermaid,
            },
            result={
                'error': str(e)
            },
            notes=error_msg
        )

        raise
