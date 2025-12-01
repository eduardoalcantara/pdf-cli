# ISSUE-001: Correção de Emojis e Símbolos Especiais no Comando md-to-pdf

## Status
**Parcialmente Resolvido** | **Prioridade:** Média | **Tipo:** Bug/Melhorias

**Nota:** Implementação concluída, mas limitações do xhtml2pdf impedem renderização completa de emojis e caracteres box-drawing. WeasyPrint oferece melhor suporte quando disponível.

---

## Descrição do Problema

O comando `md-to-pdf` não está convertendo corretamente emojis e símbolos especiais Unicode presentes no arquivo Markdown original. Os emojis são exibidos como caracteres vazios, quadrados ou substituídos por caracteres de substituição no PDF gerado.

### Exemplo do Problema

**Arquivo Markdown de entrada (`exemplo.md`):**
```markdown
## 🏗️ Estrutura de Pacotes

br.jus.pa.tre.basic.basicPersistence.pack.longIdNameFieldEntities/

├── repository/
│   └── LongIdNameRepository.java
├── service/
│   ├── AbstractLongIdNameService.java
│   └── RsqlSpecificationVisitor.java
```

**Resultado no PDF:**
- O emoji 🏗️ (construção) não é renderizado ou aparece como um quadrado vazio
- Outros emojis e símbolos Unicode também podem não ser exibidos corretamente

---

## Comportamento Esperado

1. **Emojis Unicode** (🏗️, ✅, ❌, 📝, etc.) devem ser renderizados corretamente no PDF
2. **Símbolos especiais** (→, ←, ↑, ↓, ✓, ✗, etc.) devem ser preservados
3. **Caracteres Unicode** de diferentes scripts (chinês, japonês, árabe, etc.) devem ser suportados
4. **Compatibilidade multiplataforma** deve ser mantida (Windows e Linux)

---

## Análise Técnica

### Causa Raiz Provável

1. **Fonte não suporta Unicode:**
   - O CSS padrão usa `"DejaVu Sans", Arial, sans-serif`
   - Arial pode não ter suporte completo para emojis
   - DejaVu Sans pode não incluir todos os emojis

2. **Bibliotecas de conversão:**
   - **WeasyPrint:** Pode ter limitações com emojis dependendo das fontes disponíveis no sistema
   - **xhtml2pdf:** Pode não suportar adequadamente caracteres Unicode complexos

3. **Encoding:**
   - Embora o HTML seja gerado com `<meta charset="UTF-8">`, as fontes usadas no PDF podem não incluir os glifos necessários

### Arquivos Afetados

- `src/app/md_converter.py` (linhas 36-179: DEFAULT_CSS, linhas 256-500: função de conversão)
- `src/cli/commands.py` (comando `cmd_md_to_pdf`)

---

## Soluções Propostas

### Solução 1: Adicionar Fontes com Suporte a Emojis (Recomendada)

**Descrição:** Incluir fontes que suportam emojis no CSS padrão e garantir que sejam embutidas no PDF.

**Implementação:**
1. Adicionar fontes com suporte a emojis no `DEFAULT_CSS`:
   ```css
   @font-face {
       font-family: "Noto Color Emoji";
       src: url("path/to/NotoColorEmoji.ttf");
   }

   body {
       font-family: "Noto Color Emoji", "DejaVu Sans", Arial, sans-serif;
   }
   ```

2. **Limitação:** Requer distribuir arquivos de fonte ou usar fontes do sistema

**Prós:**
- Renderização completa de emojis
- Mantém qualidade visual

**Contras:**
- Aumenta tamanho do executável se fontes forem embutidas
- Dependência de fontes do sistema ou arquivos externos

---

### Solução 2: Converter Emojis para Imagens

**Descrição:** Substituir emojis no HTML por imagens SVG ou PNG antes da conversão.

**Implementação:**
1. Criar função para detectar emojis no HTML gerado
2. Substituir cada emoji por uma tag `<img>` com SVG inline ou referência a imagem
3. Usar biblioteca como `emoji` para obter representações visuais

**Prós:**
- Funciona independente de fontes
- Controle total sobre aparência

**Contras:**
- Mais complexo de implementar
- Pode afetar layout (tamanho das imagens)
- Requer biblioteca adicional (`emoji`)

---

### Solução 3: Usar Fontes do Sistema com Fallback

**Descrição:** Detectar fontes disponíveis no sistema que suportam emojis e usá-las no CSS.

**Implementação:**
1. Detectar fontes do sistema (Windows: Segoe UI Emoji, Linux: Noto Color Emoji)
2. Ajustar `DEFAULT_CSS` dinamicamente baseado na plataforma
3. Adicionar fallback para múltiplas fontes

**Prós:**
- Não requer distribuir fontes
- Funciona bem em ambos OS

**Contras:**
- Depende de fontes do sistema (pode variar)
- Pode não funcionar em sistemas sem fontes de emoji instaladas

---

### Solução 4: Usar Biblioteca Especializada

**Descrição:** Usar biblioteca Python que converte emojis para representações compatíveis.

**Implementação:**
1. Adicionar `emoji` ou `emoji2text` para substituir emojis por texto descritivo
2. Ou usar `pillow` para renderizar emojis como imagens

**Prós:**
- Solução robusta e testada
- Pode funcionar como fallback

**Contras:**
- Dependência adicional
- Pode perder aparência visual original

---

## Recomendação

**Solução Híbrida (Solução 1 + 3):**

1. **Prioridade 1:** Atualizar `DEFAULT_CSS` para incluir fontes de emoji do sistema:
   ```css
   body {
       font-family:
           "Segoe UI Emoji",           /* Windows */
           "Apple Color Emoji",        /* macOS */
           "Noto Color Emoji",         /* Linux */
           "DejaVu Sans",
           Arial,
           sans-serif;
   }
   ```

2. **Prioridade 2:** Adicionar detecção de plataforma para ajustar fontes automaticamente

3. **Prioridade 3 (Opcional):** Implementar fallback para converter emojis não suportados em texto descritivo ou imagens

---

## Testes Necessários

### Casos de Teste

1. **Emojis básicos:**
   ```markdown
   ## 🏗️ Estrutura
   ✅ Sucesso
   ❌ Erro
   📝 Nota
   ```

2. **Símbolos especiais:**
   ```markdown
   → Seta direita
   ← Seta esquerda
   ✓ Check
   ✗ X
   ```

3. **Emojis em diferentes contextos:**
   - Em títulos (h1, h2, h3)
   - Em parágrafos
   - Em listas
   - Em blocos de código (não deve converter)

4. **Compatibilidade multiplataforma:**
   - Testar em Windows 10/11
   - Testar em Linux (Ubuntu/Debian)
   - Verificar com WeasyPrint e xhtml2pdf

---

## Arquivos de Exemplo

**Arquivo de teste sugerido:** `examples/markdown_emoji_test.md`

```markdown
# Teste de Emojis e Símbolos

## 🏗️ Estrutura de Pacotes

### ✅ Componentes Funcionais

- 📝 Documentação
- 🔧 Ferramentas
- 🚀 Deploy

### ❌ Problemas Conhecidos

→ Seta direita
← Seta esquerda
↑ Seta para cima
↓ Seta para baixo

✓ Check mark
✗ X mark
★ Estrela
```

---

## Dependências Adicionais (se necessário)

- `emoji` (opcional, para conversão de emojis)
- Fontes de emoji do sistema (não requer instalação adicional)

---

## Referências

- [Unicode Emoji](https://unicode.org/emoji/)
- [WeasyPrint Fonts](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#fonts)
- [xhtml2pdf Unicode Support](https://xhtml2pdf.readthedocs.io/)
- [CSS Font Fallbacks](https://developer.mozilla.org/en-US/docs/Web/CSS/font-family)

---

## Histórico

- **2025-01-XX:** Issue criada - Problema identificado com emojis não sendo renderizados no PDF
- **2025-01-XX:** **IMPLEMENTADO** - Solução Híbrida aplicada:
  - Criada função `_get_default_css()` que detecta a plataforma e inclui fontes de emoji apropriadas
  - Windows: `"Segoe UI Emoji", "Segoe UI Symbol"`
  - macOS: `"Apple Color Emoji"`
  - Linux: `"Noto Color Emoji", "Noto Emoji"`
  - CSS padrão atualizado para usar fontes de emoji como prioridade no `font-family`
  - Funções de conversão atualizadas para usar CSS dinâmico
  - Adicionado suporte a fontes monospace para caracteres box-drawing (├──, └──, │)
  - Criada função `_process_html_for_special_chars()` para preservar estruturas de diretórios
  - Arquivo de teste criado: `examples/markdown_emoji_test.md` com estrutura de diretórios
- **2025-01-XX:** **LIMITAÇÃO IDENTIFICADA** - xhtml2pdf não renderiza corretamente:
  - Emojis aparecem como quadrados pretos (■)
  - Caracteres box-drawing (├──, └──, │) são convertidos incorretamente
  - Limitação conhecida do xhtml2pdf com Unicode complexo
  - **Recomendação:** Usar WeasyPrint quando disponível para melhor suporte a Unicode
- **Status:** Parcialmente Resolvido (implementação completa, mas limitada pela biblioteca)

---

## Notas Adicionais

- Este problema não afeta a funcionalidade básica do comando, mas impacta a fidelidade visual do PDF gerado
- A correção deve manter compatibilidade com ambos os mecanismos de conversão (WeasyPrint e xhtml2pdf)
- Considerar adicionar opção `--emoji-fallback` para permitir ao usuário escolher o comportamento
