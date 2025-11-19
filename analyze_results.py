"""Script para analisar resultados dos testes."""
import json
from pathlib import Path
from datetime import datetime

# Verificar logs de auditoria
log_files = sorted(Path("logs").glob("audit_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)

print("=== ANÁLISE DE LOGS DE AUDITORIA ===\n")

for log_file in log_files[:5]:  # Últimos 5 logs
    with open(log_file, 'r', encoding='utf-8') as f:
        log = json.load(f)

    print(f"Arquivo: {log_file.name}")
    print(f"  Operação: {log['operation_type']}")
    print(f"  Input: {log['input_file']}")
    print(f"  Output: {log['output_file']}")
    print(f"  Engine final: {log['final_engine_used']}")
    print(f"  Fallback detectado: {log.get('any_font_fallback', False)}")
    print(f"  Preservação de fonte: {log.get('font_preservation_success', False)}")
    print(f"  Tentativas de engine: {len(log.get('engine_attempts', []))}")

    for i, attempt in enumerate(log.get('engine_attempts', []), 1):
        print(f"    {i}. {attempt['engine']}: sucesso={attempt['success']}, fallback={attempt.get('any_font_fallback', False)}")
        if attempt.get('error'):
            print(f"       Erro: {attempt['error'][:80]}")
    print()

# Verificar JSONs exportados
print("\n=== ANÁLISE DE FONTES ANTES/DEPOIS ===\n")

if Path("outputs/boleto_before.json").exists() and Path("outputs/boleto_after_pymupdf.json").exists():
    with open("outputs/boleto_before.json", 'r', encoding='utf-8') as f:
        before = json.load(f)
    with open("outputs/boleto_after_pymupdf.json", 'r', encoding='utf-8') as f:
        after = json.load(f)

    # Buscar objetos com ALCANTARA/ALCÂNTARA
    before_texts = []
    after_texts = []

    for page_key in before.keys():
        if isinstance(before[page_key], dict) and 'text' in before[page_key]:
            for t in before[page_key]['text']:
                if 'ALCAN' in t.get('content', '').upper():
                    before_texts.append(t)

    for page_key in after.keys():
        if isinstance(after[page_key], dict) and 'text' in after[page_key]:
            for t in after[page_key]['text']:
                if 'ALCÂN' in t.get('content', '').upper() or 'ALCAN' in t.get('content', '').upper():
                    after_texts.append(t)

    print(f"Objetos ANTES: {len(before_texts)}")
    print(f"Objetos DEPOIS: {len(after_texts)}")

    if before_texts and after_texts:
        print("\nComparação de fontes:")
        for i, (b, a) in enumerate(zip(before_texts[:3], after_texts[:3]), 1):
            print(f"\n  Objeto {i}:")
            print(f"    Antes:  {b.get('font_name', 'N/A'):<20} {b.get('font_size', 0)}pt")
            print(f"    Depois: {a.get('font_name', 'N/A'):<20} {a.get('font_size', 0)}pt")
            if b.get('font_name') != a.get('font_name'):
                print(f"    ⚠️  FONTE ALTERADA: {b.get('font_name')} → {a.get('font_name')}")
            elif b.get('font_size') != a.get('font_size'):
                print(f"    ⚠️  TAMANHO ALTERADO: {b.get('font_size')}pt → {a.get('font_size')}pt")
            else:
                print(f"    ✓ Fonte preservada")
