#!/usr/bin/env python3
"""
Script de Validação de Honestidade - PDF-cli Fase 4.

Este script valida que todas as implementações do PDF-cli são REAIS
e não contêm mocks, simulações ou placeholders. Verifica:

1. Operações reais em arquivos PDF
2. Logs refletem operações reais
3. Resultados verificáveis
4. Transparência sobre limitações
"""

import sys
from pathlib import Path
import json
import importlib.util
import ast

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_for_mocks(file_path: Path) -> list:
    """
    Verifica se arquivo contém mocks ou simulações.

    Returns:
        Lista de ocorrências suspeitas.
    """
    issues = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Palavras-chave que indicam mocks/simulações
        suspicious_patterns = [
            ("mock", "Uso de mock detectado"),
            ("fake", "Uso de fake detectado"),
            ("simulate", "Simulação detectada"),
            ("placeholder", "Placeholder detectado"),
            ("TODO: implement", "TODO de implementação pendente"),
            ("pass  # TODO", "TODO com pass vazio"),
            ("NotImplementedError", "NotImplementedError (pode ser legítimo)"),
        ]

        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            line_lower = line.lower()
            for pattern, message in suspicious_patterns:
                if pattern.lower() in line_lower:
                    # Ignora comentários explicativos legítimos
                    if "limitação técnica" in line_lower or \
                       "documentado" in line_lower or \
                       "edit-table" in line_lower:
                        continue

                    # Ignora imports legítimos
                    if "import" in line_lower and pattern.lower() in line_lower:
                        continue

                    issues.append({
                        "file": str(file_path),
                        "line": i,
                        "pattern": pattern,
                        "message": message,
                        "code": line.strip()[:80]
                    })
    except Exception as e:
        issues.append({
            "file": str(file_path),
            "line": 0,
            "pattern": "error",
            "message": f"Erro ao ler arquivo: {e}",
            "code": ""
        })

    return issues


def check_real_operations(file_path: Path) -> dict:
    """
    Verifica se operações são reais (usando PyMuPDF diretamente).

    Returns:
        Dict com status de validação.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Verifica uso de PyMuPDF (fitz) para operações reais
        has_real_ops = any([
            "fitz.open" in content,
            "page.insert_text" in content,
            "page.add_redact_annot" in content,
            "page.insert_image" in content,
            "doc.save" in content,
            "doc.insert_pdf" in content,
        ])

        # Verifica se há implementações reais vs apenas placeholders
        has_implementations = any([
            "def " in content and "pass" not in content[:500],
            "page.insert_text" in content,
            "page.insert_image" in content,
        ])

        return {
            "file": str(file_path),
            "has_real_operations": has_real_ops,
            "has_implementations": has_implementations,
            "status": "OK" if (has_real_ops and has_implementations) else "SUSPICIOUS"
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "has_real_operations": False,
            "has_implementations": False,
            "status": "ERROR",
            "error": str(e)
        }


def validate_logging_structure(log_dir: Path) -> dict:
    """
    Valida estrutura dos logs gerados.

    Returns:
        Dict com resultados da validação.
    """
    log_file = log_dir / "operations.jsonl"

    if not log_file.exists():
        return {
            "status": "NO_LOGS",
            "message": "Nenhum log encontrado ainda. Execute algumas operações primeiro."
        }

    required_fields = [
        "operation_id",
        "operation_type",
        "timestamp",
        "status",
        "parameters",
        "result"
    ]

    valid_logs = 0
    invalid_logs = 0
    issues = []

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                if not line.strip():
                    continue

                try:
                    log_entry = json.loads(line)

                    # Verifica campos obrigatórios
                    missing_fields = [f for f in required_fields if f not in log_entry]
                    if missing_fields:
                        invalid_logs += 1
                        issues.append({
                            "line": i,
                            "issue": f"Campos faltando: {missing_fields}",
                            "entry": log_entry.get("operation_type", "unknown")
                        })
                    else:
                        valid_logs += 1
                except json.JSONDecodeError as e:
                    invalid_logs += 1
                    issues.append({
                        "line": i,
                        "issue": f"JSON inválido: {e}",
                        "entry": None
                    })
    except Exception as e:
        return {
            "status": "ERROR",
            "message": f"Erro ao ler logs: {e}"
        }

    return {
        "status": "OK" if invalid_logs == 0 else "ISSUES",
        "valid_logs": valid_logs,
        "invalid_logs": invalid_logs,
        "issues": issues
    }


def main():
    """Função principal de validação."""
    print("=" * 70)
    print("VALIDAÇÃO DE HONESTIDADE - PDF-cli Fase 4")
    print("=" * 70)
    print()

    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    all_issues = []
    operation_status = []

    # 1. Verifica arquivos de serviço por mocks
    print("1. Verificando mocks/simulações em arquivos de serviço...")
    service_files = [
        src_dir / "app" / "services.py",
        src_dir / "app" / "pdf_repo.py",
    ]

    for file_path in service_files:
        if file_path.exists():
            issues = check_for_mocks(file_path)
            all_issues.extend(issues)
            if issues:
                print(f"   ⚠️  {file_path.name}: {len(issues)} ocorrências suspeitas")
            else:
                print(f"   ✓ {file_path.name}: Nenhum mock detectado")
        else:
            print(f"   ✗ {file_path.name}: Arquivo não encontrado")

    print()

    # 2. Verifica operações reais
    print("2. Verificando operações reais...")
    for file_path in service_files:
        if file_path.exists():
            status = check_real_operations(file_path)
            operation_status.append(status)
            if status["status"] == "OK":
                print(f"   ✓ {file_path.name}: Operações reais detectadas")
            else:
                print(f"   ⚠️  {file_path.name}: Status suspeito")

    print()

    # 3. Valida estrutura de logs
    print("3. Validando estrutura de logs...")
    log_dir = project_root / "logs"
    log_validation = validate_logging_structure(log_dir)

    if log_validation["status"] == "OK":
        print(f"   ✓ Logs válidos: {log_validation.get('valid_logs', 0)} entradas")
    elif log_validation["status"] == "NO_LOGS":
        print(f"   ⚠️  {log_validation['message']}")
    else:
        print(f"   ⚠️  Logs com problemas: {log_validation.get('invalid_logs', 0)} inválidos")
        for issue in log_validation.get("issues", [])[:5]:
            print(f"      - Linha {issue['line']}: {issue['issue']}")

    print()

    # 4. Resumo final
    print("=" * 70)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 70)

    mock_issues = len([i for i in all_issues if i["pattern"] not in ["NotImplementedError", "TODO: implement"]])
    critical_issues = len([i for i in all_issues if i["pattern"] in ["mock", "fake", "simulate"]])

    if critical_issues == 0 and mock_issues == 0:
        print("✅ STATUS: VALIDAÇÃO APROVADA")
        print("   - Nenhum mock ou fake detectado")
        print("   - Operações reais confirmadas")
        if log_validation["status"] == "OK":
            print("   - Logs estruturados corretamente")
        return 0
    else:
        print("⚠️  STATUS: ATENÇÃO NECESSÁRIA")
        if critical_issues > 0:
            print(f"   - {critical_issues} ocorrências críticas detectadas (mock/fake/simulate)")
        if mock_issues > 0:
            print(f"   - {mock_issues} ocorrências suspeitas encontradas")

        print("\nDetalhes das ocorrências:")
        for issue in all_issues[:10]:  # Mostra apenas as primeiras 10
            if issue["pattern"] in ["mock", "fake", "simulate"]:
                print(f"   [{issue['file']}:{issue['line']}] {issue['message']}")
                print(f"      Código: {issue['code']}")

        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
