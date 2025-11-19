"""Teste com fonte SegoeUI."""

import sys
sys.path.insert(0, 'src')

from app.pdf_repo import PDFRepository

repo = PDFRepository('examples/APIGuide.pdf')
objs = repo.extract_text_objects()

# Encontrar textos que usam SegoeUI
segoe_objs = [o for o in objs if 'SegoeUI' in o.font_name or o.font_name in ['SegoeUI', 'SegoeUI-Light', 'SegoeUI-Bold']]

print(f"Textos com fonte SegoeUI: {len(segoe_objs)}")
if segoe_objs:
    sample = segoe_objs[0]
    print(f"\nPrimeiro exemplo:")
    print(f"  Página: {sample.page}")
    print(f"  Fonte: {sample.font_name}")
    print(f"  Conteúdo: \"{sample.content[:60]}...\"")
    print(f"\nUse este texto para testar:")
    search_term = sample.content.split()[0] if sample.content.split() else sample.content[:10]
    print(f"  --content \"{search_term}\"")
