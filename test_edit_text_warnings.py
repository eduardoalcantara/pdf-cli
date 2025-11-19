"""Teste completo do edit-text com avisos de fontes."""

import sys
sys.path.insert(0, 'src')

from app.services import _edit_text_all_occurrences
import os

pdf_path = 'examples/APIGuide.pdf'
output_path = 'examples/APIGuide_warning_test.pdf'

print("="*80)
print("TESTE: edit-text com Avisos de Fontes")
print("="*80)

# Procurar um texto que use uma fonte específica (Courier)
# Courier aparece na página 6 segundo o list-fonts
search_term = "Courier"  # Vamos procurar texto que contenha "Courier"
new_content = "COURIER_TEST"

try:
    result_path, details = _edit_text_all_occurrences(
        pdf_path=pdf_path,
        output_path=output_path,
        search_term=search_term,
        new_content=new_content,
        create_backup=False,
        prefer_engine="pymupdf",
        strict_fonts=False
    )

    print(f"\n✅ Edição concluída!")
    print(f"   Arquivo: {result_path}")
    print(f"   Ocorrências: {details.get('occurrences_processed', 0)}")

    # Verificar se há avisos de fontes nos detalhes
    if 'font_warnings' in details:
        warnings = details['font_warnings']
        print(f"\n📋 Avisos de Fontes:")
        print(f"   Total fontes: {warnings.get('total_fonts', 0)}")
        print(f"   Fontes faltantes: {warnings.get('missing_fonts', 0)}")
        if warnings.get('has_issues'):
            print(f"   ⚠️  PROBLEMAS DETECTADOS!")

except Exception as e:
    print(f"\n❌ Erro: {e}")
    import traceback
    traceback.print_exc()

print("="*80)
