# Instruções: Como Usar WeasyPrint no Windows

## Situação Atual

O WeasyPrint **não funciona no Windows** sem instalar bibliotecas GTK+ do sistema. O erro típico é:

```
cannot load library 'libgobject-2.0-0': error 0x7e
```

## Por Que Isso Acontece?

WeasyPrint depende de bibliotecas nativas (Cairo, Pango, GDK-PixBuf) que não vêm com Python. No Windows, essas bibliotecas precisam ser instaladas separadamente.

## Soluções

### Opção 1: Usar WSL (Windows Subsystem for Linux) - RECOMENDADO

**Vantagens:**
- ✅ Funciona perfeitamente
- ✅ Dependências fáceis de instalar
- ✅ Melhor suporte a Unicode

**Passos:**

1. **Instalar WSL (se não tiver):**
   ```powershell
   wsl --install
   ```

2. **Abrir WSL e navegar para o projeto:**
   ```bash
   cd /mnt/d/proj/pdf-cli
   ```

3. **Executar script de teste:**
   ```bash
   chmod +x scripts/test_weasyprint_unicode.sh
   ./scripts/test_weasyprint_unicode.sh
   ```

4. **Ou usar o comando diretamente:**
   ```bash
   python3 src/pdf_cli.py md-to-pdf examples/markdown_emoji_test.md examples/emoji_test_weasyprint.pdf --verbose
   ```

---

### Opção 2: Instalar GTK+ no Windows (AVANÇADO)

**Requisitos:**
- MSYS2 ou pacotes GTK+ para Windows
- Configuração de variáveis de ambiente

**Passos:**

1. **Instalar MSYS2:**
   - Baixar de: https://www.msys2.org/
   - Instalar e atualizar: `pacman -Syu`

2. **Instalar GTK+ e dependências:**
   ```bash
   pacman -S mingw-w64-x86_64-gtk3
   pacman -S mingw-w64-x86_64-python-cairo
   pacman -S mingw-w64-x86_64-python-gobject
   ```

3. **Configurar variáveis de ambiente:**
   - Adicionar `C:\msys64\mingw64\bin` ao PATH

4. **Reinstalar WeasyPrint:**
   ```bash
   pip uninstall weasyprint
   pip install weasyprint
   ```

**⚠️ Nota:** Esta opção é complexa e pode causar conflitos. Recomendado apenas para usuários avançados.

---

### Opção 3: Usar xhtml2pdf (ATUAL - FALLBACK)

**Status:** ✅ **Já implementado e funcionando**

O sistema atual usa **xhtml2pdf como fallback** quando WeasyPrint não está disponível. Isso garante que o comando `md-to-pdf` sempre funcione, mesmo no Windows.

**Limitações conhecidas:**
- ❌ Emojis podem aparecer como quadrados pretos
- ❌ Caracteres box-drawing podem ser renderizados incorretamente
- ✅ Funciona sem dependências externas
- ✅ Funciona em Windows e Linux

---

## Comparação: WeasyPrint vs xhtml2pdf

| Característica | WeasyPrint | xhtml2pdf |
|---------------|------------|-----------|
| **Windows (sem GTK)** | ❌ Não funciona | ✅ Funciona |
| **Linux** | ✅ Funciona bem | ✅ Funciona |
| **Emojis** | ✅ Renderiza corretamente | ❌ Quadrados pretos |
| **Box-drawing** | ✅ Preserva caracteres | ❌ Converte incorretamente |
| **Qualidade CSS** | ✅ Excelente | ⚠️ Básica |
| **Dependências** | ❌ Requer GTK/Cairo | ✅ Apenas Python |
| **Tamanho executável** | ⚠️ +10-20 MB | ✅ Menor |

---

## Teste no Linux/WSL

Para testar WeasyPrint com símbolos Unicode complexos:

```bash
# No WSL ou Linux
cd /mnt/d/proj/pdf-cli  # ou caminho do projeto
chmod +x scripts/test_weasyprint_unicode.sh
./scripts/test_weasyprint_unicode.sh
```

O script irá:
1. Verificar se WeasyPrint está instalado
2. Instalar dependências do sistema se necessário
3. Converter `examples/markdown_emoji_test.md` para PDF
4. Verificar se emojis e caracteres especiais foram preservados

---

## Recomendação Final

**Para desenvolvimento/testes:**
- ✅ Usar WSL para testar WeasyPrint
- ✅ Manter xhtml2pdf como fallback para Windows

**Para distribuição:**
- ✅ Incluir ambos (WeasyPrint + xhtml2pdf)
- ✅ WeasyPrint funcionará no Linux
- ✅ xhtml2pdf funcionará no Windows
- ✅ Fallback automático garante funcionamento sempre

---

**Data:** 2025-01-XX
**Status:** Documentado - WeasyPrint requer GTK+ no Windows
