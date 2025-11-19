# ESPECIFICACOES-FASE-FINAL-DETECCAO-TABELAS-ADAPTATIVA.md

## Projeto: PDF-cli — Fase Final: Detecção Adaptativa e Manipulação de Tabelas PDF

**Objetivo Geral:**
Implementar uma solução robusta e adaptativa para extração e manipulação de tabelas em PDFs usando múltiplas bibliotecas especializadas, selecionando automaticamente (ou sob demanda) a engine que melhor atende à complexidade do arquivo.

---

## REQUISITOS FUNCIONAIS

### 1. **Pipeline Adaptativo de Extração de Tabelas**

- Crie uma função central que analisa o arquivo PDF e escolhe automaticamente a melhor biblioteca de extração de tabelas:
  - **Camelot:** prioridade para PDFs digitais que possuem linhas/separadores limpos.
  - **Tabula:** utilizada para PDFs digitais sem linhas claras, layouts híbridos ou margens flexíveis.
  - **pdfplumber:** usada em PDFs com ausência de estrutura tradicional ou com tabelas “desenhadas”.
  - **OCR + heurística (Tesseract):** obrigatória para PDFs de imagem ou digitalizados, combinada com análise de layout/texto para formar a tabela.

### 2. **Fallback e Escolha Manual**
- O sistema deve permitir ao usuário forçar a engine via parâmetro CLI:
  - Ex: `--engine camelot`, `--engine tabula`, `--engine pdfplumber`, `--engine ocr`
- Se nenhum resultado for considerado satisfatório pelo pipeline “auto”, deve retornar erro claro e logar todos os passos.

### 3. **Interface CLI e Parâmetros**

- Comando principal:
  ```
  pdf.exe export-table input.pdf output.json [--engine auto] [--pages 1-4] [--force-ocr]
  ```
- Parâmetros:
  - `--engine [auto|camelot|tabula|pdfplumber|ocr]`
  - `--pages`: intervalo de páginas para otimizar performance
  - `--force-ocr`: força pipeline OCR, mesmo se PDF for digital

### 4. **Formato de Saída e Modelagem**

- Exportar tabelas para JSON seguindo o modelo da Fase 2:
  ```
  {
    "id": "tbl-<uuid>",
    "page": <num>,
    "type": "table",
    "x": <float>,
    "y": <float>,
    "width": <float>,
    "height": <float>,
    "headers": ["Header1", "Header2"],
    "rows": [
      ["valor1", "valor2"],
      ["valor3", "valor4"]
    ],
    "cell_fonts": [{...}]
  }
  ```
- Permitir exportação para CSV opcional via parâmetro.

### 5. **Logs e Diagnóstico**

- Todo processo deve registrar log detalhado:
  - Engine usada, tempo da operação, número de tabelas encontradas, páginas trabalhadas, avisos e falhas.
  - Em caso de erro, informar engine tentada, tipo de falha, sugestões ao usuário.

### 6. **Testes Automatizados**

- Prepare arquivos PDF de cada tipo: digital, híbrido, imagem.
- Testes devem validar:
  - Correção do parsing dos headers/células
  - Quadros de falha em casos limítrofes (ex: layout irregular)
  - Performance e logs de diagnóstico rotineiro

### 7. **Documentação Detalhada**

- README com exemplos práticos de cada engine, resultado de exportação e limitações.
- Orientações para o usuário escolher engine manualmente caso a detecção auto seja insatisfatória.
- Tabela comparativa das bibliotecas, limitações, formatos suportados.

---

## CHECKLIST DE ENTREGA

- src/app/table_pipeline.py: implementação completa do pipeline e interface
- src/core/models.py: atualização do model TableObject conforme necessidade
- src/app/services.py: funções para exportação/manipulação/importação de tabelas com engine adaptativa
- CLI funcional e testada, integrando parâmetros e logs
- Testes automatizados em `tests/` para todos cenários/engines
- README atualizado, exemplos para todos casos

---

## REGRAS DE IMPLEMENTAÇÃO E QUALIDADE

- Todo fallback ou erro deve ser transparente, nunca simulado.
- O pipeline adaptativo não pode “mascarar” falhas: se não extrair a tabela, o usuário precisa ser informado.
- Logs são obrigatórios, devendo registrar cada tentativa de engine, parâmetros, sucesso/falha.
- Código deve ser modular para futura integração com novas bibliotecas (ex: deep learning para tabelas).
