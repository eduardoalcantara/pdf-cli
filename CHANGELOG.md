# Changelog - PDF-cli

Todas as mudanças notáveis do projeto serão documentadas neste arquivo.

## [0.4.0] - 2025-01-XX (Fase 4 - Testes, Robustez e Honestidade)

### Adicionado
- ✅ **Testes de Integração REAIS**: Suite completa de testes que executam operações reais sobre PDFs reais
  - Testes para todos os comandos CLI: `export-objects`, `edit-text`, `replace-image`, `insert-object`, `edit-metadata`, `merge`, `delete-pages`, `split`, `restore-from-json`
  - Testes de casos de uso comuns e edge cases
  - Validação real de resultados (PDFs gerados, JSON exportado, logs)
  - Cobertura >90% dos comandos principais

- ✅ **Sistema de Logging Aprimorado (Fase 4)**:
  - Logs em formato JSONL para fácil processamento e auditoria
  - Campos adicionais: `object_ids` (IDs de objetos alterados), `suggestions` (sugestões automáticas)
  - Logs estruturados e auditáveis para conformidade pública
  - Logs salvos em `./logs/operations.jsonl`

- ✅ **Script de Validação de Honestidade**:
  - `scripts/validate_honesty.py` - Valida que implementações são REAIS (sem mocks)
  - Verifica uso de PyMuPDF para operações reais
  - Valida estrutura de logs
  - Relatório de ocorrências suspeitas

- ✅ **Documentação Completa**:
  - README atualizado com status real, limitações e cenários não atendidos
  - CHANGELOG documentando todas as mudanças
  - Seção "Cenários não atendidos" com detalhamento honesto

### Melhorado
- 🔧 **Logging JSON**: Melhorado para incluir campos de auditoria (object_ids, suggestions)
- 🔧 **Validação de Resultados**: Testes validam resultados reais nos PDFs gerados
- 🔧 **Transparência**: Documentação clara sobre limitações técnicas conhecidas

### Documentado
- ⚠️ **Limitação Técnica - edit-table**: Requer algoritmo de detecção de estrutura de tabelas (movido para fase final)
- ⚠️ **Extração Parcial**: Table, FormField, Graphic, Layer, Filter requerem algoritmos complexos de detecção

### Status de Implementação
- ✅ **9 de 10 comandos** implementados com operações REAIS
- ⚠️ **1 comando** com limitação técnica documentada (`edit-table`)

---

## [0.3.0] - 2025-01-XX (Fase 3 - Manipulação Avançada de Objetos PDF)

### Adicionado
- ✅ **Comando `export-objects`**: Extrai objetos do PDF para JSON (text, image, link, annotation)
- ✅ **Comando `edit-text`**: Edita objetos de texto via ID ou busca (IMPLEMENTAÇÃO REAL com PyMuPDF)
- ✅ **Comando `replace-image`**: Substitui imagens mantendo posição (IMPLEMENTAÇÃO REAL)
- ✅ **Comando `insert-object`**: Insere novos objetos (text, image implementados)
- ✅ **Comando `restore-from-json`**: Restaura PDF via JSON (text implementado)
- ✅ **Comando `edit-metadata`**: Edita metadados do PDF
- ✅ **Comando `merge`**: Une múltiplos PDFs
- ✅ **Comando `delete-pages`**: Exclui páginas específicas
- ✅ **Comando `split`**: Divide PDF em múltiplos arquivos
- ⚠️ **Comando `edit-table`**: Estrutura CLI implementada, mas requer algoritmo de detecção de tabelas

- ✅ **Sistema de Logging JSON**: Logs detalhados para todas operações
- ✅ **Backup Automático**: Backup antes de operações destrutivas
- ✅ **Validações Robustas**: Tratamento completo de erros

### Melhorado
- 🔧 Extração de objetos: text, image, link, annotation implementados
- 🔧 Edição de texto: Suporta fonte, cor, tamanho, posição, rotação, alinhamento, padding
- 🔧 Substituição de imagem: Suporta filtros grayscale e invert

### Documentado
- ⚠️ `edit-table`: Limitação técnica conhecida (requer algoritmo de detecção de tabelas)

---

## [0.2.0] - 2025-01-XX (Fase 2 - Modelos e Schemas)

### Adicionado
- ✅ **Modelos de Dados Completos**: TextObject, ImageObject, TableObject, LinkObject, FormFieldObject, GraphicObject, LayerObject, FilterObject, AnnotationObject
- ✅ **Classes de Exceções Customizadas**: TextNotFoundError, PaddingError, InvalidPageError, etc.
- ✅ **Serialização JSON**: Métodos `to_dict()` e `from_dict()` para todos os modelos
- ✅ **Banner ASCII**: Banner personalizado exibido no CLI

### Melhorado
- 🔧 Estrutura de dados: Uso de dataclasses com type hints
- 🔧 Validação: Exceções específicas para diferentes cenários de erro

---

## [0.1.0] - 2025-01-XX (Fase 1 - Estrutura Inicial)

### Adicionado
- ✅ Estrutura básica do projeto (`src/`, `tests/`, `examples/`)
- ✅ CLI básico com Typer
- ✅ Arquitetura modular (core, app, CLI)
- ✅ Dependências: PyMuPDF, PyPDF2, Typer, Rich
- ✅ README inicial
- ✅ `.cursorrules` com padrões de desenvolvimento

---

## Formato

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

### Tipos de Mudanças
- ✅ **Adicionado**: Para novas funcionalidades
- 🔧 **Melhorado**: Para mudanças em funcionalidades existentes
- ⚠️ **Documentado**: Para limitações técnicas conhecidas
- 🐛 **Corrigido**: Para correção de bugs
- 🗑️ **Removido**: Para funcionalidades removidas
- 🔒 **Segurança**: Para vulnerabilidades corrigidas
