"""
Debug detalhado da edição do PyPDF2 para entender por que não está funcionando.
"""

import PyPDF2
import re
from pathlib import Path

pdf_path = "examples/boleto.pdf"
search_term = "ALCANTARA"
new_content = "ALCÂNTARA"
original_text = "LUIZ EDUARDO ALVES DE ALCANTARA"
replacement_text = "LUIZ EDUARDO ALVES DE ALCÂNTARA"

print("="*80)
print("DEBUG: Edição PyPDF2 - Passo a Passo")
print("="*80)

# Ler PDF
with open(pdf_path, "rb") as f:
    reader = PyPDF2.PdfReader(f)
    writer = PyPDF2.PdfWriter()

    # Processar primeira página
    page = reader.pages[0]
    page_num = 0

    print(f"\n📄 Processando página {page_num}...")

    # Obter conteúdo
    content_object = page.get_contents()

    if content_object is None:
        print("❌ Nenhum conteúdo")
    else:
        print(f"✅ Conteúdo encontrado: {type(content_object)}")

        # Extrair stream
        if hasattr(content_object, 'get_data'):
            content_stream = content_object.get_data()
        elif hasattr(content_object, 'getData'):
            content_stream = content_object.getData()
        else:
            content_stream = None

        if content_stream:
            print(f"✅ Stream extraído: {len(content_stream)} bytes")

            # Decodificar
            try:
                content_str = content_stream.decode('utf-8', errors='ignore')
                print(f"✅ Decodificado como UTF-8: {len(content_str)} caracteres")
            except:
                content_str = content_stream.decode('latin-1', errors='ignore')
                print(f"✅ Decodificado como Latin-1: {len(content_str)} caracteres")

            # Verificar se texto original está no stream
            print(f"\n🔍 Buscando '{original_text}' no stream...")
            if original_text in content_str:
                print(f"✅ Texto original encontrado no stream!")
                idx = content_str.find(original_text)
                context = content_str[max(0, idx-100):min(len(content_str), idx+200)]
                print(f"   Contexto:\n{context}")
            else:
                print(f"❌ Texto original NÃO encontrado no stream")
                # Tentar buscar apenas o termo
                if search_term in content_str.upper():
                    print(f"   Mas '{search_term}' encontrado como substring")
                    idx = content_str.upper().find(search_term)
                    context = content_str[max(0, idx-100):min(len(content_str), idx+200)]
                    print(f"   Contexto:\n{context}")

            # Tentar padrões regex
            print(f"\n🔍 Testando padrões regex...")

            escaped_original = re.escape(original_text)
            escaped_replacement = replacement_text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

            # Padrão 1: (texto) Tj
            pattern1 = re.compile(r'\(' + escaped_original + r'\)\s+Tj', re.IGNORECASE)
            matches1 = pattern1.findall(content_str)
            print(f"   Padrão 1 '(...) Tj': {len(matches1)} encontrado(s)")
            if matches1:
                for i, match in enumerate(matches1[:3], 1):
                    print(f"      {i}. {match[:80]}...")

            # Padrão 2: Texto sem parênteses no padrão
            pattern2 = re.compile(r'\(' + escaped_original + r'\)', re.IGNORECASE)
            matches2 = pattern2.findall(content_str)
            print(f"   Padrão 2 '(...)': {len(matches2)} encontrado(s)")
            if matches2:
                for i, match in enumerate(matches2[:3], 1):
                    print(f"      {i}. {match[:80]}...")

            # Tentar substituição
            print(f"\n✏️  Tentando substituição...")
            modified_str = content_str

            if pattern1.search(modified_str):
                print(f"   ✅ Padrão 1 encontrado, substituindo...")
                modified_str = pattern1.sub(f'({escaped_replacement}) Tj', modified_str)
                print(f"   ✅ Substituição realizada")
            elif pattern2.search(modified_str):
                print(f"   ✅ Padrão 2 encontrado, substituindo...")
                modified_str = pattern2.sub(f'({escaped_replacement})', modified_str)
                print(f"   ✅ Substituição realizada")
            else:
                print(f"   ❌ Nenhum padrão encontrado para substituição")

            # Verificar se substituição funcionou
            if replacement_text in modified_str or 'ALCÂNTARA' in modified_str:
                print(f"   ✅ Novo texto encontrado no stream modificado!")
            else:
                print(f"   ❌ Novo texto NÃO encontrado no stream modificado")

            # Verificar diferenças
            if modified_str != content_str:
                print(f"   ✅ Stream foi modificado (diferença: {len(modified_str) - len(content_str)} caracteres)")
            else:
                print(f"   ❌ Stream NÃO foi modificado")

            # Tentar atualizar objeto de conteúdo
            print(f"\n💾 Tentando atualizar objeto de conteúdo...")

            try:
                # Recodificar
                new_stream = modified_str.encode('utf-8')
                print(f"   ✅ Stream recodificado: {len(new_stream)} bytes")

                # Atualizar objeto
                if hasattr(content_object, 'set_data'):
                    print(f"   ✅ Tentando set_data()...")
                    content_object.set_data(new_stream)
                    print(f"   ✅ set_data() executado com sucesso")
                elif hasattr(content_object, 'setData'):
                    print(f"   ✅ Tentando setData()...")
                    content_object.setData(new_stream)
                    print(f"   ✅ setData() executado com sucesso")
                else:
                    print(f"   ❌ Nenhum método de set disponível")

                # Adicionar página ao writer
                writer.add_page(page)
                print(f"   ✅ Página adicionada ao writer")

                # Salvar PDF
                output_path = "examples/boleto_pypdf_debug.pdf"
                with open(output_path, "wb") as f:
                    writer.write(f)
                print(f"   ✅ PDF salvo: {output_path}")

                # Verificar se texto foi modificado no PDF salvo
                print(f"\n🔍 Verificando PDF salvo...")
                with open(output_path, "rb") as f:
                    reader2 = PyPDF2.PdfReader(f)
                    page2 = reader2.pages[0]
                    content2 = page2.get_contents()
                    if content2:
                        stream2 = content2.get_data() if hasattr(content2, 'get_data') else content2.getData()
                        str2 = stream2.decode('utf-8', errors='ignore')
                        if 'ALCÂNTARA' in str2 or replacement_text in str2:
                            print(f"   ✅ Texto modificado encontrado no PDF salvo!")
                        else:
                            print(f"   ❌ Texto modificado NÃO encontrado no PDF salvo")
                            if 'ALCANTARA' in str2:
                                print(f"   ⚠️  Texto original ainda presente")

            except Exception as e:
                print(f"   ❌ Erro ao atualizar: {e}")
                import traceback
                traceback.print_exc()

print("\n" + "="*80)
print("FIM DO DEBUG")
print("="*80)
