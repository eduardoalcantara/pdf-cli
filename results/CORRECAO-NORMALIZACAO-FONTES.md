# Correção: Normalização de Nomes de Fontes com Prefixo de Subset

**Data**: 19/11/2025
**Status**: ✅ CORRIGIDO E TESTADO

---

## 1. PROBLEMA IDENTIFICADO

O usuário identificou uma inconsistência entre os dados:
- **`export-objects`** mostrava que textos usavam fontes (ex: `"font_name": "SegoeUI-Bold"`)
- **`list-fonts`** mostrava que as mesmas fontes **não eram usadas** (0 ocorrências)

### Causa Raiz

Os PDFs com fontes **subset** usam prefixos no nome das fontes:
- `extract_fonts()` retorna: `"EAAAAB+SegoeUI-Bold"` (nome completo com prefixo)
- `extract_text_objects()` retorna: `"SegoeUI-Bold"` (nome normalizado)

Quando comparávamos `font_key` (com prefixo) com `text_obj.font_name` (sem prefixo), não havia correspondência, resultando em **0 ocorrências** para todas as fontes.

---

## 2. SOLUÇÃO IMPLEMENTADA

### 2.1. Função de Normalização

Criada função `_normalize_font_name()` em **dois locais**:
1. `src/pdf_cli.py` (para comando `list-fonts`)
2. `src/app/services.py` (para `export-objects --include-fonts`)

```python
def _normalize_font_name(font_name: str) -> str:
    """
    Normaliza o nome da fonte removendo prefixos de subset.

    Os PDFs com fontes subset usam prefixos como "EAAAAB+SegoeUI-Bold",
    mas os objetos de texto extraídos usam apenas "SegoeUI-Bold".
    Esta função remove o prefixo para permitir correspondência correta.

    Exemplos:
        "EAAAAB+SegoeUI-Bold" -> "SegoeUI-Bold"
        "ABCDEF+Times-Roman" -> "Times-Roman"
        "ArialMT" -> "ArialMT"
        "Courier" -> "Courier"
    """
    if not font_name:
        return font_name

    # Padrão: prefixo de subset é sempre seguido de "+"
    if '+' in font_name:
        parts = font_name.split('+', 1)
        if len(parts) > 1:
            return parts[1]  # Retorna tudo depois do "+"

    return font_name
```

### 2.2. Ajustes em `list-fonts` (src/pdf_cli.py)

**Antes:**
```python
font_stats[font_name]["occurrences"] += 1  # Usava nome original
usage = font_stats.get(font_key, {})  # Comparava com chave sem normalização
```

**Depois:**
```python
# Normalizar antes de adicionar às estatísticas
normalized_name = _normalize_font_name(font_name)
font_stats[normalized_name]["occurrences"] += 1

# Normalizar antes de buscar nas estatísticas
normalized_font_name = _normalize_font_name(font_data.name)
usage = font_stats.get(normalized_font_name, {})
```

**Mudanças adicionais:**
- Adicionado campo `normalized_name` no JSON de saída
- Exibição usa nome normalizado (mais legível) no console
- Mantém `name` original no JSON para referência

### 2.3. Ajustes em `export-objects` (src/app/services.py)

**Mesmo padrão aplicado:**
```python
# Normalizar nomes de fontes antes de comparar
normalized_name = _normalize_font_name(text_obj.font_name)
font_stats[normalized_name]["occurrences"] += 1

normalized_font_name = _normalize_font_name(font_data.name)
usage = font_stats.get(normalized_font_name, {})
```

**JSON exportado agora inclui:**
- `name`: Nome original (ex: "EAAAAB+SegoeUI-Bold")
- `normalized_name`: Nome sem prefixo (ex: "SegoeUI-Bold")
- `usage`: Estatísticas corretas baseadas no nome normalizado

---

## 3. TESTES REALIZADOS

### Teste 1: list-fonts com APIGuide.pdf

**Antes da correção:**
```
1. EAAAAB+SegoeUI-Bold ⚠ não embeddada
   Não usada em nenhum objeto de texto extraído  ❌ ERRADO
```

**Depois da correção:**
```
3. SegoeUI-Bold ([Bold]) ⚠ não embeddada
   Usada em: 1419 ocorrência(s)  ✅ CORRETO
   Páginas: 0, 2, 3, 4, 6, ... (+309 mais)
   Tamanhos: 10pt, 12pt, 16pt, 18pt, 22pt, 26pt
```

### Teste 2: export-objects --include-fonts

**Resultado verificado:**
```json
{
  "_fonts": {
    "total_fonts": 6,
    "fonts": [
      {
        "name": "EAAAAB+SegoeUI-Bold",
        "normalized_name": "SegoeUI-Bold",
        "usage": {
          "occurrences": 1419,  ✅ CORRETO (antes era 0)
          "pages": [0, 2, 3, ...],
          "sizes": [10, 12, 16, ...]
        }
      },
      ...
    ]
  }
}
```

### Teste 3: Validação Completa

**Fontes testadas no APIGuide.pdf:**
1. ✅ **Courier**: 2 ocorrências (sem prefixo, funciona igual)
2. ✅ **SegoeUI**: 5425 ocorrências (antes: 0)
3. ✅ **SegoeUI-Bold**: 1419 ocorrências (antes: 0)
4. ✅ **SegoeUI-Italic**: 69 ocorrências (antes: 0)
5. ✅ **SourceCodePro-Regular**: 7250 ocorrências (antes: 0)
6. ✅ **SegoeUI-Light**: 6542 ocorrências (antes: 0)

**Todas as fontes agora mostram estatísticas corretas!**

---

## 4. ARQUIVOS MODIFICADOS

1. **`src/pdf_cli.py`**
   - Adicionada função `_normalize_font_name()`
   - Modificado comando `list-fonts` para normalizar nomes antes de comparar
   - Adicionado campo `normalized_name` no JSON de saída
   - Exibição usa nome normalizado (mais legível)

2. **`src/app/services.py`**
   - Adicionada função `_normalize_font_name()`
   - Modificada função `export_objects()` para normalizar nomes antes de comparar
   - Adicionado campo `normalized_name` no JSON exportado

---

## 5. COMPATIBILIDADE

### Fontes Sem Prefixo
- Fontes sem prefixo (ex: "Courier", "ArialMT") funcionam normalmente
- A função retorna o nome original se não houver "+"

### Fontes com Prefixo
- Prefixos removidos automaticamente para correspondência
- Nome original preservado no campo `name` para referência
- Nome normalizado usado para exibição e estatísticas

---

## 6. RESULTADO FINAL

✅ **Problema resolvido completamente**

- `list-fonts` agora mostra estatísticas corretas
- `export-objects --include-fonts` agora inclui estatísticas corretas
- Compatível com fontes com e sem prefixo
- Nome original preservado para referência técnica
- Nome normalizado usado para exibição e estatísticas

---

## 7. EXEMPLOS DE USO

### Comando: list-fonts
```bash
pdf-cli list-fonts documento.pdf
```

**Saída:**
```
📚 Fontes encontradas no PDF: 6

1. Courier ⚠ não embeddada
   Usada em: 2 ocorrência(s)
   Páginas: 6
   Tamanhos: 9pt

2. SegoeUI ⚠ não embeddada
   Usada em: 5425 ocorrência(s)
   Páginas: 2, 3, 4, 5, 6, ...
   Tamanhos: 10pt, 12pt
```

### Comando: export-objects --include-fonts
```bash
pdf-cli export-objects documento.pdf objetos.json --include-fonts
```

**JSON gerado:**
```json
{
  "_fonts": {
    "total_fonts": 6,
    "fonts": [
      {
        "name": "EAAAAB+SegoeUI-Bold",
        "normalized_name": "SegoeUI-Bold",
        "variants": ["Bold"],
        "embedded": false,
        "usage": {
          "occurrences": 1419,
          "pages": [0, 2, 3, ...],
          "sizes": [10, 12, 16, ...]
        }
      }
    ]
  }
}
```

---

**Status**: ✅ **CORRIGIDO E TESTADO COM SUCESSO**

Todas as fontes agora mostram suas estatísticas de uso corretamente, independentemente de terem ou não prefixos de subset no nome.

---

**Elaborado por**: Cursor IDE (AI Assistant)
**Data**: 19/11/2025
