**Prompt para Cursor IDE — Fase 6: Testes Reais e Relatório de Auditoria**

Leia e siga estritamente o documento “ESPECIFICACOES-FASE-5-VALIDACAO-REPRODUTIVIDADE-REAL.md”.
Sua missão nesta fase é garantir a reprodutibilidade, honestidade e auditoria total das funções implementadas até aqui, usando os arquivos PDF da pasta `./examples`.

## **Tarefas Obrigatórias**

1. **Teste cada funcionalidade do PDF-cli com TODOS os arquivos reais da pasta `./examples`**
   - Utilize os arquivos: `boleto.pdf`, `contracheque.pdf`, `demonstrativo.pdf`, `despacho.pdf`, `orçamento.pdf`.
   - Não utilize PDFs simulados, mockados ou gerados artificialmente.

2. **Para cada função/comando CLI já implementado:**
   - Extraia textos, imagens, metadados, anotações, links, páginas, etc.
   - Execute edições de texto, imagens, metadados e manipulações de páginas.
   - Salve e registre os arquivos de saída (JSONs, imagens exportadas, PDFs modificados).
   - Gere logs detalhados (em JSON) das operações.

3. **Documente os resultados reais em um relatório “FASE-5-RELATORIO-TESTES-REAIS.md”:**
   - Para cada comando/teste, registre:
     - Parâmetros utilizados
     - Saídas reais geradas (trechos representativos)
     - Logs reais das execuções
     - Status (sucesso, erro, limitação)
     - Observações sobre o resultado funcional e visual
     - Caso alguma função não opere conforme o esperado, justifique tecnicamente e sugira possível solução.

4. **Checklist de auditoria:**
   - Todos arquivos gerados devem ser disponibilizados para conferência (pasta “logs/”, “outputs/”).
   - O relatório deve permitir que outro profissional repita exatamente os testes e obtenha os mesmos resultados.

5. **Transparência e honestidade:**
   - Não omita falhas, erros ou resultados incompletos.
   - Só declare como testada a funcionalidade que operou de fato sobre os PDFs reais.

## **Regra de Ouro**
> “Testar é validar com o mundo real: cada função deve ser exercitada nos arquivos originais, toda saída deve ser concreta, todo relatório deve ser fidedigno e auditável.”

***

Inicie a execução dos testes conforme especificações, organize as saídas, e redija o relatório final para homologação do projeto.
