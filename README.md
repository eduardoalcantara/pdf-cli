# PDF-cli — Ferramenta CLI para Edição Estrutural de PDFs

**PDF-cli** é uma ferramenta de linha de comando robusta e extensível para automação e edição avançada de arquivos PDF, totalmente desenvolvida em Python. Esta ferramenta foi criada para desenvolvedores e power users que desejam editar textos, manipular páginas, extrair metadados ricos e manter layouts visuais precisos de documentos PDF de maneira eficiente e programável.

# Desenvolvimento

- Eduardo Alcântara
- Perplexity (Claude Sonnect 4.5)
- Cursor IDE (Claude, ChatGPT e Composer)

---

## Funcionalidades

- **Editar Conteúdo de Texto**
  Substitua textos em arquivos PDF de forma precisa, automatizada e personalizável via terminal.

- **Ajustar Posição do Texto**
  Modifique manualmente (ou por script) as coordenadas dos objetos de texto, permitindo realinhamento de títulos, legendas e blocos.

- **Exportar Metadados para JSON**
  Extraia os objetos textuais do PDF (inclusive conteúdo, posição, fonte e página) em um arquivo `.json`. Ideal para auditar, localizar, alterar ou utilizar como base para edição reversível/restauração.

- **Substituição de Texto Centralizado**
  Substitua palavras ou frases centralizadas já alinhando automaticamente os espaços antes e depois, mantendo o texto visualmente centralizado em relação à área original.

- **Substituição Sem Quebra de Design**
  Ao editar textos, mantenha o tamanho visual do bloco ajustando com espaços à direita ou esquerda para preservar a diagramação e evitar desalinhamento.

- **Unir (Merge) Vários PDFs**
  Combine múltiplos arquivos PDF em um único documento mantendo a ordem definida pelo usuário.

- **Excluir Páginas do PDF**
  Remova páginas específicas via CLI, seja por número ou intervalo.

---

## Exemplo de Uso CLI
