# ESPECIFICACOES-FASE-10-PDF-TO-MD-HTML-MULTIPLATAFORMA.md

## Projeto: PDF-cli — Fase 10: Comandos `pdf-to-md` e `pdf-to-html` multiplataforma

**Objetivo Geral:**
Adicionar ao PDF-cli dois comandos para exportar conteúdo de arquivos PDF para Markdown (`.md`) e HTML (`.html`), com total compatibilidade e instalação simples tanto em Windows quanto Linux.

---

## REQUISITOS FUNCIONAIS

### 1. **Novo comando: `pdf-to-md`**
- Sintaxe:
  ```
  pdf-cli pdf-to-md entrada.pdf saida.md
  ```
- Argumentos:
  - `entrada.pdf`: Arquivo PDF de origem
  - `saida.md`: Arquivo Markdown de destino

- Funcionalidade:
  - Extrair texto do PDF por página usando biblioteca multiplataforma
  - Preservar estrutura: títulos, listas, links, imagens, tabelas simples
  - Converter para markdown compatível com Github, VSCode e sites institucionais
  - Exportar para arquivo `.md`

### 2. **Novo comando: `pdf-to-html`**
- Sintaxe:
  ```
  pdf-cli pdf-to-html entrada.pdf saida.html
  ```
- Argumentos:
  - `entrada.pdf`: Arquivo PDF de origem
  - `saida.html`: Arquivo HTML de destino

- Funcionalidade:
  - Extrair texto, imagens e links estruturados por página
  - Gerar HTML básico com tags para h1-h6, p, ul/ol, a, img, table
  - Exportar para `.html` pronto para visualização web e processamento por IA

### 3. **Bibliotecas obrigatórias (instaláveis via pip)**
Use **apenas** bibliotecas abaixo, que funcionam em ambos Windows e Linux:
- **Para extração de texto/imagens do PDF:**
  - [`pymupdf`](https://github.com/pymupdf/PyMuPDF) (`pip install pymupdf`)
  - [`pdfplumber`](https://github.com/jsvine/pdfplumber) (`pip install pdfplumber`)
- **Para manipulação e conversão HTML/markdown:**
  - [`markdownify`](https://github.com/matthewwithanm/python-markdownify) (`pip install markdownify`)
  - [`beautifulsoup4`](https://www.crummy.com/software/BeautifulSoup/) (`pip install beautifulsoup4`)
- **Não exigir instalação extra/manual de binários externos** (pandoc, chromium, etc.)

### 4. **Regras de Formatação**
- Preservar ao máximo estrutura visual do PDF (se possível).
- Avisar no help/README sobre limitações na conversão de elementos gráficos/tabelas complexas.
- Testar sempre os arquivos convertidos em ambos OS para garantir compatibilidade.

### 5. **Help e exemplos práticos**
- Help detalhado por comando, incluindo exemplos com arquivos de `/examples`.
- Documentar limitações e diferenciais da conversão por sistema operacional.

### 6. **Logs e erros**
- Mensagens claras e multiplataforma (sem dependências de terminal/cores).
- Registrar logs básicos das conversões e apontar erros específicos (arquivo não encontrado, PDF corrompido, problemas de permissão).

---

## CHECKLIST DE ENTREGA

- Comandos `pdf-to-md` e `pdf-to-html` implementados e testados em Windows e Linux.
- Dependências listadas **exclusivamente** para instalação via `pip` no README.
- Arquivos de saída testados em ambos OS e salvos em `/outputs/`, validados por exemplos reais.
- Help atualizado e multiplataforma.
- README com instruções de instalação e troubleshooting para ambos OS.
- Logs ou relatórios de erros padronizados, sem dependência de terminal.

---

**Esta fase garante que o PDF-cli será multiplataforma, fácil para o usuário técnico e institucional, e robusto para automações e integração com IA.**
