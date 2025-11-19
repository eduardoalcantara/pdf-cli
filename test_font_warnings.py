"""Teste direto do sistema de avisos de fontes."""

import sys
sys.path.insert(0, 'src')

from app.pdf_repo import PDFRepository
from core.font_manager import FontManager, FontMatchQuality

# Testar com APIGuide.pdf
pdf_path = 'examples/APIGuide.pdf'

print("="*80)
print("TESTE: Sistema de Avisos de Fontes")
print("="*80)

with PDFRepository(pdf_path) as repo:
    # Extrair fontes
    fonts_dict = repo.extract_fonts()

    print(f"\n📚 Fontes encontradas: {len(fonts_dict)}")
    for font_name in list(fonts_dict.keys())[:3]:
        print(f"   - {font_name}")

    # Extrair textos
    text_objects = repo.extract_text_objects()
    print(f"\n📄 Textos encontrados: {len(text_objects)}")

    # Criar font_manager
    font_manager = FontManager()

    # Simular busca de fonte para uma fonte que provavelmente não existe
    test_font_name = "EAAAAA+SegoeUI"  # Fonte com nome estranho (substituição de fonte)

    print(f"\n🔍 Testando busca de fonte: {test_font_name}")

    font_loaded, font_source = repo.get_font_for_text_object(test_font_name, fonts_dict)

    print(f"   Fonte carregada: {font_loaded.name if font_loaded else 'None'}")
    print(f"   Source: {font_source}")

    # Verificar correspondência
    if font_loaded:
        loaded_font_name = font_loaded.name if hasattr(font_loaded, 'name') else ""
        font_name_matches = (loaded_font_name.lower() in test_font_name.lower() or
                           test_font_name.lower() in loaded_font_name.lower())

        print(f"   Nome corresponde? {font_name_matches}")

        # Determinar qualidade
        if font_source == "extracted" or font_source == "embedded":
            match_quality = FontMatchQuality.EXACT
        elif font_name_matches and font_source in ["system", "cache"]:
            match_quality = FontMatchQuality.EXACT
        elif font_source in ["system", "cache"] and not font_name_matches:
            match_quality = FontMatchQuality.VARIANT
        elif font_source == "fallback":
            match_quality = FontMatchQuality.FALLBACK
        else:
            match_quality = FontMatchQuality.SIMILAR

        print(f"   Qualidade: {match_quality.value}")

        # Registrar no font_manager se não for exata
        if match_quality != FontMatchQuality.EXACT:
            font_manager.add_requirement(
                font_name=test_font_name,
                found_font=loaded_font_name,
                match_quality=match_quality,
                system_path=getattr(font_loaded, '_fontfile', None),
                page=0
            )
            print(f"   ✅ Registrado no font_manager")
        else:
            print(f"   ⏭️  Não registrado (correspondência exata)")
    else:
        # Fonte não encontrada
        font_manager.add_requirement(
            font_name=test_font_name,
            found_font=None,
            match_quality=FontMatchQuality.MISSING,
            page=0
        )
        print(f"   ❌ Fonte não encontrada - registrado como MISSING")

    # Verificar avisos
    print(f"\n📋 Resultado:")
    print(f"   Tem fontes faltantes? {font_manager.has_missing_fonts()}")
    print(f"   Total de requisitos: {len(font_manager.requirements)}")
    print(f"   Total faltantes: {len(font_manager.missing_fonts)}")

    if font_manager.has_missing_fonts():
        print("\n" + font_manager.get_missing_fonts_summary())

print("="*80)
