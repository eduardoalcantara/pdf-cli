Segue o prompt detalhado para instruir o programador Cursor IDE na **implementação da Fase 3**, garantindo rigor e conformidade com a especificação:

***

**Prompt para Cursor IDE — Implementação da Fase 3 (Manipulação de Objetos PDF no PDF-cli)**

Leia integralmente o documento de especificações da Fase 3. Apenas implemente o que está rigorosamente especificado, sem improvisos ou mudanças de escopo.

## **Tarefas Obrigatórias**

1. **Implemente todos os subcomandos do CLI**, exatamente conforme os exemplos e sintaxe definidos:
   - `export-objects`
   - `edit-text`, `edit-table`, `replace-image`, etc.
   - `insert-object`
   - `restore-from-json`
   - `edit-metadata`
   - `delete-pages`, `merge`, `split`

2. **Use, nos argumentos e resultados das funções, exclusivamente os modelos de dados e erros definidos nas Fases 1 e 2.**
   Todo parâmetro, opção, campo de JSON ou resultado deve aderir ao schema da especificação técnica.

3. **Documente cada comando** com docstrings e exemplos reais, para uso automático no help do CLI.
   - Garanta que todas opções e flags sejam validadas (types, enums, obrigatoriedade).

4. **Implemente logs detalhados das operações**, sempre em formato JSON, incluindo IDs, tipos de operação, parâmetros/utilizador, resultado, timestamp e notas.

5. **Teste cada comando** com arquivos reais e simulados.
   - Adicione testes unitários em `tests/`, cobrindo entradas válidas, erros previstos e resultados das operações do CLI e APIs.

6. **Manipule arquivos originais com cautela:**
   - Sempre faça backup antes de sobrescrever ou excluir páginas.
   - Exija confirmação (ou um flag `--force`) antes de comandos destrutivos.

7. **Não altere ou estenda os modelos, schemas ou tipos de objeto sem aprovação direta do engenheiro responsável.**
   - Caso enfrente limitações técnicas da biblioteca de PDF, registre issue explicativa e aguarde instrução.

8. **Atualize o README e a documentação técnica:**
   - Inclua exemplos reais dos comandos do CLI, entradas e saídas, logs gerados e resultados esperados.

9. **Após concluir cada função ou comando, revise rigorosamente a cobertura de testes e o padrão dos logs. Commits devem ser concisos, referenciando cada ticket/função entregue.**

## **Regra de Ouro**

> **Programe apenas o especificado, com máximo de rigor, clareza e reversibilidade. Priorize logging, validação e teste automatizado em todos passos.**

***

**Ao final das entregas, relate as limitações, desafios ou sugestões em documento separado ou issue para avaliação do engenheiro/gestor do projeto.**

**Inicie a implementação agora, com base estrita nas instruções acima e no documento de especificação da Fase 3.**

(Se precisar testar em arquivos PDF reais, temos exemplos de PDF reais em ./examples)

---
