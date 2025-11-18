#!/usr/bin/env python3
"""
PDF-cli - Ferramenta CLI para automação de edição de arquivos PDF.

Entrypoint principal e roteador de comandos da aplicação. Este módulo
define a interface de linha de comando usando Typer, incluindo todos
os subcomandos e suas opções.

Para executar:
    python pdf_cli.py --help
    python pdf_cli.py extract --help

TODO (Fase 1):
    - Implementar subcomandos básicos com help
    - Adicionar mensagem de boas-vindas
    - Configurar logging básico

TODO (Fase 2):
    - Implementar subcomando 'extract' (exportar textos para JSON)
    - Implementar subcomando 'replace' (substituir textos)

TODO (Fase 3):
    - Implementar subcomando 'merge' (unir PDFs)
    - Implementar subcomando 'delete-pages' (excluir páginas)

TODO (Fase 4):
    - Adicionar opções de verbose/logging
    - Adicionar confirmação para operações destrutivas
    - Melhorar mensagens de erro e feedback
"""

import sys
from pathlib import Path
from typing import Optional, List
import typer
from rich.console import Console
from rich.text import Text

# Adiciona o diretório src ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

# Imports dos módulos do projeto
try:
    from app import services
    from core.exceptions import PDFCliException
except ImportError:
    # Fallback para imports relativos se necessário
    import app.services as services
    from core.exceptions import PDFCliException

# Inicialização do Typer e Rich
app = typer.Typer(
    name="pdf-cli",
    help="Ferramenta CLI para automação de edição de arquivos PDF",
    add_completion=False,
)
console = Console()


def print_welcome() -> None:
    """Exibe mensagem de boas-vindas."""
    welcome_text = Text()
    welcome_text.append("PDF-cli", style="bold cyan")
    welcome_text.append(" - Ferramenta CLI para edição de arquivos PDF\n", style="dim")
    console.print(welcome_text)
    console.print("Use [bold]--help[/bold] após qualquer comando para mais informações.\n")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Exibe a versão"),
) -> None:
    """
    PDF-cli - Ferramenta CLI para automação de edição de arquivos PDF.

    Comandos disponíveis:
        extract       - Extrai textos do PDF para JSON
        replace       - Substitui textos no PDF
        merge         - Une múltiplos PDFs em um
        delete-pages  - Exclui páginas específicas
    """
    if version:
        console.print("[bold cyan]PDF-cli[/bold cyan] versão 0.1.0 (Fase 1)")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_welcome()
        console.print(ctx.get_help())
        console.print("\n[dim]Para começar, use:[/dim] [bold]pdf-cli extract --help[/bold]")


@app.command("extract")
def extract_texts(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho de saída para o JSON"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Extrai todos os objetos de texto de um PDF e exporta para JSON.

    Este comando extrai textos do PDF incluindo suas posições, fontes,
    tamanhos e outros metadados, salvando tudo em um arquivo JSON legível
    e reversível.

    Exemplo:
        pdf-cli extract documento.pdf
        pdf-cli extract documento.pdf -o textos.json
    """
    # TODO (Fase 2): Implementar lógica de extração
    console.print(f"[yellow]⚠️  Comando 'extract' será implementado na Fase 2[/yellow]")
    console.print(f"   PDF: {pdf_path}")
    if output:
        console.print(f"   Saída: {output}")


@app.command("replace")
def replace_texts(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    json_file: str = typer.Option(..., "--json", "-j", help="Arquivo JSON com as substituições"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho de saída do PDF modificado"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve o arquivo original sem confirmação"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Substitui textos no PDF baseado em um arquivo JSON de substituições.

    Realiza substituições de texto mantendo formatação e posição visual.
    O arquivo JSON deve conter uma lista de objetos com 'id' ou 'text'
    e 'new_text'.

    Exemplo:
        pdf-cli replace documento.pdf -j substituicoes.json
        pdf-cli replace documento.pdf -j substituicoes.json -o resultado.pdf
    """
    # TODO (Fase 2): Implementar lógica de substituição
    console.print(f"[yellow]⚠️  Comando 'replace' será implementado na Fase 2[/yellow]")
    console.print(f"   PDF: {pdf_path}")
    console.print(f"   JSON: {json_file}")
    if output:
        console.print(f"   Saída: {output}")


@app.command("merge")
def merge_pdfs(
    pdf_paths: List[str] = typer.Argument(..., help="Caminhos dos PDFs a serem unidos"),
    output: str = typer.Option("merged.pdf", "--output", "-o", help="Caminho de saída do PDF unido"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Une múltiplos arquivos PDF em um único documento.

    Combina vários PDFs na ordem especificada. Todos os arquivos devem
    existir e ser PDFs válidos.

    Exemplo:
        pdf-cli merge doc1.pdf doc2.pdf doc3.pdf -o resultado.pdf
    """
    # TODO (Fase 3): Implementar lógica de merge
    console.print(f"[yellow]⚠️  Comando 'merge' será implementado na Fase 3[/yellow]")
    console.print(f"   PDFs: {', '.join(pdf_paths)}")
    console.print(f"   Saída: {output}")


@app.command("delete-pages")
def delete_pages(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    pages: str = typer.Option(..., "--pages", "-p", help="Páginas a excluir (ex: 1,3,5 ou 1-5)"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho de saída do PDF modificado"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve o arquivo original sem confirmação"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Exclui páginas específicas de um PDF.

    Remove páginas do PDF. Pode ser especificado por números individuais
    (separados por vírgula) ou intervalos (ex: 1-5).

    Exemplo:
        pdf-cli delete-pages documento.pdf -p 1,3,5
        pdf-cli delete-pages documento.pdf -p 1-5
    """
    # TODO (Fase 3): Implementar lógica de exclusão de páginas
    console.print(f"[yellow]⚠️  Comando 'delete-pages' será implementado na Fase 3[/yellow]")
    console.print(f"   PDF: {pdf_path}")
    console.print(f"   Páginas: {pages}")
    if output:
        console.print(f"   Saída: {output}")


def handle_exceptions(func):
    """Decorator para tratamento centralizado de exceções."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except PDFCliException as e:
            console.print(f"[bold red]Erro:[/bold red] {str(e)}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
            if "--verbose" in sys.argv:
                import traceback
                console.print(traceback.format_exc())
            raise typer.Exit(1)
    return wrapper


if __name__ == "__main__":
    app()
