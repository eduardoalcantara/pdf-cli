**Prompt para Cursor IDE — Implementação da Fase 4: Testes, Robustez e Honestidade**

Leia integralmente o documento de especificações da Fase 4.
Sua missão central nesta fase é garantir a **robustez, honestidade e auditoria plena** no funcionamento do PDF-cli.

## **Tarefas Obrigatórias**

1. **Implemente testes automatizados e funcionais para cada comando CLI:**
   - *Somente operações reais e efetivas devem ser testadas.*
   - Cubra casos comuns, cenários limite, erros esperados e resultados verificáveis.
   - Não use mocks, prints or simulações (tests must work on real PDFs and outputs).

2. **Certifique-se que todo comando/serviço faça exatamente o que está na especificação:**
   - Não marque nenhuma função como concluída se ela não realiza operações reais sobre o PDF.
   - Se alguma limitação técnica impedir uma funcionalidade, **documente imediatamente** no README, ESPEC e log da operação.
   - Nunca omita ou camufle funcionalidades pendentes: seja transparente quanto ao que está pronto e ao que está em desenvolvimento.

3. **Gere logs JSON exatos e completos para todas operações:**
   - Cada alteração, erro ou sucesso deve ser registrado de forma auditável.
   - Logs devem refletir os resultados reais, nunca “fakes”.

4. **Atualize e mantenha toda documentação:**
   - README, ESPEC-FINAL, CHANGELOG devem indicar progresso, limitações, cenários não atendidos e possíveis melhorias futuras.
   - Informe claramente aos usuários e gestores qualquer restrição ou falha detectada durante os testes/execuções.

5. **Checklist de honestidade:**
   - Antes de qualquer commit, valide que a feature/teste/operação está 100% operacional e honesta.
   - Não declare como "feito" nada que dependa de simulação, mock ou workaround temporário.

***

## **Observação Crítica**

> **A implementação do processamento adaptativo de tabelas (detecção via múltiplas bibliotecas: Camelot, Tabula, pdfplumber, OCR, etc.) foi movida para a última fase do projeto.**
> Portanto, nesta fase você NÃO deverá tentar simular ou entregar processamento de tabelas fora do contexto de teste/auditoria.
> Caso necessário, faça referência explícita aos comandos relacionados a tabelas como "planejados para a fase final" e documente esse adiamento nos relatórios, logs e README.

***

**Regra de Ouro:**
> “Transparência absoluta e confiabilidade — entregue apenas o que é real! Toda pendência ou limitação deve estar plenamente registrada. Testes devem rodar sobre arquivos e operações reais, nunca mocks.”

***

Inicie os trabalhos conforme instruções acima, garantindo que o padrão ético e técnico do PDF-cli seja mantido em toda a entrega da fase 4.
