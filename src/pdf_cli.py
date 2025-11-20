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
        export-text        - Extrai apenas textos do PDF para JSON (alias)
        export-objects     - Extrai objetos do PDF para JSON
        export-images      - Extrai imagens do PDF como arquivos PNG/JPG
        list-fonts         - Lista todas as fontes e variantes usadas no PDF
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
        console.print("[bold cyan]PDF-cli[/bold cyan] versão 0.6.0 (Fase 6)")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        # Banner obrigatório conforme Fase 2
        print_banner()
        console.print(ctx.get_help())


@app.command("export-text")
def export_text(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output: str = typer.Argument(..., help="Caminho de saída para o JSON"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Extrai e exporta apenas textos do PDF para JSON (alias para export-objects --types text).

    Útil para copiar textos de PDFs protegidos ou exportar apenas conteúdo textual.
    Permite exportar textos com metadados (posição, fonte, tamanho, etc.).

    Exemplo:
        pdf-cli export-text documento.pdf textos.json
        pdf-cli export-text documento.pdf textos.json --verbose
    """
    try:
        # Alias: chamar export-objects com --types text
        stats = services.export_objects(pdf_path, output, types=["text"], include_fonts=False)

        console.print(f"[green]✓[/green] Textos exportados com sucesso!")
        console.print(f"   Arquivo: {output}")
        console.print(f"   Total de textos: {stats['by_type'].get('text', 0)}")

        if verbose:
            console.print(f"\n   Estatísticas:")
            console.print(f"     Total de objetos: {stats['total_objects']}")
            if stats.get('by_page'):
                console.print(f"     Páginas: {len(stats['by_page'])}")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("export-objects")
def export_objects(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output: str = typer.Argument(..., help="Caminho de saída para o JSON"),
    types: Optional[str] = typer.Option(None, "--types", "-t", help="Tipos de objetos a exportar (ex: text,image,table)"),
    include_fonts: bool = typer.Option(False, "--include-fonts", help="Inclui informações de fontes no JSON exportado"),
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

        stats = services.export_objects(pdf_path, output, type_list, include_fonts=include_fonts)

        console.print(f"[green]✓[/green] Objetos exportados com sucesso!")
        console.print(f"   Arquivo: {output}")
        console.print(f"   Total de objetos: {stats['total_objects']}")

        if include_fonts and 'fonts' in stats:
            console.print(f"   Total de fontes: {stats['fonts']['total_fonts']}")

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


@app.command("export-images")
def export_images(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output_dir: str = typer.Argument(..., help="Diretório onde as imagens serão salvas"),
    format: str = typer.Option("png", "--format", "-f", help="Formato de saída: png ou jpg"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Extrai todas as imagens do PDF e salva como arquivos de imagem reais (PNG ou JPG).

    Diferente de export-objects --types image que exporta apenas metadados em JSON,
    este comando salva as imagens como arquivos reais em um diretório.

    As imagens são nomeadas como: imagem_<página>_<índice>.<extensão>
    Exemplo: imagem_0_1.png, imagem_1_3.jpg

    Exemplo:
        pdf-cli export-images documento.pdf imagens/
        pdf-cli export-images documento.pdf imagens/ --format jpg
        pdf-cli export-images documento.pdf imagens/ --format png --verbose
    """
    try:
        stats = services.export_images(pdf_path, output_dir, format=format)

        console.print(f"[green]✓[/green] Imagens exportadas com sucesso!")
        console.print(f"   Diretório: {stats['output_directory']}")
        console.print(f"   Total de imagens: {stats['total_images']}")

        if verbose:
            console.print(f"\n   Por página:")
            for page, count in sorted(stats['by_page'].items()):
                console.print(f"     Página {page}: {count} imagem(ns)")

            if stats['saved_files']:
                console.print(f"\n   Arquivos salvos:")
                for img in stats['saved_files'][:10]:  # Mostrar apenas primeiras 10
                    console.print(f"     - {img['filename']} ({img['width']}×{img['height']}px, página {img['page']})")
                if len(stats['saved_files']) > 10:
                    console.print(f"     ... (+{len(stats['saved_files'])-10} mais)")
    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


@app.command("list-fonts")
def list_fonts(
    pdf_path: str = typer.Argument(..., help="Caminho para o arquivo PDF"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Caminho de saída para JSON (opcional)"),
    verbose: bool = typer.Option(False, "--verbose", help="Exibe informações detalhadas"),
) -> None:
    """
    Lista todas as fontes e suas variantes usadas no PDF.

    Mostra informações sobre cada fonte:
    - Nome da fonte
    - Variantes (Bold, Italic, Narrow, etc.)
    - Se está embeddada no PDF
    - Tamanhos usados
    - Páginas onde é usada

    Exemplo:
        pdf-cli list-fonts documento.pdf
        pdf-cli list-fonts documento.pdf --output fontes.json
        pdf-cli list-fonts documento.pdf --verbose
    """
    try:
        from app.pdf_repo import PDFRepository

        with PDFRepository(pdf_path) as repo:
            # Extrair fontes do PDF
            fonts_dict = repo.extract_fonts()

            # Extrair textos para obter estatísticas de uso
            text_objects = repo.extract_text_objects()

            # Estatísticas de uso por fonte (já normalizados pelo extract_text_objects)
            font_stats = {}
            for text_obj in text_objects:
                font_name = text_obj.font_name
                # Normalizar nome para garantir correspondência
                normalized_name = _normalize_font_name(font_name)
                if normalized_name not in font_stats:
                    font_stats[normalized_name] = {
                        "name": normalized_name,
                        "pages": set(),
                        "sizes": set(),
                        "occurrences": 0
                    }
                font_stats[normalized_name]["pages"].add(text_obj.page)
                font_stats[normalized_name]["sizes"].add(text_obj.font_size)
                font_stats[normalized_name]["occurrences"] += 1

            # Preparar dados para exibição
            fonts_info = []
            for font_key, font_data in fonts_dict.items():
                # Normalizar nome da fonte extraída para corresponder às estatísticas
                normalized_font_name = _normalize_font_name(font_data.name)
                usage = font_stats.get(normalized_font_name, {})

                # Detectar variantes adicionais
                name_upper = font_data.name.upper() if font_data.name else ""
                variants_detected = []
                if font_data.is_bold:
                    variants_detected.append("Bold")
                if font_data.is_italic:
                    variants_detected.append("Italic")
                if "NARROW" in name_upper:
                    variants_detected.append("Narrow")
                if "CONDENSED" in name_upper:
                    variants_detected.append("Condensed")
                if "LIGHT" in name_upper:
                    variants_detected.append("Light")
                if "BLACK" in name_upper:
                    variants_detected.append("Black")

                # Usar nome normalizado para exibição (mais limpo)
                display_name = normalized_font_name if normalized_font_name != font_data.name else font_data.name

                font_info = {
                    "name": font_data.name,  # Nome original (com prefixo se houver)
                    "base_font": font_data.base_font,
                    "normalized_name": normalized_font_name,  # Nome sem prefixo
                    "variants": variants_detected,
                    "embedded": font_data.font_file_path is not None,
                    "encoding": getattr(font_data, 'encoding', ''),
                    "xref": getattr(font_data, 'xref', None),
                    "usage": {
                        "occurrences": usage.get("occurrences", 0),
                        "pages": sorted(list(usage.get("pages", set()))),
                        "sizes": sorted(list(usage.get("sizes", set())))
                    }
                }
                fonts_info.append(font_info)

            # Ordenar por nome
            fonts_info.sort(key=lambda x: x["name"] or "")

            # Exibir no console
            console.print(f"\n[bold cyan]📚 Fontes encontradas no PDF:[/bold cyan] {len(fonts_info)}\n")

            for i, font_info in enumerate(fonts_info, 1):
                variant_str = f" ([{', '.join(font_info['variants'])}])" if font_info['variants'] else ""
                embedded_str = " [green]✓ embeddada[/green]" if font_info["embedded"] else " [yellow]⚠ não embeddada[/yellow]"

                # Usar nome normalizado para exibição (mais legível)
                display_name = font_info.get('normalized_name', font_info['name']) or 'N/A'
                console.print(f"{i}. [bold]{display_name}[/bold]{variant_str}{embedded_str}")

                if font_info["usage"]["occurrences"] > 0:
                    console.print(f"   Usada em: {font_info['usage']['occurrences']} ocorrência(s)")
                    if verbose or len(font_info['usage']['pages']) <= 10:
                        console.print(f"   Páginas: {', '.join(map(str, font_info['usage']['pages']))}")
                    else:
                        pages_str = f"{', '.join(map(str, font_info['usage']['pages'][:5]))}, ... (+{len(font_info['usage']['pages'])-5} mais)"
                        console.print(f"   Páginas: {pages_str}")

                    if font_info['usage']['sizes']:
                        sizes_str = ", ".join([f"{s}pt" for s in font_info['usage']['sizes'][:10]])
                        if len(font_info['usage']['sizes']) > 10:
                            sizes_str += f" (+{len(font_info['usage']['sizes'])-10} mais)"
                        console.print(f"   Tamanhos: {sizes_str}")
                else:
                    console.print(f"   [dim]Não usada em nenhum objeto de texto extraído[/dim]")

                if font_info["base_font"] and font_info["base_font"] != font_info["name"]:
                    console.print(f"   Base: {font_info['base_font']}")

                if verbose and font_info["encoding"]:
                    console.print(f"   Encoding: {font_info['encoding']}")

                if verbose and font_info["xref"]:
                    console.print(f"   XRef: {font_info['xref']}")

                console.print()

            # Salvar em JSON se solicitado
            if output:
                import json
                output_data = {
                    "pdf_path": pdf_path,
                    "total_fonts": len(fonts_info),
                    "fonts": fonts_info
                }
                with open(output, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                console.print(f"[green]✓[/green] Informações salvas em: {output}")

    except PDFCliException as e:
        console.print(f"[bold red]Erro:[/bold red] {str(e)}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Erro inesperado:[/bold red] {str(e)}")
        if verbose:
            import traceback
            console.print(traceback.format_exc())
        raise typer.Exit(1)


def _validate_input_output_paths(input_path: str, output_path: str) -> None:
    """
    Valida que os caminhos de entrada e saída não são o mesmo arquivo.

    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída

    Raises:
        PDFCliException: Se os caminhos forem iguais (mesmo arquivo)
    """
    from pathlib import Path
    from core.exceptions import PDFCliException

    # Resolver caminhos absolutos e normalizar
    input_abs = Path(input_path).resolve()
    output_abs = Path(output_path).resolve()

    if input_abs == output_abs:
        raise PDFCliException(
            f"Erro: O arquivo de entrada e saída são o mesmo: {input_path}\n"
            f"   Use um nome diferente para o arquivo de saída."
        )


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
    all_occurrences: bool = typer.Option(False, "--all-occurrences", help="Substitui todas as ocorrências do texto (apenas com --content)"),
    prefer_engine: str = typer.Option("pymupdf", "--prefer-engine", help="Engine preferido: 'pymupdf' (padrão) ou 'pypdf' (Fase 5)"),
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
        pdf-cli edit-text input.pdf output.pdf --content "ALCANTARA" --new-content "ALCÂNTARA" --all-occurrences
    """
    try:
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

        if all_occurrences:
            # Pré-verificar fontes faltantes ANTES de processar
            from app.pdf_repo import PDFRepository
            from core.font_manager import FontManager, FontMatchQuality

            preview_font_manager = FontManager()
            with PDFRepository(pdf_path) as repo:
                if content:  # Só faz sentido se há busca por conteúdo
                    text_objects = repo.extract_text_objects()
                    fonts_dict = repo.extract_fonts()
                    target_objects = [obj for obj in text_objects if content in obj.content]

                    # Verificar fontes que serão usadas
                    for obj in target_objects:
                        font_loaded, font_source = repo.get_font_for_text_object(obj.font_name, fonts_dict)
                        if font_loaded:
                            loaded_font_name = font_loaded.name if hasattr(font_loaded, 'name') else ""
                            font_name_matches = (loaded_font_name.lower() in obj.font_name.lower() or
                                               obj.font_name.lower() in loaded_font_name.lower())

                            if font_source in ["extracted", "embedded"]:
                                match_quality = FontMatchQuality.EXACT
                            elif font_name_matches and font_source in ["system", "cache"]:
                                match_quality = FontMatchQuality.EXACT
                            elif font_source in ["system", "cache"] and not font_name_matches:
                                match_quality = FontMatchQuality.VARIANT
                            elif font_source == "fallback":
                                match_quality = FontMatchQuality.FALLBACK
                            else:
                                match_quality = FontMatchQuality.SIMILAR

                            if match_quality != FontMatchQuality.EXACT:
                                preview_font_manager.add_requirement(
                                    font_name=obj.font_name,
                                    found_font=loaded_font_name,
                                    match_quality=match_quality,
                                    system_path=getattr(font_loaded, '_fontfile', None),
                                    page=obj.page
                                )
                        else:
                            preview_font_manager.add_requirement(
                                font_name=obj.font_name,
                                found_font=None,
                                match_quality=FontMatchQuality.MISSING,
                                page=obj.page
                            )

            # Se há fontes faltantes, solicitar confirmação ANTES de processar
            if preview_font_manager.has_missing_fonts():
                summary = preview_font_manager.get_missing_fonts_summary()
                print(summary)
                console.print("\n[bold yellow]⚠️ ATENÇÃO:[/bold yellow] O PDF gerado pode ter aparência diferente devido às fontes faltantes.")
                if not typer.confirm("\nDeseja continuar assim mesmo e gerar o PDF?", default=False):
                    console.print("[yellow]Operação cancelada pelo usuário.[/yellow]")
                    raise typer.Abort()
                console.print()

            console.print("\n[bold yellow]Processando ocorrências...[/bold yellow]\n")
            result_path, details = services.edit_text(
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
                create_backup=not force,
                all_occurrences=all_occurrences,
                prefer_engine=prefer_engine,
                feedback_callback=lambda detail: console.print(
                    f"┌─ Ocorrência (processando...)\n"
                    f"│ ID: {detail['id']}\n"
                    f"│ Página: {detail['page']}  |  Posição: ({detail['coordinates']['x']:.1f}, {detail['coordinates']['y']:.1f})  |  Tamanho: {detail['coordinates']['width']:.1f}×{detail['coordinates']['height']:.1f}\n"
                    f"│ Modificado: '{detail['original_content']}' → '{detail['new_content']}'\n"
                    f"│ Fonte original: {detail['font_original']} ({detail['font_size']}pt)\n"
                    f"│ {'⚠' if detail['font_fallback'] else '✓'} Fonte usada: {detail['font_used']} ({detail['font_source']})\n"
                    f"└─\n"
                )
            )
            occurrences_processed = details.get('occurrences_processed', 0)
            console.print(f"[green]✓[/green] Total: {occurrences_processed} ocorrência(s) editada(s) com sucesso!")
            console.print(f"   Arquivo: {result_path}")

            # Mostrar informações sobre engine usado (Fase 5)
            if details.get("engine_used"):
                engine_used = details["engine_used"]
                console.print(f"[dim]Engine usado: {engine_used}[/dim]")
                if details.get("font_fallback_detected"):
                    console.print(f"[yellow]⚠[/yellow] [dim]Fallback de fonte detectado. Tente usar --prefer-engine pypdf se disponível.[/dim]")
        else:
            # Caso de edição única (não --all-occurrences)
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
                create_backup=not force,
                all_occurrences=all_occurrences,
                prefer_engine=prefer_engine
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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(source_pdf, output)

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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

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
        # Validar que entrada e saída não são o mesmo arquivo
        _validate_input_output_paths(pdf_path, output)

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
