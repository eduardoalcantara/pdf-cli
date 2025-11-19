# Diagnóstico Completo: Problema de Fontes no PDF-CLI

**Data**: 19/11/2025
**Fase**: 5 - Fallback Inteligente PyMuPDF + pypdf
**Status**: 🔴 PROBLEMA CRÍTICO IDENTIFICADO

---

## 1. RESUMO DO PROBLEMA

Quando editamos texto em um PDF, as fontes originais são alteradas para Helvetica, resultando em:
- **Tamanho visual menor** (letras menores que o original)
- **Largura diferente** (texto mais estreito ou mais largo)
- **Perda de fidelidade visual** (até 20% de diferença)

### Exemplo Real (boleto.pdf):
```
ORIGINAL:  ArialMT (6pt) - Altura: 7.80pt, Largura: 131.93pt
EDITADO:   Helvetica (6pt) - Altura: 8.24pt, Largura: 113.36pt
DIFERENÇA: Altura +5.7%, Largura -14.1%
```

---

## 2. ANÁLISE TÉCNICA

### 2.1. O Que Está Funcionando ✅

1. **Extração de fontes**: O sistema identifica corretamente as fontes do PDF original
   - ArialMT
   - ArialNarrow-Bold
   - ArialNarrow

2. **Busca de fontes no sistema**: O sistema encontra as fontes instaladas no Windows
   - ArialMT → `C:\Windows\Fonts\arial.ttf`
   - ArialNarrow-Bold → `C:\Windows\Fonts\ARIALNB.TTF`
   - ArialNarrow → `C:\Windows\Fonts\ARIALN.TTF`

3. **Carregamento de fontes**: O PyMuPDF consegue carregar as fontes do sistema
   ```python
   font = fitz.Font(fontfile="C:\\Windows\\Fonts\\arial.ttf")
   # Resultado: font.name = "ArialMT Regular"
   ```

### 2.2. O Que NÃO Está Funcionando ❌

**PROBLEMA PRINCIPAL**: A fonte carregada do sistema **não está sendo embeddada corretamente** no PDF durante a edição.

#### Fluxo Atual (INCORRETO):
```
1. Carregar fonte do sistema ✅
   font = fitz.Font(fontfile="arial.ttf")

2. Tentar embeddar na página ⚠️
   page.insert_font(fontname="ArialMT", fontfile="arial.ttf")
   # Retorna xref, mas não garante uso correto

3. Inserir texto ❌
   page.insert_text(..., fontname="ArialMT")
   # PyMuPDF NÃO encontra "ArialMT" embeddado
   # Faz fallback automático para Helvetica
```

#### Por Que Falha:
1. **`page.insert_font()` não garante que a fonte seja usável**
   - O método retorna um `xref` (número de referência do objeto)
   - Mas o `fontname` que passamos pode não ser o nome correto para uso em `insert_text()`

2. **`insert_text()` não usa o fontname embeddado**
   - Quando chamamos `insert_text(fontname="ArialMT")`, o PyMuPDF procura por "ArialMT" nas fontes **padrão** do PyMuPDF
   - Não procura nas fontes embeddadas via `insert_font()`
   - Como "ArialMT" não é uma fonte padrão do PyMuPDF, faz fallback para "Helvetica"

3. **Desconexão entre `insert_font` e `insert_text`**
   - `insert_font` embedda a fonte no PDF (objeto de fonte)
   - `insert_text` não sabe usar essa fonte embeddada
   - Falta uma "ponte" entre os dois métodos

---

## 3. EVIDÊNCIAS

### 3.1. Debug de Fontes (test_debug_fonts.py)
```
🔤 Fonte: ArialMT
   ✓ Fonte carregada: ArialMT Regular
   ✓ Fonte source: system  ← Fonte encontrada no sistema

📄 Texto: LUIZ EDUARDO ALVES DE ALCANTARA
   Fonte: ArialMT
   Tamanho: 6pt
   Altura: 7.80pt (proporção 1.30)
```

### 3.2. Resultado Após Edição
```
Fonte usada: ArialMT Regular (extraída (ArialMT))  ← Diz que usou ArialMT
Mas no PDF final: Helvetica                          ← Na verdade usou Helvetica
```

### 3.3. Teste Direto de Embeddagem (test_embed_arialmt.py)
- **Funcionou** quando testado isoladamente
- **Falhou** no fluxo completo de edição
- Indica problema de **integração**, não de capacidade

---

## 4. CAUSA RAIZ

O PyMuPDF tem **duas APIs separadas para fontes**:

### API 1: Fontes Padrão (Built-in)
```python
# Fontes que o PyMuPDF conhece nativamente
font = fitz.Font("helv")  # Helvetica
font = fitz.Font("hebo")  # Helvetica Bold
font = fitz.Font("times") # Times
# Essas funcionam diretamente com insert_text()
```

### API 2: Fontes Customizadas (Externas)
```python
# Fontes carregadas de arquivos
font = fitz.Font(fontfile="arial.ttf")
# Essas NÃO funcionam diretamente com insert_text()
# Precisam ser embeddadas primeiro com insert_font()
# E depois referenciadas pelo nome CORRETO
```

**PROBLEMA**: Não estamos usando o nome correto após embeddar!

---

## 5. SOLUÇÕES POSSÍVEIS

### Opção 1: Usar `TextWriter` ao invés de `insert_text()` ⭐ RECOMENDADA
```python
# TextWriter suporta fontes customizadas diretamente
tw = fitz.TextWriter(page.rect)
tw.append(
    pos=(x, y),
    text="ALCÂNTARA",
    font=font,  # Usa objeto Font diretamente, não nome!
    fontsize=6
)
tw.write_text(page)
```

**Vantagens**:
- Usa o objeto `Font` diretamente (não precisa de nome)
- Suporta fontes customizadas nativamente
- Mais controle sobre posicionamento

**Desvantagens**:
- API diferente de `insert_text()`
- Requer refatoração do código atual

### Opção 2: Descobrir o Nome Correto da Fonte Embeddada
```python
# Após embeddar
xref = page.insert_font(fontname="ArialMT", fontfile="arial.ttf")

# Descobrir o nome real usado internamente
# (pode ser diferente de "ArialMT")
font_name_real = page.get_fonts()[xref]['name']  # Ex: "F1", "F2"

# Usar nome real no insert_text
page.insert_text(..., fontname=font_name_real)
```

**Vantagens**:
- Menos refatoração
- Mantém API atual

**Desvantagens**:
- Complexo descobrir nome correto
- Pode variar entre documentos

### Opção 3: Usar Fontes Padrão com Ajuste de Tamanho ⚠️ PALIATIVO
```python
# Aceitar que vamos usar Helvetica
# Mas ajustar tamanho para preservar altura visual
original_height = 7.80  # ArialMT
adjusted_size = original_height / 1.2  # Proporção Helvetica
# adjusted_size ≈ 6.5pt ao invés de 6pt
```

**Vantagens**:
- Simples de implementar
- Já parcialmente implementado

**Desvantagens**:
- Não preserva fonte original
- Apenas minimiza diferença visual
- Largura ainda será diferente

---

## 6. RECOMENDAÇÃO FINAL

### Implementar Opção 1: TextWriter

**Justificativa**:
1. É a solução **correta** e **definitiva**
2. Suporta fontes customizadas **nativamente**
3. Melhor controle de posicionamento
4. API oficial do PyMuPDF para texto avançado

**Plano de Ação**:
1. Refatorar `_edit_text_all_occurrences` para usar `TextWriter`
2. Manter objeto `Font` carregado (não converter para nome)
3. Usar `tw.append(font=font_object)` ao invés de `insert_text(fontname=string)`
4. Testar com todos os PDFs de exemplo
5. Validar preservação de fontes

**Estimativa**: 2-3 horas de trabalho

---

## 7. PRÓXIMOS PASSOS

1. ✅ Diagnóstico completo (ESTE DOCUMENTO)
2. ⏳ Implementar solução com TextWriter
3. ⏳ Testar em todos os PDFs de exemplo
4. ⏳ Atualizar relatório de Fase 5
5. ⏳ Documentar limitações (se houver)

---

## 8. CONCLUSÃO

O problema **NÃO é de capacidade** do PyMuPDF ou das fontes do sistema.
O problema é de **integração** entre `insert_font()` e `insert_text()`.

A solução é usar **`TextWriter`**, que foi projetado para trabalhar com fontes customizadas.

**Status Atual**: 🔴 BLOQUEADO - Aguardando implementação de TextWriter
**Prioridade**: 🔥 CRÍTICA - Impacta fidelidade visual de todas as edições

---

**Elaborado por**: Cursor IDE (AI Assistant)
**Revisado**: Pendente aprovação do supervisor
