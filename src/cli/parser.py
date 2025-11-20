"""
Módulo Parser - Parser manual de argumentos da linha de comando.

Este módulo implementa um parser manual de argumentos usando apenas sys.argv,
sem dependências externas. Suporta:
- Comandos posicionais
- Flags opcionais (--flag e -f)
- Valores de flags (--flag valor e -f valor)
- Help automático (--help comando e comando --help)
"""

from typing import Dict, List, Any, Optional


def parse_args(argv: List[str]) -> Dict[str, Any]:
    """
    Parse manual dos argumentos usando apenas sys.argv.

    Args:
        argv: Lista de argumentos (geralmente sys.argv)

    Returns:
        dict: Dicionário com argumentos parseados:
            - command: Nome do comando (ou None)
            - version: True se --version ou -v foi usado
            - help: True se --help ou -h foi usado
            - help_command: Nome do comando para help (se --help <comando>)
            - positional: Lista de argumentos posicionais
            - flags: Dicionário com flags e valores
    """
    args = {
        'command': None,
        'version': False,
        'help': False,
        'help_command': None,
        'positional': [],
        'flags': {}
    }

    i = 1  # Pular argv[0] que é o nome do script
    skip_next = False

    while i < len(argv):
        if skip_next:
            skip_next = False
            i += 1
            continue

        arg = argv[i]

        # Versão global (apenas se não tiver comando ainda)
        if arg in ['--version', '-v']:
            if args['command'] is None:
                args['version'] = True
            # Se já tem comando, -v não é versão (ignorar, pode ser digitado por engano)
            i += 1
            continue

        # Help
        if arg in ['--help', '-h']:
            args['help'] = True
            # Verificar se há comando antes ou depois
            if i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                # Formato: --help comando ou comando --help
                if args['command'] is None:
                    # Formato: --help comando
                    args['help_command'] = argv[i + 1]
                    skip_next = True
                else:
                    # Formato: comando --help (já temos comando)
                    pass
            i += 1
            continue

        # Se não tiver comando ainda, este é o comando
        if args['command'] is None and not arg.startswith('-'):
            args['command'] = arg
            i += 1
            continue

        # Flags/opções (começam com -- ou -)
        if arg.startswith('--'):
            flag_name = arg[2:]
            # Verificar se flag aceita valor (próximo arg não começa com -)
            if i + 1 < len(argv) and not argv[i + 1].startswith('-') and argv[i + 1] not in ['True', 'False']:
                args['flags'][flag_name] = argv[i + 1]
                skip_next = True
                i += 1
            else:
                args['flags'][flag_name] = True
            i += 1
        elif arg.startswith('-') and len(arg) > 1:
            # Flag curta (-v, -t, etc)
            flag_char = arg[1:]
            # Se tiver mais caracteres, pode ser valor (ex: -ttext,image)
            if '=' in flag_char:
                # Formato: -t=valor
                parts = flag_char.split('=', 1)
                args['flags'][parts[0]] = parts[1]
            elif len(flag_char) == 1:
                # Mapear flags curtas especiais
                if flag_char == 'l':
                    # -l = --verbose (log)
                    args['flags']['verbose'] = True
                elif flag_char == 'q':
                    # -q = --force (quiet)
                    args['flags']['force'] = True
                elif flag_char in ['t', 'o', 'f', 'r', 'p'] and i + 1 < len(argv) and not argv[i + 1].startswith('-'):
                    # Flag que aceita valor
                    args['flags'][flag_char] = argv[i + 1]
                    skip_next = True
                    i += 1
                else:
                    args['flags'][flag_char] = True
            else:
                # Múltiplas flags curtas (-vx) ou flag com valor (-ttext)
                # Assumir que é flag simples
                for char in flag_char:
                    args['flags'][char] = True
            i += 1
        else:
            # Argumento posicional
            args['positional'].append(arg)
            i += 1

    return args


def get_flag_value(args: Dict[str, Any], *flag_names: str, default: Any = None) -> Any:
    """
    Obtém o valor de uma flag, tentando múltiplos nomes.

    Args:
        args: Dicionário de argumentos parseados
        *flag_names: Nomes alternativos da flag (ex: 'verbose', 'v')
        default: Valor padrão se flag não encontrada

    Returns:
        Valor da flag ou default
    """
    for name in flag_names:
        if name in args['flags']:
            value = args['flags'][name]
            return value if value is not True else True
    return default


def has_flag(args: Dict[str, Any], *flag_names: str) -> bool:
    """
    Verifica se uma flag está presente.

    Args:
        args: Dicionário de argumentos parseados
        *flag_names: Nomes alternativos da flag

    Returns:
        True se flag está presente
    """
    return any(name in args['flags'] and args['flags'][name] for name in flag_names)
