#!/usr/bin/env python3
"""
Entrypoint principal e roteador de comandos da aplicação.

Este módulo serve apenas como ponto de entrada do CLI, roteando comandos
para os módulos apropriados (cli/help, cli/parser, cli/commands).

Para executar:
    python pdf_cli.py --help
    python pdf_cli.py export-text --help
    python pdf_cli.py --help export-text
"""

import sys
from pathlib import Path

# Adiciona o diretório src ao path para imports
# Se estiver rodando como executável PyInstaller, o __file__ aponta para um temp
# Nesse caso, precisamos encontrar o diretório base do executável
if getattr(sys, 'frozen', False):
    # Rodando como executável compilado (PyInstaller)
    # sys._MEIPASS contém o caminho temporário onde os arquivos estão descompactados
    base_path = Path(sys._MEIPASS)
    # Os módulos coletados pelo PyInstaller ficam em sys._MEIPASS
    # Adiciona ao path para garantir que os imports funcionem
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))
else:
    # Rodando como script Python normal
    sys.path.insert(0, str(Path(__file__).parent))

# Imports dos módulos CLI
from cli.help import (
    print_banner, print_help_general,
    print_help_export_text, print_help_export_objects, print_help_export_images, print_help_list_fonts,
    print_help_edit_text, print_help_edit_table, print_help_replace_image, print_help_insert_object,
    print_help_restore_from_json, print_help_edit_metadata, print_help_merge, print_help_delete_pages,
    print_help_split
)
from cli.parser import parse_args
from cli.commands import (
    cmd_export_text, cmd_export_objects, cmd_export_images, cmd_list_fonts,
    cmd_edit_text, cmd_edit_table, cmd_replace_image, cmd_insert_object,
    cmd_restore_from_json, cmd_edit_metadata, cmd_merge, cmd_delete_pages,
    cmd_split
)


# Mapa de comandos para funções
COMMAND_MAP = {
    'export-text': cmd_export_text,
    'export-objects': cmd_export_objects,
    'export-images': cmd_export_images,
    'list-fonts': cmd_list_fonts,
    'edit-text': cmd_edit_text,
    'edit-table': cmd_edit_table,
    'replace-image': cmd_replace_image,
    'insert-object': cmd_insert_object,
    'restore-from-json': cmd_restore_from_json,
    'edit-metadata': cmd_edit_metadata,
    'merge': cmd_merge,
    'delete-pages': cmd_delete_pages,
    'split': cmd_split,
}

# Mapa de comandos para help
HELP_MAP = {
    'export-text': print_help_export_text,
    'export-objects': print_help_export_objects,
    'export-images': print_help_export_images,
    'list-fonts': print_help_list_fonts,
    'edit-text': print_help_edit_text,
    'edit-table': print_help_edit_table,
    'replace-image': print_help_replace_image,
    'insert-object': print_help_insert_object,
    'restore-from-json': print_help_restore_from_json,
    'edit-metadata': print_help_edit_metadata,
    'merge': print_help_merge,
    'delete-pages': print_help_delete_pages,
    'split': print_help_split,
}


def main() -> int:
    """Função principal do CLI."""
    # Parse dos argumentos
    parsed = parse_args(sys.argv)

    # Versão global
    if parsed['version']:
        print("PDF-cli versao 0.7.0 (Fase 7)")
        return 0

    # Help geral ou de comando específico
    if parsed['help']:
        # Se há comando definido (formato: comando --help)
        if parsed['command']:
            help_func = HELP_MAP.get(parsed['command'])
            if help_func:
                help_func()
                return 0
            else:
                print(f"Comando '{parsed['command']}' encontrado mas help nao implementado")
                print("Use 'pdf-cli --help' para ver comandos disponiveis")
                return 1
        # Se há help_command (formato: --help comando)
        elif parsed['help_command']:
            help_func = HELP_MAP.get(parsed['help_command'])
            if help_func:
                help_func()
                return 0
            else:
                print(f"Comando '{parsed['help_command']}' nao encontrado ou help nao implementado")
                print("Use 'pdf-cli --help' para ver comandos disponiveis")
                return 1
        else:
            # Help geral
            print_banner()
            print_help_general()
            return 0

    # Se não tiver comando, mostrar banner + help
    if parsed['command'] is None:
        print_banner()
        print_help_general()
        return 0

    # Executar comando
    command_func = COMMAND_MAP.get(parsed['command'])
    if command_func:
        return command_func(parsed)
    else:
        print(f"ERRO: Comando '{parsed['command']}' nao implementado")
        print("Use 'pdf-cli --help' para ver comandos disponiveis")
        return 1


if __name__ == "__main__":
    sys.exit(main())
