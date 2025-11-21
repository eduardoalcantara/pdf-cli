**Prompt para Cursor IDE — Implementação da FASE 10: Comandos Multiplataforma `pdf-to-md` e `pdf-to-html`**

Implemente os comandos `pdf-to-md` e `pdf-to-html` no PDF-cli seguindo rigorosamente as especificações multiplicataforma abaixo.

## **Requisitos obrigatórios**

1. **Comando `pdf-to-md`**
   - Sintaxe:
     ```
     pdf-cli pdf-to-md entrada.pdf saida.md
     ```
   - Funcionalidade:
     - Extrair texto do PDF usando bibliotecas 100% compatíveis com Windows e Linux (`pymupdf` ou `pdfplumber`).
     - Converter blocos (títulos, listas, links, imagens, parágrafos, tabelas simples) para markdown estruturado, preservando hierarquia e organização visual.
     - Gerar arquivo `.md` pronto para edição ou ingestão por sistemas automatizados.

2. **Comando `pdf-to-html`**
   - Sintaxe:
     ```
     pdf-cli pdf-to-html entrada.pdf saida.html
     ```
   - Funcionalidade:
     - Extrair texto, imagens e links do PDF.
     - Converter e organizar conteúdo em HTML básico com tags corretas (`h1-h6`, `p`, `ul/ol`, `a`, `img`, `table`).
     - Gerar arquivo `.html` leve e funcional.

3. **Dependências obrigatórias (pip only, multiplataforma)**
   - Só utilize:
     - `pymupdf` (`fitz`)
     - `pdfplumber`
     - `markdownify`
     - `beautifulsoup4`
   - Não utilize nem exija instalação de binários externos, browsers, ou comandos fora do Python/pip.
   - Documente as dependências no README do projeto.

4. **Compatibilidade real Windows e Linux**
   - Teste ambos comandos nos dois sistemas operacionais.
   - Gere os outputs nas respectivas pastas `/outputs/` e valide o conteúdo.
   - Mensagens de erro devem ser claras e portáveis (sem dependências de cores/terminals).

5. **Help, exemplos e documentação**
   - Implemente help detalhado por comando (ex: `pdf-cli pdf-to-md --help`) mostrando sintaxe, exemplos e limitações.
   - Use arquivos reais de `/examples/` nos exemplos do help.
   - Explique limitações (tabelas complexas, elementos gráficos especiais) e valor da conversão para automação/IA.

6. **Logs, erros e funcionamento**
   - Gerar logs simples e multiplataforma das operações realizadas.
   - Tratar erros comuns: arquivo não encontrado, PDF corrompido, problemas de permissão e avisos de limitações técnicas.

7. **Checklist e entrega**
   - Não marque nenhuma tarefa como concluída até testar efetivamente em Windows e Linux.
   - Arquive outputs produzidos e logs em `/outputs/` para auditoria.
   - Atualize o README com exemplos e instruções de troubleshooting para ambos OS.

***

## **Regra de ouro**
> “Priorize sempre bibliotecas Python que funcionem por igual em Windows e Linux e que possam ser instaladas por pip, sem artifícios. Assegure que toda documentação, help e exemplos sejam claros, testados e fundamentados em arquivos reais do projeto.”

***

**Execute sem atalhos, testando em ambos OS e informando limitações técnicas de conversão. Transparência e compatibilidade são obrigatórias!**

---
