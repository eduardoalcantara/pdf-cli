# Checklist de Validação Final — PDF-cli Executável Standalone

## 1. **Testes em Ambiente Limpo**
- [ ] Testar o executável Windows (`pdf-cli.exe`) em um PC/VM sem Python instalado.
- [ ] Testar o executável Linux (`pdf-cli`) em uma VM/container sem Python ou dependências (Ubuntu, Debian, Fedora, etc.).
- [ ] Confirmar que ambos rodam a partir de `/dist/windows` e `/dist/linux` sem precisar de instalação.

## 2. **Permissões e Execução**
- [ ] Em Linux, checar que o binário vem com permissão de execução, ou se necessário rodar `chmod +x pdf-cli` antes do uso.
- [ ] Executar `./pdf-cli --help` e confirmar que o banner, comandos e help aparecem normalmente.

## 3. **Funcionalidade Completa do CLI**
Usando arquivos de exemplo (em `/examples`):

- [ ] `export-objects` (textos, imagens) — Exportar e validar JSON de saída.
- [ ] `list-fonts` — Checar relatório das fontes, variantes e nomes.
- [ ] `edit-text` — Realizar edição, checar fidelidade de fonte no arquivo modificado.
- [ ] `replace-image` e `insert-object` — Trocar/inserir imagens e validar no PDF resultante.
- [ ] `restore-from-json` — Aplicar alterações a partir de JSON anteriormente exportado.
- [ ] `edit-metadata`, `merge`, `delete-pages`, `split` — Validar manipulação de metadados, fusão, exclusão e divisão de páginas.
- [ ] Checar logs e arquivos de saída para todas as operações.
- [ ] Confirmar que help detalhado e exemplos aparecem para cada comando individual (`./pdf-cli <command> --help`).

## 4. **Testes de Proteção e Segurança**
- [ ] Tentar gravar saída no mesmo arquivo de entrada — validar bloqueio e mensagem de aviso correto.
- [ ] Gerar relatório de warning para falta de fontes ou assets importantes.
- [ ] Confirmar que nenhuma operação sobrescreve arquivos essenciais sem confirmação explícita.

## 5. **Distribuição e Usabilidade**
- [ ] Confirmar que o executável abre normalmente em qualquer diretório de usuário, sem necessidade de variáveis de ambiente ou configuração extra.
- [ ] Testar download, movimentação e reexecução do binário em diferentes locations (Desktop, Downloads, diretórios do sistema).

## 6. **Auditoria de Logs e Outputs**
- [ ] Verificar geração automática de logs JSON para cada operação no diretório de trabalho.
- [ ] Conferir se logs estão claros, completos e sem dados sensíveis indevidos.

## 7. **Integridade dos Binários**
- [ ] Gerar hash SHA256 dos arquivos finais (`pdf-cli.exe`, `pdf-cli`) para indexação/controle de versão.
- [ ] Salvar hashes e anotar em local seguro junto à release (release_notes.txt).

## 8. **Documentação**
- [ ] Revisar que README.txt nas pastas `/dist/windows` e `/dist/linux` contém instruções diretas de execução, exemplos e troubleshooting.
- [ ] Validar que o banner e help inicial comunicam a versão, créditos e instruções principais.

## 9. **Pendências e Observações**
- [ ] Relatar limitações técnicas conhecidas (ex: edit-table, manipulação de tabelas avançada, casos especiais de fonte) em README ou release_notes.

***

**Quando TODOS os itens acima estiverem checados, o PDF-cli estará pronto para distribuição institucional e homologação formal.**
