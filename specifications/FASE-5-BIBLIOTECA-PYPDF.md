# ESPECIFICACOES-FASE-5-INTEGRACAO-FIDELIDADE-FONTO-PyMuPDF-E-PYPDF.md

## PDF-cli — Fase 5: Estrutura adaptativa para preservação máxima da fonte

**Objetivo Geral:**
Permitir que a ferramenta PDF-cli utilize PyMuPDF como engine padrão para extração/edição, mas faça **fallback automático para pypdf** sempre que PyMuPDF não conseguir preservar a fonte original ao editar textos. Assim, maximiza fidelidade visual com eficiência de implementação, sem reescrever o código-base por completo.

---

## REQUISITOS FUNCIONAIS

### 1. Detecção automática de problema de fonte
- Ao executar um comando de edição (ex: `edit-text`), o sistema deve:
  - Tentar a operação usando PyMuPDF normalmente.
  - Antes de salvar ou após modificar, verificar se ocorreu fallback indesejado de fonte (ex: Arial mudou para Helvetica).
  - Se detectar fallback, registrar log detalhado e exibir alerta ao usuário.

### 2. Fallback inteligente para pypdf
- Quando identificar o problema de preservação de fonte:
  - O sistema deve automaticamente tentar **usar pypdf** para realizar a operação.
    - Editar o conteúdo dos streams mantendo as referências originais de objetos de fonte.
    - Caso pypdf consiga preservar a fonte, salvar e informar sucesso. Caso não, avisar usuário e registrar logs.
  - O comando CLI deve apresentar ao usuário qual engine foi usada em cada etapa (PyMuPDF ou pypdf) e registrar ambas tentativas no log.

### 3. Arquivo e acesso seguro
- Atentar para **lock de arquivos e concorrência**:
  - PyMuPDF e pypdf não devem abrir/escrever o arquivo simultaneamente.
  - Use arquivos temporários/intermediários para evitar acesso negado (Windows).
  - Sempre garantir que apenas uma biblioteca manipule o arquivo por vez — feche e libere antes da troca de engine.

### 4. Interface CLI
- O comando relevante (ex: `edit-text`) deve aceitar parâmetro opcional:
   - `--prefer-engine pymupdf` (default) ou `--prefer-engine pypdf`
   - Se for detectada perda de fidelidade, engine fallback é aplicado e logado automaticamente.
- O feedback ao usuário deve incluir:
   - Engine utilizada, fonte original e fonte final, sucesso/erro, logs detalhados.

### 5. Documentação, logs e testes
- Documente em README, ESPEC e CHANGELOG como funciona o fallback e em que casos o usuário pode esperar troca de engine.
- Logs devem mostrar em JSON:
   - Tentativa original (PyMuPDF), resultado, fontes, sucesso/erro
   - Tentativa do fallback (pypdf), resultado, fontes, sucesso/erro
- Testes automatizados para casos de substituição de texto, com PDFs reais que usam fontes do Windows e acompanham troca de engine.

---

## CHECKLIST DE ENTREGA

- src/core/engine_manager.py: módulo/função para detectar fallback de fonte e orquestrar troca de engine.
- src/app/services.py: comandos de edição adaptados para usar engine manager.
- README: documentação do sistema adaptativo de preservação de fontes.
- logs/: exemplos reais de edição com fallback.
- Testes automáticos que simulam (e auditam) cenários de perda/preservação de fonte.

---

## NOTAS E ALERTA

- Não reestruturar todo o sistema — adapte somente os comandos afetados pelo problema de fidelidade de fonte.
- Transparência é mandatória: sempre informar ao usuário qual engine foi usada, resultado, e logs completos das tentativas.
- Se ambos engines falharem, registrar limitação técnica e sugerir workflow alternativo (ex: edição por imagem/PIL para máxima fidelidade).

---

**Essa fase permite evoluir o PDF-cli garantindo fidelidade visual, eficiência operacional e máxima honestidade na entrega institucional.**
