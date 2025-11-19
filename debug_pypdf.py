"""
Script para investigar como PyPDF2 lida com streams PDF e identificar
os problemas na implementação atual.
"""

import PyPDF2
import re
from pathlib import Path

pdf_path = "examples/boleto.pdf"

print("="*80)
print("INVESTIGAÇÃO: PyPDF2 Streams PDF")
print("="*80)

# Ler PDF
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)

    print(f"\n📄 Total de páginas: {len(reader.pages)}")

    # Analisar primeira página
    page = reader.pages[0]

    print("\n" + "="*80)
    print("PÁGINA 0")
    print("="*80)

    # Verificar conteúdo
    content_object = page.get_contents()

    if content_object is None:
        print("❌ Nenhum conteúdo encontrado")
    else:
        print(f"✅ Conteúdo encontrado: {type(content_object)}")

        # Tentar extrair dados
        try:
            if hasattr(content_object, 'get_data'):
                content_stream = content_object.get_data()
            elif hasattr(content_object, 'getData'):
                content_stream = content_object.getData()
            else:
                print("❌ Não tem método get_data ou getData")
                content_stream = None

            if content_stream:
                print(f"📦 Tamanho do stream: {len(content_stream)} bytes")

                # Verificar se está comprimido
                try:
                    import zlib
                    try:
                        decompressed = zlib.decompress(content_stream)
                        print("✅ Stream está COMPRIMIDO (zlib)")
                        content_stream = decompressed
                    except:
                        print("ℹ️  Stream NÃO está comprimido (zlib)")
                except ImportError:
                    print("⚠️  zlib não disponível para verificar compressão")

                # Tentar decodificar
                try:
                    content_str = content_stream.decode('utf-8', errors='ignore')
                    print(f"✅ Decodificado como UTF-8: {len(content_str)} caracteres")
                except:
                    try:
                        content_str = content_stream.decode('latin-1', errors='ignore')
                        print(f"✅ Decodificado como Latin-1: {len(content_str)} caracteres")
                    except:
                        content_str = content_stream.decode('cp1252', errors='ignore')
                        print(f"✅ Decodificado como CP1252: {len(content_str)} caracteres")

                # Buscar padrões de texto relacionados a "ALCANTARA"
                print("\n" + "-"*80)
                print("BUSCANDO PADRÕES DE TEXTO 'ALCANTARA'")
                print("-"*80)

                # Buscar diferentes padrões
                patterns = [
                    (r'\([^)]*ALCANTARA[^)]*\)\s*Tj', 'Tj (texto simples)'),
                    (r'\[[^\]]*\([^)]*ALCANTARA[^)]*\)[^\]]*\]\s*TJ', 'TJ (array de texto)'),
                    (r'ALCANTARA', 'Texto simples (sem operadores)'),
                    (r'/F\d+\s+\d+\s+Tf', 'Operador de fonte (Tf)'),
                    (r'BT\s+.*?ET', 'Bloco de texto (BT...ET)'),
                ]

                for pattern, desc in patterns:
                    matches = re.findall(pattern, content_str, re.IGNORECASE | re.DOTALL)
                    if matches:
                        print(f"\n✅ Padrão '{desc}': {len(matches)} encontrado(s)")
                        for i, match in enumerate(matches[:3]):  # Mostrar apenas primeiros 3
                            print(f"   Match {i+1}: {match[:100]}...")
                    else:
                        print(f"❌ Padrão '{desc}': Nenhum encontrado")

                # Procurar contexto ao redor de "ALCANTARA" se encontrar
                if 'ALCANTARA' in content_str.upper():
                    idx = content_str.upper().find('ALCANTARA')
                    context = content_str[max(0, idx-200):min(len(content_str), idx+200)]
                    print(f"\n✅ Contexto encontrado ao redor de 'ALCANTARA':")
                    print(f"{context}")
                else:
                    print("\n❌ 'ALCANTARA' não encontrado no stream decodificado")
                    print("   Pode estar em formato binário, comprimido ou em outro objeto")

                # Verificar se há múltiplos objetos de conteúdo
                if hasattr(page, 'get_contents'):
                    try:
                        contents = page['/Contents']
                        if isinstance(contents, list):
                            print(f"\n✅ Múltiplos objetos de conteúdo: {len(contents)}")
                        else:
                            print(f"\nℹ️  Objeto de conteúdo único")
                    except:
                        pass

        except Exception as e:
            print(f"❌ Erro ao processar stream: {e}")
            import traceback
            traceback.print_exc()

print("\n" + "="*80)
print("FIM DA INVESTIGAÇÃO")
print("="*80)
