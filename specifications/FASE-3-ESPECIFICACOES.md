```markdown
# ESPECIFICACOES-FASE-3-MANIPULACAO-OBJETOS-PDF.md

## Projeto: PDF-cli — Fase 3: Manipulação Avançada de Objetos PDF

**Objetivo Geral:**
Implementar todas as funcionalidades de manipulação e edição de objetos extraídos de PDFs, de acordo com os schemas e modelos definidos nas Fases 1 e 2. As operações do CLI devem ser precisas, seguras e 100% reversíveis, mantendo a integridade visual e semântica do documento.

---

## FUNCIONALIDADES E SUBCOMANDOS

### 1. **Extração Completa de Objetos**

- **Comando:**
  ```
  pdf.exe export-objects input.pdf output.json [--types text image table link formfield graphic layer annotation filter]
  ```
- **Features:**
  - Permite especificar quais tipos de objetos exportar via parâmetro `--types` (padrão: todos).
  - Exporta a lista completa, agrupada por página, fiel ao schema.
  - Salva JSON na estrutura exata dos modelos (ver templates da Fase 2).
- **Validação:**
  - Usuário pode solicitar apenas tipos específicos (ex: só “table” ou “image”).
  - Gera log com quantidade de objetos extraídos por tipo/página.

---

### 2. **Edição de Objetos Existentes**

**2.1 TextObject**
- **Comando:**
  ```
  pdf.exe edit-text input.pdf output.pdf --id <text_id> --content "Novo texto" [--align center --pad true]
  ```
- **Features:**
  - Permite alteração do conteúdo via ID único ou busca (content).
  - Ajusta alinhamento e padding conforme parâmetros.
  - Ajusta posição (`x`, `y`), fonte, cor, rotação conforme especificado.
  - Salva log detalhado das alterações, incluindo antes e depois.

**2.2 TableObject**
- **Comando:**
  ```
  pdf.exe edit-table input.pdf output.pdf --id <table_id> --row 2 --col 3 --value "Novo valor"
  ```
- **Features:**
  - Permite editar células específicas via linha/coluna.
  - Permite alterar headers, fontes de coluna, cor da célula.
  - Gera log de alterações granulares.

**2.3 ImageObject**
- **Comando:**
  ```
  pdf.exe replace-image input.pdf output.pdf --id <image_id> --src "nova_imagem.png"
  ```
- **Features:**
  - Troca imagem mantendo posição e dimensões.
  - Permite aplicar filtro (ex: grayscale, invert).

**2.4 Outros Objetos**
- Funções específicas para FormField, Gráficos/Vetoriais, Links (edit, toggle, add/remove).

---

### 3. **Inserção de Novos Objetos**

- **Comando:**
  ```
  pdf.exe insert-object input.pdf output.pdf --type <tipo> --params <json>
  ```
- **Features:**
  - Permite criar novos objetos, preencher todos campos conforme schema do tipo desejado.
  - Permite passar parâmetros via JSON para máxima flexibilidade.
  - Validação pesada: todos campos obrigatórios devem ser checados; campos opcionais informam valor padrão/documentado no log.
  - Suporte a múltiplos objetos em lote (inserção de várias imagens/tabelas/textos/etc. de uma vez usando JSON).

---

### 4. **Reconstrução/Reimportação via JSON**

- **Comando:**
  ```
  pdf.exe restore-from-json source.pdf objetos_editados.json output.pdf
  ```
- **Features:**
  - Aplica todas alterações presentes no JSON ao PDF original.
  - Altera textos, imagens, posições, inclui ou remove objetos conforme especificação do JSON.
  - Garante reversibilidade: sempre salva log de alteração e backup do original.
  - Antes de aplicar, executa validação da integridade do JSON vs modelos (alerta e aborta se houver inconsistência).

---

### 5. **Edição de Metadata Estrutural**

- **Comando:**
  ```
  pdf.exe edit-metadata input.pdf output.pdf --title "Novo Título" --author "Novo Autor" --keywords "palavra1,palavra2"
  ```
- **Features:**
  - Permite edição dos metadados básicos e avançados do PDF.
  - Gera log da alteração; mantém histórico de alterações de metadados.

---

### 6. **Exclusão, União e Split de Páginas**

**6.1. Exclusão**
- **Comando:**
  ```
  pdf.exe delete-pages input.pdf output.pdf --pages 1,4,6-8
  ```
- **Features:**
  - Remove páginas específicas, ajusta estrutura restante dos objetos.
  - Salva log de operação.

**6.2. União**
- **Comando:**
  ```
  pdf.exe merge arquivo1.pdf arquivo2.pdf ... -o combinado.pdf
  ```
- **Features:**
  - Junta arquivos mantendo ordem dos objetos e páginas.
  - Valida compatibilidade de modelos entre os PDFs.

**6.3. Split**
- **Comando:**
  ```
  pdf.exe split input.pdf --ranges 1-3,4-6 --out prefix_
  ```
- **Features:**
  - Divide PDF em diversos arquivos conforme faixas de páginas.
  - Mantém integridade dos objetos exportados/inseridos.

---

## REGRAS DE IMPLEMENTAÇÃO

- Todos comandos devem validar os parâmetros (type hints, help, enums).
- Flags destrutivas requerem confirmação pra evitar perdas.
- Logs em JSON detalhados devem ser gerados para cada operação, sempre com IDs únicos.
- Reutilize e estenda os modelos de dados da Fase 2.
- Todo novo objeto inserido deve estar 100% conforme os schemas dos exemplos técnicos.
- Testes automatizados em `tests/` para todos comandos; exija coverage significativo antes do commit.

---

## MODELO DE TESTE

- Teste para manipulação de cada tipo de objeto: extração, edição, inserção, exclusão, merge/split, restore.
- Teste para logs e reversibilidade da operação.
- Teste para integridade visual/resultados finais em PDF e JSON.
- Teste para erro esperado: parâmetros inválidos, inconsistências de schema, alterações em lote.

---

## DOCS E EXEMPLOS PRÁTICOS

- README sempre atualizado com exemplos reais de todos comandos e objetos.
- Relatório de cobertura, performance e limitações (quando houver) na entrega.

---

## CHECKLIST DE ENTREGA

- src/app/services.py: funções core de manipulação, documentadas e testadas conforme especificação.
- src/app/pdf_repo.py: métodos para todas operações implementados.
- src/core/models.py: atualizado caso novos campos/tipos surgirem.
- CLI testado e funcional, integrando todas operações.
- Suite de testes e logs de operação completos.
- Documentação de todos comandos e modelos (README, SPEC).

---

## REGRAS DE COMPORTAMENTO E QUALIDADE

- Programe com rigor: apenas o especificado e documentado.
- Consulte engenheiro antes de qualquer ajuste de schema ou modelo.
- Reforce logging, testes e validação em cada commit.
- Qualquer dúvida, registre issue explicativa e aguarde direcionamento.

---

**Essa Fase 3 consolida o projeto como ferramenta de automação PDF de padrão profissional, extensível e auditável.**
```
