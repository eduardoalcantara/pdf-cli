"""Verifica se as posições mudam após edição."""
import json

with open('outputs/boleto_test_stable_ids2.json', 'r', encoding='utf-8') as f:
    before = json.load(f)
with open('outputs/boleto_after_stable2.json', 'r', encoding='utf-8') as f:
    after = json.load(f)

# Extrair todos os textos
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

print(f"ANTES: {len(b_alc)} objetos")
print(f"DEPOIS: {len(a_alc)} objetos")
print()

# Comparar por posição aproximada (tolerância de 1 pixel)
for i, b in enumerate(b_alc[:3], 1):
    print(f"Objeto {i} ANTES:")
    print(f"  ID: {b['id'][:16]}...")
    print(f"  Pos: ({b['x']:.2f}, {b['y']:.2f})")
    print(f"  Size: {b['width']:.2f}×{b['height']:.2f}")
    print(f"  Font: {b['font_name']} ({b['font_size']}pt)")
    print(f"  Content: '{b['content'][:50]}'")

    # Buscar por posição aproximada
    matches = [a for a in a_alc if abs(a['x'] - b['x']) < 1.0 and abs(a['y'] - b['y']) < 1.0]
    if matches:
        a = matches[0]
        print(f"\n  DEPOIS (encontrado por posição):")
        print(f"  ID: {a['id'][:16]}...")
        print(f"  Pos: ({a['x']:.2f}, {a['y']:.2f})")
        print(f"  Size: {a['width']:.2f}×{a['height']:.2f}")
        print(f"  Font: {a['font_name']} ({a['font_size']}pt)")
        print(f"  Content: '{a['content'][:50]}'")
        if b['font_name'] != a['font_name']:
            print(f"  ⚠️  FONTE ALTERADA: {b['font_name']} → {a['font_name']}")
        else:
            print(f"  ✓ Fonte preservada")
    else:
        print(f"\n  ⚠️  NÃO ENCONTRADO no arquivo depois")
    print()
