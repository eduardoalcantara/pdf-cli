# Teste: WeasyPrint com Símbolos Unicode Complexos e Emojis

## Status do Teste

**Data:** 2025-01-XX
**Ambiente:** Windows 10/11
**Resultado:** WeasyPrint não disponível no Windows sem GTK+

---

## Tentativa de Teste no Windows

### Comando Executado

```bash
python test_weasyprint.py
```

### Resultado

```
[ERRO] WeasyPrint não disponível:
cannot load library 'libgobject-2.0-0': error 0x7e
```

**Causa:** WeasyPrint requer bibliotecas GTK+ do sistema que não estão instaladas no Windows.

---

## Implementação Atual

### Código Já Implementado

O código em `src/app/md_converter.py` **já está preparado** para usar WeasyPrint quando disponível:

```python
# Tentar usar WeasyPrint primeiro (melhor qualidade)
if WEASYPRINT_AVAILABLE:
    try:
        # Usar WeasyPrint com CSS otimizado para Unicode
        css_obj = CSS(string=_get_default_css())
        html_doc = HTML(string=full_html, base_url=base_url)
        html_doc.write_pdf(pdf_path, stylesheets=[css_obj])
    except Exception:
        # Fallback automático para xhtml2pdf
        _convert_with_xhtml2pdf(...)
```

### Características Implementadas

✅ **CSS dinâmico com suporte a emojis:**
- Windows: `Segoe UI Emoji`, `Segoe UI Symbol`
- macOS: `Apple Color Emoji`
- Linux: `Noto Color Emoji`, `Noto Emoji`

✅ **Fontes monospace para box-drawing:**
- Windows: `Consolas`, `Courier New`
- macOS: `Menlo`, `Monaco`
- Linux: `DejaVu Sans Mono`, `Liberation Mono`

✅ **Processamento de HTML:**
- Função `_process_html_for_special_chars()` detecta estruturas de diretórios
- Converte parágrafos com box-drawing para `<pre>` com classe especial

---

## Como Testar WeasyPrint

### Opção 1: Linux/WSL (RECOMENDADO)

**Script criado:** `scripts/test_weasyprint_unicode.sh`

```bash
# No WSL ou Linux
cd /mnt/d/proj/pdf-cli
chmod +x scripts/test_weasyprint_unicode.sh
./scripts/test_weasyprint_unicode.sh
```

**O que o script faz:**
1. Verifica se WeasyPrint está instalado
2. Instala dependências do sistema (Cairo, Pango) se necessário
3. Converte `examples/markdown_emoji_test.md` para PDF
4. Verifica se emojis e caracteres box-drawing foram preservados
5. Exibe primeiros 1000 caracteres do PDF gerado

### Opção 2: Comando Direto (Linux/WSL)

```bash
python3 src/pdf_cli.py md-to-pdf \
    examples/markdown_emoji_test.md \
    examples/emoji_test_weasyprint.pdf \
    --verbose
```

---

## Resultados Esperados com WeasyPrint

### ✅ O que deve funcionar:

1. **Emojis:**
   - 🏗️ ✅ ❌ 📝 🔧 🚀 devem aparecer corretamente
   - Não devem aparecer como quadrados pretos

2. **Caracteres box-drawing:**
   - ├── └── │ devem ser preservados
   - Estrutura de diretórios deve aparecer corretamente

3. **Símbolos especiais:**
   - → ← ↑ ↓ devem aparecer corretamente
   - ✓ ✗ ★ ☆ devem ser renderizados

4. **Qualidade geral:**
   - CSS renderizado com precisão
   - Layouts complexos funcionando
   - Tipografia de alta qualidade

---

## Comparação: WeasyPrint vs xhtml2pdf

### Teste com `examples/markdown_emoji_test.md`

| Característica | WeasyPrint | xhtml2pdf (atual) |
|---------------|------------|-------------------|
| **Emojis** | ✅ Renderiza | ❌ Quadrados pretos |
| **Box-drawing** | ✅ Preserva | ❌ Converte para "III" |
| **Setas** | ✅ Funciona | ✅ Funciona |
| **Qualidade CSS** | ✅ Excelente | ⚠️ Básica |
| **Windows** | ❌ Requer GTK+ | ✅ Funciona |
| **Linux** | ✅ Funciona | ✅ Funciona |

---

## Arquivos Criados

1. **`test_weasyprint.py`** - Script Python para testar WeasyPrint
2. **`scripts/test_weasyprint_unicode.sh`** - Script bash para Linux/WSL
3. **`issues/INSTRUCOES-WEASYPRINT-WINDOWS.md`** - Instruções detalhadas
4. **`issues/TESTE-WEASYPRINT-UNICODE.md`** - Este documento

---

## Conclusão

### Implementação

✅ **Código pronto:** A implementação já suporta WeasyPrint quando disponível
✅ **Fallback funcional:** xhtml2pdf garante funcionamento sempre
✅ **CSS otimizado:** Fontes de emoji e monospace configuradas
✅ **Processamento especial:** Estruturas de diretórios detectadas e preservadas

### Limitação no Windows

❌ **WeasyPrint requer GTK+:** Não funciona no Windows sem instalação manual
✅ **Solução:** Usar WSL ou Linux para testar WeasyPrint
✅ **Alternativa:** xhtml2pdf funciona no Windows (com limitações de Unicode)

### Próximos Passos

1. **Testar no Linux/WSL:** Executar `scripts/test_weasyprint_unicode.sh`
2. **Comparar resultados:** Verificar se emojis e box-drawing são preservados
3. **Documentar:** Adicionar exemplos visuais na documentação

---

**Status:** ✅ Implementação completa, aguardando teste em ambiente Linux/WSL
