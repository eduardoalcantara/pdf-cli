# ESPECIFICACOES-FASE-9-NOVA-COMANDO-MD-TO-PDF.md

## Projeto: PDF-cli — Novo Comando `md-to-pdf` para Conversão de Markdown

**Objetivo Geral:**
Agregar ao PDF-cli uma função prática e robusta de conversão de arquivos Markdown (`.md`) para PDF, com visualização fiel, fácil uso e integração com demais comandos do CLI.

---

## REQUISITOS FUNCIONAIS

### 1. **Novo comando: `md-to-pdf`**
- O comando deve ser chamado assim no CLI:
  ```
  pdf-cli md-to-pdf entrada.md saida.pdf
  ```
- Deve aceitar dois argumentos obrigatórios:
  - Arquivo markdown de entrada (`.md`)
  - Arquivo PDF de saída (`.pdf`)

### 2. **Conversão Markdown → PDF**
- O comando deve:
  - Ler o conteúdo markdown do arquivo informado.
  - Converter o markdown para HTML fiel (incluindo listas, cabeçalhos, links, imagens locais, tabelas, itálico/negrito, blocos de código).
  - Converter o HTML resultante diretamente para PDF, mantendo a formatação visual.
  - Gerar o PDF de saída no caminho especificado, sobrescrevendo se já existir.

### 3. **Requisitos de formatação e estilo**
- O PDF produzido deve ter formatação básica (margens, fontes, estilos de cabeçalho, código, links).
- Se possível, incluir um CSS padrão amigável (opcional: permitir argumento `--css caminho.css` para folhas de estilo customizadas).
- Imagens linkadas localmente no markdown devem ser incluídas no PDF (se disponíveis).

### 4. **Dependências**
- Utilizar bibliotecas Python confiáveis e portáveis:
  - Recomendado: [`markdown2`](https://github.com/trentm/python-markdown2) para conversão em HTML.
  - [`weasyprint`](https://weasyprint.org/) ou [`pdfkit`](https://pypi.org/project/pdfkit/) para HTML → PDF.
  - (Opcional) Suporte a Pandoc via subprocess se preferir integração externa.

### 5. **Exemplo prático no help**
- O help do comando (`pdf-cli md-to-pdf --help`) deve incluir:
  - Descrição clara.
  - Exemplo de uso típico.
  - Explicação das limitações/capacidades (ex: imagens locais, tabelas, extensões markdown avançadas).

### 6. **Logs e erros**
- O comando deve registrar logs básicos de sucesso/falha.
- Relatar claramente:
  - Se o arquivo de entrada não existe ou não é markdown.
  - Se não é possível criar o PDF no destino.
  - Se ocorrer erro de conversão.

### 7. **Testes**
- Testar conversão de exemplos reais:
  - Markdown simples (títulos, listas).
  - Markdown com imagens locais e remotas.
  - Markdown com tabelas e blocos de código.
- Gerar os arquivos PDF resultantes em `/outputs/` e documentar os testes no relatório de entrega.

---

## CHECKLIST DE ENTREGA

- Novo comando `md-to-pdf` registrado no CLI, help e documentação.
- Dependências novas informadas no README/install.
- Exemplo funcional de conversão em `/examples/markdown.md`.
- PDF gerado para cada exemplo, passível de auditoria.
- Código testado e robusto para erros comuns.

---

**Com este comando, o PDF-cli amplia sua utilidade para documentação, relatórios e automação, mantendo a robustez esperada em ambiente institucional.**
