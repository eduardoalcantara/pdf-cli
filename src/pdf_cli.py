#!/usr/bin/env python3
"""
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
    help="",
    add_completion=False,
)
console = Console()


def print_banner() -> None:
    """
    Exibe o banner ASCII artístico do PDF-cli.

    Banner conforme ESPECIFICACOES-FASE-2-EXTRACAO-EDICAO-TEXTO.md
    Este banner deve ser exibido obrigatoriamente ao executar o programa sem parâmetros.
    """
    banner = """┏━┓╺┳┓┏━╸  ┏━╸╻  ╻
┣━┛ ┃┃┣╸╺━╸┃  ┃  ┃
╹  ╺┻┛╹    ┗━╸┗━╸╹
2025 ⓒ Eduardo Alcantara
Made With Perplexity & Cursor
Ferramenta CLI para automação de edição de arquivos PDF"""
    console.print(banner, style="bold cyan")
    console.print("\n[dim]For help on individual commands:[/dim] [bold]pdf.exe <command> --help[/bold]")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-v", help="Exibe a versão"),
) -> None:
    """
    Comandos disponíveis:
        export-objects     - Extrai objetos do PDF para JSON
        edit-text          - Edita objeto de texto
        edit-table         - Edita tabela
        replace-image      - Substitui imagem
        insert-object      - Insere novo objeto
        restore-from-json  - Restaura PDF via JSON
        edit-metadata      - Edita metadados
        merge              - Une múltiplos PDFs
        delete-pages       - Exclui páginas
        split              - Divide PDF em múltiplos arquivos
    """
    if version:
        console.print("[bold cyan]PDF-cli[/bold cyan] versão 0.3.0 (Fase 3)")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Banner obrigatório conforme Fase 2
        print_banner()
        console.print(ctx.get_help())


@app.command("export-objects")
def export_objects(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output: str = typer.Argument(..., help="Caminho de saída para o JSON"),
    types: Optional[str] = typer.Option(None, "--types", "-t", help="Tipos de objetos a exportar (ex: text,image,table)"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Extrai e exporta objetos do PDF para JSON.

    Permite especificar quais tipos de objetos exportar via parâmetro --types.
    Tipos disponíveis: text, image, table, link, formfield, graphic, layer, annotation, filter.

    Exemplo:
        pdf-cli export-objects documento.pdf objetos.json
        pdf-cli export-objects documento.pdf objetos.json --types text,image
        pdf-cli export-objects documento.pdf objetos.json --types table
    """
    try:
        type_list = types.split(",") if types else None

        stats = services.export_objects(pdf_path, output, type_list)

        console.print(f"[green]✓[/green] Objetos exportados com sucesso!")
        console.print(f"   Arquivo: {output}")
        console.print(f"   Total de objetos: {stats['total_objects']}")

        if verbose:
            console.print(f"\n   Por tipo:")
            for obj_type, count in stats['by_type'].items():
                if count > 0:
                    console.print(f"     {obj_type}: {count}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("edit-text")
def edit_text(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    id: Optional[str] = typer.Option(None, "--id", help="ID único do objeto de texto"),
    content: Optional[str] = typer.Option(None, "--content", help="Conteúdo do texto a buscar (se --id não fornecido)"),
    new_content: str = typer.Option(..., "--new-content", help="Novo conteúdo do texto"),
    align: Optional[str] = typer.Option(None, "--align", help="Alinhamento (left, center, right, justify)"),
    pad: bool = typer.Option(False, "--pad", help="Aplica padding para manter largura visual"),
    x: Optional[float] = typer.Option(None, "--x", help="Nova posição X"),
    y: Optional[float] = typer.Option(None, "--y", help="Nova posição Y"),
    font_name: Optional[str] = typer.Option(None, "--font-name", help="Nome da fonte"),
    font_size: Optional[int] = typer.Option(None, "--font-size", help="Tamanho da fonte"),
    color: Optional[str] = typer.Option(None, "--color", help="Cor do texto (hex)"),
    rotation: Optional[float] = typer.Option(None, "--rotation", help="Rotação em graus"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Edita um objeto de texto no PDF.

    Permite alteração via ID único ou busca por conteúdo.
    Ajusta alinhamento, padding, posição, fonte, cor e rotação conforme especificado.

    Exemplo:
        pdf-cli edit-text input.pdf output.pdf --id abc123 --new-content "Novo texto"
        pdf-cli edit-text input.pdf output.pdf --content "Texto antigo" --new-content "Novo" --align center --pad
    """
    try:
        result_path = services.edit_text(
            pdf_path=pdf_path,
            output_path=output,
            object_id=id,
            search_content=content,
            new_content=new_content,
            align=align,
            pad=pad,
            x=x,
            y=y,
            font_name=font_name,
            font_size=font_size,
            color=color,
            rotation=rotation,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Texto editado com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("edit-table")
def edit_table(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    id: str = typer.Option(..., "--id", help="ID único da tabela"),
    row: Optional[int] = typer.Option(None, "--row", help="Índice da linha (0-indexed)"),
    col: Optional[int] = typer.Option(None, "--col", help="Índice da coluna (0-indexed)"),
    value: Optional[str] = typer.Option(None, "--value", help="Novo valor da célula"),
    header: Optional[str] = typer.Option(None, "--header", help="Novo cabeçalho (se --row não fornecido)"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Edita uma célula de tabela no PDF.

    Permite editar células específicas via linha/coluna.
    Permite alterar headers, fontes de coluna, cor da célula.

    Exemplo:
        pdf-cli edit-table input.pdf output.pdf --id tbl-123 --row 2 --col 3 --value "Novo valor"
        pdf-cli edit-table input.pdf output.pdf --id tbl-123 --header "Novo Header"
    """
    try:
        result_path = services.edit_table(
            pdf_path=pdf_path,
            output_path=output,
            table_id=id,
            row=row,
            col=col,
            value=value,
            header=header,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Tabela editada com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("replace-image")
def replace_image(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    id: str = typer.Option(..., "--id", help="ID único da imagem"),
    src: str = typer.Option(..., "--src", help="Caminho da nova imagem"),
    filter_type: Optional[str] = typer.Option(None, "--filter", help="Tipo de filtro (grayscale, blur, invert)"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Substitui uma imagem no PDF.

    Troca imagem mantendo posição e dimensões.
    Permite aplicar filtro (ex: grayscale, invert).

    Exemplo:
        pdf-cli replace-image input.pdf output.pdf --id img-123 --src nova_imagem.png
        pdf-cli replace-image input.pdf output.pdf --id img-123 --src nova.png --filter grayscale
    """
    try:
        result_path = services.replace_image(
            pdf_path=pdf_path,
            output_path=output,
            image_id=id,
            src=src,
            filter_type=filter_type,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Imagem substituída com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("insert-object")
def insert_object(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    type: str = typer.Option(..., "--type", "-t", help="Tipo do objeto (text, image, table, etc.)"),
    params: str = typer.Option(..., "--params", "-p", help="Parâmetros do objeto em JSON"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Insere um novo objeto no PDF.

    Permite criar novos objetos, preencher todos campos conforme schema do tipo desejado.
    Permite passar parâmetros via JSON para máxima flexibilidade.

    Exemplo:
        pdf-cli insert-object input.pdf output.pdf --type text --params '{"page":0,"content":"Novo texto","x":100,"y":100,"width":200,"height":20,"font_name":"Arial","font_size":12}'
    """
    try:
        result_path = services.insert_object(
            pdf_path=pdf_path,
            output_path=output,
            obj_type=type,
            params=params,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Objeto inserido com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("restore-from-json")
def restore_from_json(
    source_pdf: str = typer.Argument(..., help="Caminho do PDF original"),
    json_file: str = typer.Argument(..., help="Caminho do arquivo JSON com alterações"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Restaura/reaplica alterações de um JSON ao PDF.

    Aplica todas alterações presentes no JSON ao PDF original.
    Altera textos, imagens, posições, inclui ou remove objetos conforme especificação do JSON.

    Exemplo:
        pdf-cli restore-from-json source.pdf objetos_editados.json output.pdf
    """
    try:
        result_path = services.restore_from_json(
            source_pdf=source_pdf,
            json_file=json_file,
            output_path=output,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] PDF restaurado do JSON com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("edit-metadata")
def edit_metadata(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    title: Optional[str] = typer.Option(None, "--title", help="Novo título"),
    author: Optional[str] = typer.Option(None, "--author", help="Novo autor"),
    keywords: Optional[str] = typer.Option(None, "--keywords", help="Palavras-chave (separadas por vírgula)"),
    subject: Optional[str] = typer.Option(None, "--subject", help="Novo assunto"),
    creator: Optional[str] = typer.Option(None, "--creator", help="Novo criador"),
    producer: Optional[str] = typer.Option(None, "--producer", help="Novo produtor"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Edita metadados do PDF.

    Permite edição dos metadados básicos e avançados do PDF.
    Gera log da alteração; mantém histórico de alterações de metadados.

    Exemplo:
        pdf-cli edit-metadata input.pdf output.pdf --title "Novo Título" --author "Novo Autor"
        pdf-cli edit-metadata input.pdf output.pdf --keywords "palavra1,palavra2"
    """
    try:
        result_path = services.edit_metadata(
            pdf_path=pdf_path,
            output_path=output,
            title=title,
            author=author,
            keywords=keywords,
            subject=subject,
            creator=creator,
            producer=producer,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Metadados editados com sucesso!")
        console.print(f"   Arquivo: {result_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("merge")
def merge_pdfs(
    pdf_paths: List[str] = typer.Argument(..., help="Caminhos dos PDFs a serem unidos"),
    output: str = typer.Option("merged.pdf", "--output", "-o", help="Caminho de saída do PDF unido"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Une múltiplos arquivos PDF em um único documento.

    Junta arquivos mantendo ordem dos objetos e páginas.
    Valida compatibilidade de modelos entre os PDFs.

    Exemplo:
        pdf-cli merge arquivo1.pdf arquivo2.pdf arquivo3.pdf -o combinado.pdf
    """
    try:
        result_path = services.merge_pdf(pdf_paths, output)
        console.print(f"[green]✓[/green] PDFs unidos com sucesso!")
        console.print(f"   Arquivo: {result_path}")
        console.print(f"   PDFs combinados: {len(pdf_paths)}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("delete-pages")
def delete_pages(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    output: str = typer.Argument(..., help="Caminho de saída do PDF modificado"),
    pages: str = typer.Option(..., "--pages", "-p", help="Páginas a excluir (ex: 1,3,5 ou 1-5)"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Exclui páginas específicas de um PDF.

    Remove páginas específicas, ajusta estrutura restante dos objetos.
    Salva log de operação.

    Exemplo:
        pdf-cli delete-pages input.pdf output.pdf --pages 1,4,6-8
        pdf-cli delete-pages input.pdf output.pdf --pages 1-5
    """
    try:
        # Confirmar se for operação destrutiva sem --force
        if not force:
            page_list = services.parse_page_numbers(pages)
            console.print(f"[yellow]⚠️  Você está prestes a excluir {len(page_list)} página(s).[/yellow]")
            console.print(f"   Páginas: {pages}")

            confirm = typer.confirm("Deseja continuar?", default=False)
            if not confirm:
                console.print("[yellow]Operação cancelada.[/yellow]")
                raise typer.Exit(0)

        page_numbers = services.parse_page_numbers(pages)
        result_path = services.delete_pages(
            pdf_path=pdf_path,
            page_numbers=page_numbers,
            output_path=output,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] Páginas excluídas com sucesso!")
        console.print(f"   Arquivo: {result_path}")
        console.print(f"   Páginas excluídas: {len(page_numbers)}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("split")
def split_pdf(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF de entrada"),
    ranges: str = typer.Option(..., "--ranges", "-r", help="Faixas de páginas (ex: 1-3,4-6)"),
    out: str = typer.Option("split_", "--out", "-o", help="Prefixo para os arquivos de saída"),
    force: bool = typer.Option(False, "--force", help="Sobrescreve sem criar backup"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Divide o PDF em diversos arquivos conforme faixas de páginas.

    Divide PDF em diversos arquivos conforme faixas de páginas.
    Mantém integridade dos objetos exportados/inseridos.

    Exemplo:
        pdf-cli split input.pdf --ranges 1-3,4-6 --out prefix_
        pdf-cli split input.pdf --ranges 1-5,6-10 --out resultado_
    """
    try:
        page_ranges = services.parse_page_ranges(ranges)
        result_files = services.split_pdf(
            pdf_path=pdf_path,
            ranges=page_ranges,
            output_prefix=out,
            create_backup=not force
        )
        console.print(f"[green]✓[/green] PDF dividido com sucesso!")
        console.print(f"   Arquivos criados: {len(result_files)}")
        for file_path in result_files:
            console.print(f"     - {file_path}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


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
