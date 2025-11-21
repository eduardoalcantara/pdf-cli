"""
Módulo Commands - Implementação de todos os comandos CLI.

Este módulo contém todas as funções que implementam os comandos do CLI,
utilizando apenas print() para saída e validando argumentos manualmente.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import json

# Imports dos módulos do projeto
try:
    from app import services
    from core.exceptions import PDFCliException
except ImportError:
    import app.services as services
    from core.exceptions import PDFCliException

from cli.help import print_success, print_error, print_warning
from cli.parser import get_flag_value, has_flag


def _validate_input_output_paths(input_path: str, output_path: str) -> None:
    """
    Valida que os caminhos de entrada e saída não são o mesmo arquivo.

    Args:
        input_path: Caminho do arquivo de entrada
        output_path: Caminho do arquivo de saída

    Raises:
        PDFCliException: Se os caminhos forem iguais (mesmo arquivo)
    """
    input_abs = Path(input_path).resolve()
    output_abs = Path(output_path).resolve()

    if input_abs == output_abs:
        raise PDFCliException(
            f"Erro: O arquivo de entrada e saida sao o mesmo: {input_path}\n"
            f"   Use um nome diferente para o arquivo de saida."
        )


def _validate_pdf_path(pdf_path: str, param_name: str = "arquivo_entrada.pdf") -> None:
    """
    Valida que o caminho PDF inclui o nome do arquivo.

    Args:
        pdf_path: Caminho do arquivo PDF
        param_name: Nome do parâmetro para mensagem de erro
    """
    if not pdf_path.endswith('.pdf'):
        print_warning(f"O caminho {param_name} nao termina com .pdf")
        print(f"  Caminho informado: {pdf_path}")
        print(f"  Certifique-se de incluir o nome completo do arquivo, exemplo: ./doc/boleto.pdf")


def _normalize_font_name(font_name: str) -> str:
    """Normaliza o nome da fonte removendo prefixos de subset."""
    if not font_name:
        return font_name
    if '+' in font_name:
        parts = font_name.split('+', 1)
        if len(parts) > 1:
            return parts[1]
    return font_name


def cmd_export_text(args: Dict[str, Any]) -> int:
    """Comando export-text: Extrai apenas textos do PDF para JSON."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 2:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli export-text <arquivo_entrada.pdf> <arquivo_saida.json> [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        pdf_path = args['positional'][0]
        output = args['positional'][1]

        # Validar caminhos
        _validate_pdf_path(pdf_path)
        _validate_input_output_paths(pdf_path, output)

        # Processar flags
        verbose = has_flag(args, 'verbose', 'l')

        # Executar
        stats = services.export_objects(pdf_path, output, types=["text"], include_fonts=False)

        print_success("Textos exportados com sucesso")
        print(f"  Arquivo: {output}")
        print(f"  Total de textos: {stats['by_type'].get('text', 0)}")

        if verbose:
            print()
            print("  Estatisticas:")
            print(f"    Total de objetos: {stats['total_objects']}")
            if stats.get('by_page'):
                print(f"    Paginas: {len(stats['by_page'])}")

        return 0

    except PDFCliException as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1


def cmd_export_objects(args: Dict[str, Any]) -> int:
    """Comando export-objects: Extrai objetos do PDF para JSON."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 2:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli export-objects <arquivo_entrada.pdf> <arquivo_saida.json> [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        pdf_path = args['positional'][0]
        output = args['positional'][1]

        # Validar caminhos
        _validate_pdf_path(pdf_path)
        _validate_input_output_paths(pdf_path, output)

        # Processar tipos
        types = None
        types_str = get_flag_value(args, 'types', 't')
        if types_str:
            types = types_str.split(',') if isinstance(types_str, str) else None

        # Processar flags
        include_fonts = has_flag(args, 'include-fonts')
        verbose = has_flag(args, 'verbose', 'l')

        # Executar
        stats = services.export_objects(pdf_path, output, types, include_fonts)

        print_success("Objetos exportados com sucesso")
        print(f"  Arquivo: {output}")
        print(f"  Total de objetos: {stats['total_objects']}")

        if include_fonts and 'fonts' in stats:
            print(f"  Total de fontes: {stats['fonts']['total_fonts']}")

        if verbose:
            print()
            print("  Por tipo:")
            for obj_type, count in stats['by_type'].items():
                if count > 0:
                    print(f"    {obj_type}: {count}")

        return 0

    except PDFCliException as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1


def cmd_export_images(args: Dict[str, Any]) -> int:
    """Comando export-images: Extrai imagens do PDF como arquivos PNG/JPG."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 2:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli export-images <arquivo_entrada.pdf> <diretorio_saida> [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        pdf_path = args['positional'][0]
        output_dir = args['positional'][1]

        # Validar caminho PDF
        _validate_pdf_path(pdf_path)

        # Processar formato
        format_str = get_flag_value(args, 'format', 'f', default='png')
        if format_str.lower() == 'jpeg':
            format_str = 'jpg'
        if format_str.lower() not in ['png', 'jpg']:
            print_error(f"Formato invalido: {format_str}. Use 'png' ou 'jpg'.")
            return 1

        # Processar flags
        verbose = has_flag(args, 'verbose', 'l')

        # Executar
        stats = services.export_images(pdf_path, output_dir, format=format_str)

        print_success("Imagens exportadas com sucesso")
        print(f"  Diretorio: {stats['output_directory']}")
        print(f"  Total de imagens: {stats['total_images']}")

        if verbose:
            print()
            print("  Por pagina:")
            for page, count in sorted(stats['by_page'].items()):
                print(f"    Pagina {page}: {count} imagem(ns)")

            if stats['saved_files']:
                print()
                print("  Arquivos salvos:")
                for img in stats['saved_files'][:10]:
                    print(f"    - {img['filename']} ({img['width']}x{img['height']}px, pagina {img['page']})")
                if len(stats['saved_files']) > 10:
                    print(f"    ... (+{len(stats['saved_files'])-10} mais)")

        return 0

    except PDFCliException as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1


def cmd_list_fonts(args: Dict[str, Any]) -> int:
    """Comando list-fonts: Lista todas as fontes e variantes usadas no PDF."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 1:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli list-fonts <arquivo_entrada.pdf> [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        pdf_path = args['positional'][0]

        # Validar caminho PDF
        _validate_pdf_path(pdf_path)

        from app.pdf_repo import PDFRepository

        with PDFRepository(pdf_path) as repo:
            fonts_dict = repo.extract_fonts()
            text_objects = repo.extract_text_objects()

            # Estatísticas de uso por fonte
            font_stats = {}
            for text_obj in text_objects:
                font_name = text_obj.font_name
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
                normalized_font_name = _normalize_font_name(font_data.name)
                usage = font_stats.get(normalized_font_name, {})

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

                font_info = {
                    "name": font_data.name,
                    "base_font": font_data.base_font,
                    "normalized_name": normalized_font_name,
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

            fonts_info.sort(key=lambda x: x["name"] or "")

            # Exibir no console
            print()
            print(f"Fontes encontradas no PDF: {len(fonts_info)}")
            print()

            verbose = has_flag(args, 'verbose', 'l')

            for i, font_info in enumerate(fonts_info, 1):
                variant_str = f" ({', '.join(font_info['variants'])})" if font_info['variants'] else ""
                embedded_str = " [EMBEDDED]" if font_info["embedded"] else " [NAO EMBEDDED]"

                display_name = font_info.get('normalized_name', font_info['name']) or 'N/A'
                print(f"{i}. {display_name}{variant_str}{embedded_str}")

                if font_info["usage"]["occurrences"] > 0:
                    print(f"   Usada em: {font_info['usage']['occurrences']} ocorrencia(s)")
                    if verbose or len(font_info['usage']['pages']) <= 10:
                        print(f"   Paginas: {', '.join(map(str, font_info['usage']['pages']))}")
                    else:
                        pages_str = f"{', '.join(map(str, font_info['usage']['pages'][:5]))}, ... (+{len(font_info['usage']['pages'])-5} mais)"
                        print(f"   Paginas: {pages_str}")

                    if font_info['usage']['sizes']:
                        sizes_str = ", ".join([f"{s}pt" for s in font_info['usage']['sizes'][:10]])
                        if len(font_info['usage']['sizes']) > 10:
                            sizes_str += f" (+{len(font_info['usage']['sizes'])-10} mais)"
                        print(f"   Tamanhos: {sizes_str}")
                else:
                    print(f"   Nao usada em nenhum objeto de texto extraido")

                if font_info["base_font"] and font_info["base_font"] != font_info["name"]:
                    print(f"   Base: {font_info['base_font']}")

                if verbose and font_info["encoding"]:
                    print(f"   Encoding: {font_info['encoding']}")

                if verbose and font_info["xref"]:
                    print(f"   XRef: {font_info['xref']}")

                print()

            # Salvar em JSON se solicitado
            output_file = get_flag_value(args, 'output', 'o')
            if output_file:
                output_data = {
                    "pdf_path": pdf_path,
                    "total_fonts": len(fonts_info),
                    "fonts": fonts_info
                }
                with open(output_file, "w", encoding="utf-8") as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                print_success(f"Informacoes salvas em: {output_file}")

        return 0

    except PDFCliException as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1


# ============================================================================
# COMANDOS DE EDIÇÃO
# ============================================================================

def cmd_edit_text(args: Dict[str, Any]) -> int:
    """Comando edit-text: Edita objeto de texto no PDF."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 2:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli edit-text <arquivo_entrada.pdf> <arquivo_saida.pdf> --new-content \"texto\" [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        pdf_path = args['positional'][0]
        output = args['positional'][1]

        # Validar caminhos
        _validate_pdf_path(pdf_path)
        _validate_input_output_paths(pdf_path, output)

        # Validar new-content obrigatório
        new_content = get_flag_value(args, 'new-content', 'new_content')
        if not new_content:
            print_error("--new-content e obrigatorio")
            return 1

        # Processar flags
        object_id = get_flag_value(args, 'id')
        content = get_flag_value(args, 'content')
        align = get_flag_value(args, 'align')
        pad = has_flag(args, 'pad')
        x = get_flag_value(args, 'x')
        y = get_flag_value(args, 'y')
        font_name = get_flag_value(args, 'font-name')
        font_size = get_flag_value(args, 'font-size')
        color = get_flag_value(args, 'color')
        rotation = get_flag_value(args, 'rotation')
        all_occurrences = has_flag(args, 'all-occurrences')
        prefer_engine = get_flag_value(args, 'prefer-engine', default='pymupdf')
        force = has_flag(args, 'force', 'q')
        verbose = has_flag(args, 'verbose', 'l')

        # Converter tipos
        if x is not None:
            try:
                x = float(x)
            except ValueError:
                print_error(f"Valor invalido para --x: {x}")
                return 1
        if y is not None:
            try:
                y = float(y)
            except ValueError:
                print_error(f"Valor invalido para --y: {y}")
                return 1
        if font_size is not None:
            try:
                font_size = int(font_size)
            except ValueError:
                print_error(f"Valor invalido para --font-size: {font_size}")
                return 1
        if rotation is not None:
            try:
                rotation = float(rotation)
            except ValueError:
                print_error(f"Valor invalido para --rotation: {rotation}")
                return 1

        # Processar all_occurrences com feedback
        if all_occurrences:
            # Pré-verificar fontes faltantes
            from app.pdf_repo import PDFRepository
            from core.font_manager import FontManager, FontMatchQuality

            preview_font_manager = FontManager()
            with PDFRepository(pdf_path) as repo:
                if content:
                    text_objects = repo.extract_text_objects()
                    fonts_dict = repo.extract_fonts()
                    target_objects = [obj for obj in text_objects if content in obj.content]

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

            # Solicitar confirmação se houver fontes faltantes
            if preview_font_manager.has_missing_fonts():
                summary = preview_font_manager.get_missing_fonts_summary()
                print(summary)
                print_warning("ATENCAO: O PDF gerado pode ter aparencia diferente devido as fontes faltantes.")
                response = input("\nDeseja continuar assim mesmo e gerar o PDF? (s/N): ").strip().lower()
                if response not in ['s', 'sim', 'y', 'yes']:
                    print_warning("Operacao cancelada pelo usuario.")
                    return 0
                print()

            print("\nProcessando ocorrencias...\n")

            def feedback_callback(detail):
                print(f"Ocorrencia (processando...)")
                print(f"  ID: {detail['id']}")
                print(f"  Pagina: {detail['page']}  |  Posicao: ({detail['coordinates']['x']:.1f}, {detail['coordinates']['y']:.1f})  |  Tamanho: {detail['coordinates']['width']:.1f}x{detail['coordinates']['height']:.1f}")
                print(f"  Modificado: '{detail['original_content']}' -> '{detail['new_content']}'")
                print(f"  Fonte original: {detail['font_original']} ({detail['font_size']}pt)")
                status = "AVISO" if detail['font_fallback'] else "OK"
                print(f"  [{status}] Fonte usada: {detail['font_used']} ({detail['font_source']})")
                print()

            result_path, details = services.edit_text(
                pdf_path=pdf_path,
                output_path=output,
                object_id=object_id,
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
                feedback_callback=feedback_callback
            )
            occurrences_processed = details.get('occurrences_processed', 0)
            print_success(f"Total: {occurrences_processed} ocorrencia(s) editada(s) com sucesso")
            print(f"  Arquivo: {result_path}")

            if details.get("engine_used"):
                engine_used = details["engine_used"]
                print(f"  Engine usado: {engine_used}")
                if details.get("font_fallback_detected"):
                    print_warning("Fallback de fonte detectado. Tente usar --prefer-engine pypdf se disponivel.")
        else:
            result_path = services.edit_text(
                pdf_path=pdf_path,
                output_path=output,
                object_id=object_id,
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
            print_success("Texto editado com sucesso")
            print(f"  Arquivo: {result_path}")

        return 0

    except PDFCliException as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1


# Placeholder para comandos restantes - serão adicionados em seguida
def cmd_edit_table(args: Dict[str, Any]) -> int:
    """Comando edit-table: Edita célula de tabela no PDF."""
    print_error("Comando edit-table ainda nao implementado neste formato")
    return 1


def cmd_replace_image(args: Dict[str, Any]) -> int:
    """Comando replace-image: Substitui imagem no PDF."""
    print_error("Comando replace-image ainda nao implementado neste formato")
    return 1


def cmd_insert_object(args: Dict[str, Any]) -> int:
    """Comando insert-object: Insere novo objeto no PDF."""
    print_error("Comando insert-object ainda nao implementado neste formato")
    return 1


def cmd_restore_from_json(args: Dict[str, Any]) -> int:
    """Comando restore-from-json: Restaura PDF via JSON."""
    print_error("Comando restore-from-json ainda nao implementado neste formato")
    return 1


def cmd_edit_metadata(args: Dict[str, Any]) -> int:
    """Comando edit-metadata: Edita metadados do PDF."""
    print_error("Comando edit-metadata ainda nao implementado neste formato")
    return 1


def cmd_merge(args: Dict[str, Any]) -> int:
    """Comando merge: Une múltiplos PDFs."""
    print_error("Comando merge ainda nao implementado neste formato")
    return 1


def cmd_delete_pages(args: Dict[str, Any]) -> int:
    """Comando delete-pages: Exclui páginas do PDF."""
    print_error("Comando delete-pages ainda nao implementado neste formato")
    return 1


def cmd_split(args: Dict[str, Any]) -> int:
    """Comando split: Divide PDF em múltiplos arquivos."""
    print_error("Comando split ainda nao implementado neste formato")
    return 1


def cmd_md_to_pdf(args: Dict[str, Any]) -> int:
    """Comando md-to-pdf: Converte arquivo Markdown para PDF."""
    try:
        # Validar argumentos posicionais
        if len(args['positional']) < 2:
            print_error("Argumentos insuficientes")
            print("Sintaxe: pdf-cli md-to-pdf <entrada.md> <saida.pdf> [opcoes]")
            print("Use --help para ver exemplos e detalhes")
            return 1

        md_path = args['positional'][0]
        pdf_path = args['positional'][1]

        # Validar arquivo de entrada
        md_file = Path(md_path)
        if not md_file.exists():
            print_error(f"Arquivo markdown nao encontrado: {md_path}")
            return 1

        if not md_path.lower().endswith('.md'):
            print_error(f"Arquivo de entrada deve ser .md: {md_path}")
            return 1

        # Validar arquivo de saída
        if not pdf_path.lower().endswith('.pdf'):
            print_error(f"Arquivo de saida deve ser .pdf: {pdf_path}")
            return 1

        # Validar que entrada e saída são diferentes
        _validate_input_output_paths(md_path, pdf_path)

        # Processar opções
        css_path = get_flag_value(args, 'css')
        verbose = has_flag(args, 'verbose', 'l')

        # Importar converter
        from app.md_converter import convert_md_to_pdf

        # Executar conversão
        if verbose:
            print(f"[INFO] Convertendo {md_path} para {pdf_path}...")

        result = convert_md_to_pdf(
            md_path=md_path,
            pdf_path=pdf_path,
            css_path=css_path,
            verbose=verbose
        )

        if result['status'] == 'success':
            print_success("Conversao concluida com sucesso")
            print(f"  Entrada: {md_path}")
            print(f"  Saida: {pdf_path}")
            if result.get('pages'):
                print(f"  Paginas geradas: {result['pages']}")
            return 0
        else:
            print_error(f"Erro na conversao: {result.get('error', 'Erro desconhecido')}")
            return 1

    except FileNotFoundError as e:
        print_error(str(e))
        return 1
    except ValueError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Erro inesperado: {str(e)}")
        if verbose or has_flag(args, 'verbose', 'l'):
            import traceback
            traceback.print_exc()
        return 1
