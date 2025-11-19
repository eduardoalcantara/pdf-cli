"""Verifica se o fallback automático preservou as fontes."""
import json

with open('outputs/boleto_final_before2.json', 'r', encoding='utf-8') as f:
    before = json.load(f)
with open('outputs/boleto_detection_after.json', 'r', encoding='utf-8') as f:
    after = json.load(f)

# Extrair textos
b_texts = []
a_texts = []
for v in before.values():
    if isinstance(v, dict) and 'text' in v:
        b_texts.extend(v['text'])
for v in after.values():
    if isinstance(v, dict) and 'text' in v:
        a_texts.extend(v['text'])

# Buscar objetos com ALCANTARA/ALCÂNTARA
b_alc = [t for t in b_texts if 'ALCAN' in t.get('content', '').upper()]
a_alc = [t for t in a_texts if 'ALCÂN' in t.get('content', '').upper() or 'ALCAN' in t.get('content', '').upper()]

print("=== VERIFICAÇÃO DE PRESERVAÇÃO DE FONTES (com fallback automático) ===\n")

# Comparar por posição
for i, b in enumerate(b_alc[:3], 1):
    matches = [a for a in a_alc if abs(a['x'] - b['x']) < 2.0 and abs(a['y'] - b['y']) < 2.0]
    if matches:
        a = matches[0]
        print(f"Objeto {i}:")
        print(f"  ANTES:  {b['font_name']:<25} {b['font_size']}pt")
        print(f"  DEPOIS: {a['font_name']:<25} {a['font_size']}pt")
        if b['font_name'] != a['font_name']:
            print(f"  ⚠️  FONTE ALTERADA: {b['font_name']} → {a['font_name']}")
        else:
            print(f"  ✓ FONTE PRESERVADA!")
        print()
