import json

with open('outputs/boleto_before.json', 'r', encoding='utf-8') as f:
    before = json.load(f)

texts = [t for t in before['text'] if 'ALCAN' in t['content'].upper()]
print(f'Encontrados {len(texts)} objetos com ALCAN')
for i, t in enumerate(texts[:3], 1):
    print(f"{i}. ID: {t.get('id', 'N/A')[:12]}... | Font: {t['font_name']} ({t['font_size']}pt) | Text: '{t['content'][:50]}'")
