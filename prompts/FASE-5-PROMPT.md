**Prompt para Cursor IDE — Implementação da FASE 5: Fallback Inteligente PyMuPDF + pypdf e Auditoria Completa**

Você deverá implementar a FASE 5 conforme a especificação “ESPECIFICACOES-FASE-5-INTEGRACAO-FIDELIDADE-FONTO-PyMuPDF-E-PYPDF.md”.
**Sua missão é garantir preservação máxima da fonte original do PDF durante edição de textos, utilizando fallback automático para pypdf sempre que o PyMuPDF não conseguir preservar a fidelidade visual.**

## **Tarefas Obrigatórias**

1. **Desenvolva um “engine manager” para edição de texto:**
   - Toda edição de texto (`edit-text`) deve inicialmente usar PyMuPDF.
   - Após a tentativa, verifique se ocorreu fallback de fonte (ex: Arial mudou para Helvetica).
   - Se ocorreu, o sistema deve automaticamente realizar a edição utilizando pypdf, preservando a fonte original nas referências do PDF.
   - O CLI deve informar claramente ao usuário o resultado de cada engine: fonte original, fonte usada, sucesso/falha, log detalhado.
   - Permita parâmetro ao usuário para forçar uso de engine (`--prefer-engine`).

2. **Teste, de fato, todas operações usando TODOS arquivos PDF do repositório (`./examples/`).**
   - Execute comandos reais (não simulações) sobre:
     - boleto.pdf
     - contracheque.pdf
     - demonstrativo.pdf
     - despacho.pdf
     - orçamento.pdf
   - Para cada substituição de texto, avalie e registre o comportamento das fontes antes e depois da modificação.

3. **Produza e guarde logs e JSONs reais:**
   - Para cada operação e cada arquivo, gere:
     - JSON representando a estrutura dos objetos “antes” da modificação
     - JSON representando a estrutura “depois”
     - Log detalhado (JSONL) com engine utilizada, fontes, sucesso/erro, observações, hashes dos arquivos envolvidos
   - Todos esses arquivos devem ser organizados para análise posterior (pasta “logs/”, “outputs/”).

4. **Relatório de auditoria obrigatória:**
   - Elabore um documento “FASE-5-RELATORIO-FONTS-REAL.md” contendo:
     - Tabela (por arquivo) comparando fonte antes/depois, engine utilizada, divergências, possíveis causas e sugestões de solução
     - Trechos relevantes dos arquivos modificados (imagens ou texto extraído)
     - Logs e JSONs gerados

5. **Transparência e honestidade absoluta:**
   - Não oculte ou mascare falhas, limitações ou problemas; cada ocorrência deve ser informada com precisão e justificativa técnica.
   - Nunca declare como “feito/testado” nenhuma funcionalidade que não opere sobre arquivos reais do repositório.
   - Se ambos engines falharem, registre limitação técnica no relatório, proponha workaround ou pesquisa complementar.

6. **Documentação e commit:**
   - Atualize o README, documentação e CHANGELOG com o novo fluxo de fallback, exemplos de uso, logs reais e limitações.
   - Cada commit deve associar código, logs, JSONs e relatório da operação.

***

## **Regra de Ouro:**
> “Priorize sempre a honestidade e auditoria: toda modificação deve ser rastreável, testada, logada e documentada com o máximo de detalhes, usando arquivos reais do acervo do projeto.”

***

**A qualidade institucional e técnica do PDF-cli depende da perfeição e transparência desta fase. Execute sem atalhos!**
