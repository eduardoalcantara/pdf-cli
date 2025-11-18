# ESPECIFICACOES-INICIAIS-DESENVOLVIMENTO.md

## Projeto: PDF-cli

**Descrição:**
Ferramenta CLI multiplataforma para automação de edição de arquivos PDF: localizar e substituir textos, ajustar posição, extrair/alterar metadados, unir e excluir páginas, exportação/edição via arquivo JSON.

**Paradigma:**
Python 3.8+, modular, SOLID, DDD-lite, testável, extensível.
CLI roteável (subcomandos). Documentação compreensiva. Clean Code.

---

## FASES DO DESENVOLVIMENTO

### Fase 1 — Infraestrutura e CLI Base

- **Objetivos**
  - Estruturar projeto em pastas por responsabilidade.
  - Implementar CLI roteador de comandos (argparse/typer).
  - Criar modelo de configuração e log.

- **Arquivos a gerar:**
  - `pdf_cli.py` (entrypoint/roteador)
  - `app/services.py` (casos de uso/funções core)
  - `app/pdf_repo.py` (infraestrutura/manipulação PDF)
  - `core/models.py` (DTOs, identificadores de objeto)
  - `requirements.txt` (dependências)
  - `tests/` (base para unit tests)
  - `docs/ESPECIFICACOES-INICIAIS-DESENVOLVIMENTO.md` (este)
  - `README.md`, `LICENSE`

- **Bibliotecas obrigatórias:**
  - PyMuPDF (fitz)
  - PyPDF2
  - argparse ou typer

---

### Fase 2 — Edição e Busca de Texto

- **Objetivos**
  - Implementar extração de textos por página, posição, fonte, tamanho.
  - Implementar busca e substituição de texto.
  - Ajuste de texto (preservação visual, centralização, padding).
  - Exportar para JSON lista de textos com seus metadados.

- **Funções principais:**
  - `extract_text_objects(pdf_path) -> List[TextObject]`
  - `replace_text(pdf_path, objetos_json, params) -> novo_pdf`
  - `export_text_json(pdf_path) -> json_path`
  - `center_and_pad_text(obj, new_text) -> str`
  - Utilizar UUID/id para cada objeto editável.

---

### Fase 3 — Manipulação Estrutural de PDF

- **Objetivos**
  - Unir arquivos PDF (`merge_pdf(files: List[str]) -> novo_pdf`)
  - Excluir páginas específicas (`delete_pages(pdf, lista_paginas) -> novo_pdf`)
  - Suporte a múltiplos comandos encadeados na CLI.

---

### Fase 4 — Testes, Robustez e Documentação

- Testes unitários e integração (pytest)
- Tratamento de erros com mensagens claras
- README exemplos avançados, instruções ALIADAS ao Cursor IDE (scripts de build, pyinstaller…)
- Prontos para expansão futura (OCR, suporte a imagens, regex, GUI mínima, etc.)

---

## INSTRUÇÕES DE PROGRAMAÇÃO (para Cursor IDE)

1. Cada função/caso de uso deve ser modular, documentada com docstring clara (descrição, params, returns, exemplos).
2. CLI roteável (subcomandos) com help contextual.
3. Classes/DTOs de objetos PDF possuem id único, página, coord., fonte, texto, etc.
4. Favoritar sempre “DRY” — funções utilitárias no próprio módulo se reaproveitáveis.
5. Estruturar exceptions customizadas para falhas comuns (PDF malformado, texto não encontrado, etc).
6. O JSON de exportação deve ser legível e garantir reversibilidade (todos dados necessários para reconstrução).
7. Qualquer comando crítico/irreversível pedir confirmação (ou `--force`).
8. Todos os comandos aceitam caminhos absolutos e relativos.
9. Scripts de testes em `tests/` separados por funcionalidade.

---

## Observação

Após a entrega da Fase 1, cada fase ou funcionalidade deverá ter um documento de especificação próprio detalhado (docs/ESPEC-XYZ.md), com exemplos de entrada, saída, cenários de erro e sugestões de testes. Todas dependências a serem usadas devem ser registradas no requirements.txt.

---

**Engenheiro responsável e supervisor:**
Perplexity AI (com supervisão do usuário, líder do projeto)

**Qualquer dúvida ou ajuste de escopo, gerar issue e documentar feedbacks!**
