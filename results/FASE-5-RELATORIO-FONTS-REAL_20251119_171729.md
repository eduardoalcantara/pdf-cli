# Relatório de Auditoria - Fase 5: Preservação de Fontes

**Data:** 2025-11-19 17:17:29
**Versão:** 0.5.0 (Fase 5)
**Total de Testes:** 13

---

## Resumo Executivo

- **Testes realizados:** 13
- **Fallback detectado:** 0
- **Fontes preservadas:** 7
- **Taxa de preservação:** 53.8%

---

## Detalhes dos Testes

### Teste 1: orçamento.pdf

- **Arquivo de entrada:** `examples/orçamento.pdf`
- **Arquivo de saída:** `orçamento_test.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 30.88ms
   - Comparações de fonte: 0

---

### Teste 2: despacho.pdf

- **Arquivo de entrada:** `examples/despacho.pdf`
- **Arquivo de saída:** `despacho_test.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 10.77ms
   - Comparações de fonte: 0

---

### Teste 3: demonstrativo.pdf

- **Arquivo de entrada:** `examples/demonstrativo.pdf`
- **Arquivo de saída:** `demonstrativo_test.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 82.06ms
   - Comparações de fonte: 0

---

### Teste 4: contracheque.pdf

- **Arquivo de entrada:** `examples/contracheque.pdf`
- **Arquivo de saída:** `contracheque_test.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 84.65ms
   - Comparações de fonte: 0

---

### Teste 5: boleto.pdf

- **Arquivo de entrada:** `examples/boleto.pdf`
- **Arquivo de saída:** `boleto_test.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 80.12ms
   - Comparações de fonte: 0

---

### Teste 6: boleto.pdf

- **Arquivo de entrada:** `examples/boleto.pdf`
- **Arquivo de saída:** `boleto_test_pypdf.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 58.89ms
   - Comparações de fonte: 0

---

### Teste 7: boleto.pdf

- **Arquivo de entrada:** `examples/boleto.pdf`
- **Arquivo de saída:** `boleto_test_pymupdf.pdf`
- **Engine final:** `pymupdf`
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ✓ Sim
- **Tentativas de engine:** 1

**Tentativas:**

1. **pymupdf**
   - Sucesso: ✓
   - Fallback: ✓ Não
   - Tempo: 75.07ms
   - Comparações de fonte: 0

---

### Teste 8: orçamento.pdf

- **Arquivo de entrada:** `examples\orçamento.pdf`
- **Arquivo de saída:** `orçamento_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

### Teste 9: despacho.pdf

- **Arquivo de entrada:** `examples\despacho.pdf`
- **Arquivo de saída:** `despacho_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

### Teste 10: demonstrativo.pdf

- **Arquivo de entrada:** `examples\demonstrativo.pdf`
- **Arquivo de saída:** `demonstrativo_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

### Teste 11: contracheque.pdf

- **Arquivo de entrada:** `examples\contracheque.pdf`
- **Arquivo de saída:** `contracheque_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

### Teste 12: boleto.pdf

- **Arquivo de entrada:** `examples\boleto.pdf`
- **Arquivo de saída:** `boleto_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

### Teste 13: boleto.pdf

- **Arquivo de entrada:** `examples/boleto.pdf`
- **Arquivo de saída:** `boleto_edited.pdf`
- **Engine final:** ``
- **Fallback detectado:** ✓ Não
- **Preservação de fonte:** ⚠️ Não
- **Tentativas de engine:** 0

**Tentativas:**

---

## Conclusões

### Problemas Identificados

### Próximos Passos

1. Investigar por que o fallback automático não está sendo acionado
2. Verificar se a detecção de fallback está comparando corretamente os objetos
3. Testar a implementação do pypdf com preservação de especificações de fonte (/F1, /F2, etc.)
4. Validar que o pypdf realmente preserva as fontes quando usado corretamente

