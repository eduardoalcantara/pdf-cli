**Prompt Inicial para Cursor IDE: Início do Projeto PDF-cli**

Você é um programador especialista em Python e automação de PDF.
Seu objetivo é iniciar o desenvolvimento do projeto **PDF-cli** em um repositório limpo já criado em `d:\proj\pdf` com as pastas `specifications`, `documents` e `src`.

## Tarefas iniciais

1. **Estruture a pasta `src/` com o seguinte esqueleto de arquivos:**
   - `pdf_cli.py` — arquivo principal (entrypoint CLI e roteador de comandos)
   - `app/services.py` — casos de uso (funções core)
   - `app/pdf_repo.py` — camada de infraestrutura para operações com PDF
   - `core/models.py` — objetos, DTOs para textos do PDF (inclua id único, página, coordenadas, fonte etc.)

   Crie as subpastas conforme necessário dentro de `src/`.

2. **Prepare o arquivo `requirements.txt`** na raiz do repositório (ou da pasta src/), listando as dependências obrigatórias:
   - PyMuPDF (fitz)
   - PyPDF2
   - argparse ou typer

3. **Inclua docstrings básicas explicando a responsabilidade de cada arquivo e módulo.**

4. **Garanta que o entrypoint (`pdf_cli.py`) possa exibir uma mensagem de boas-vindas e o help inicial ao ser executado.**

5. **Monte comentários TODO indicando o plano para cada módulo/component, alinhado às fases descritas em `specifications/ESPECIFICACOES-INICIAIS-DESENVOLVIMENTO.md`.**

6. **Não implemente funções completas de edição neste momento, apenas construa o esqueleto/fundação para facilitar extensão futura e aderir às boas práticas do projeto.**

7. **Documente seu progresso e decisões em comentários e arquivos de log (se apropriado).**

**Regra fundamental:** clareza, qualidade e extensibilidade.
Siga rigorosamente as regras de modelagem, comportamento e padrões definidos em `.cursorrules`.

***

**Instrução para execução do Cursor:**

> “Inicie o projeto PDF-cli estruturando o diretório `src/` conforme especificado, crie todos arquivos e docstrings indicados, liste as dependências em `requirements.txt` e documente pontos de extensão futura. Confirme ao fim que o help da CLI está funcionando e que todos arquivos necessários estão presentes para início seguro do desenvolvimento.”
