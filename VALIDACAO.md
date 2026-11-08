# Validação da cópia local

Executada em 08/11/2026, com dados fictícios, em PostgreSQL temporário local. Nenhum dado hospedado foi acessado ou alterado nesta rodada.

## Resultado

- 50 testes Django passaram, incluindo novo ajuste de duração e composição na triagem, data real diferente da previsão, permissão de histórico e restrições no banco.
- 7 verificações PostgreSQL passaram: concorrência de entrega, compatibilidade de backup anterior, restauração em base separada, destino preenchido, controle de acesso, comprovante de arquivo e suspensão até liberação.
- `manage.py check`: sem problemas; migração 0011 executada em banco de teste limpo.
- `manage.py check --deploy --fail-level ERROR`: sem erros; quatro avisos de SSL/HSTS/cookies vieram da configuração local de teste (`CESTAS_LOCAL_TEST=1`). Os valores efetivos de produção não foram inspecionados.
- `collectstatic --noinput`: passou; `workflow.css` foi copiado para a pasta servida. O comando foi incluído no build da Vercel para evitar assets desatualizados.
- `manage.py makemigrations --check --dry-run`: nenhuma migração faltante.
- Navegador Playwright: login e triagem testados em 390 px; cadastro e entrega em 320 px; triagem em 768 px; início, ficha e relatórios em 1366 px. As páginas conferidas mantiveram `scrollWidth` igual à viewport.
- Fluxo manual com dados fictícios: coordenação revisou a triagem, ajustou duração de 2 meses para 1, aprovou e recebeu confirmação. Nenhum erro ou aviso no console ao final.
- A primeira abertura detectou `workflow.css` ausente do `staticfiles` e resposta 404. Foi corrigido o build para executar `collectstatic`; após reiniciar o servidor, CSS respondeu HTTP 200 e console zerado.

Os testes e o navegador usaram somente PostgreSQL local com dados fictícios. Não foram feitos testes em aparelho Android físico nem com voluntários reais. A migração e o código continuam sem aplicação/publicação em produção e sem envio ao GitHub.

## Verificações ainda necessárias antes do uso real

1. Atualizar e migrar o ambiente Vercel/Neon pretendido, após backup preservado e validação da branch correta.
2. Antes de reabrir retiradas após a migração, revisar os atendimentos existentes que ficarão pendentes e registrar aprovação/recusa pela coordenação.
3. Conferir que contas individuais da coordenação e dos atendentes têm os privilégios certos.
4. Ativar e provar uma cópia externa, bem como ensaiar recuperação.
5. Conferir o fluxo num Android físico com os voluntários e validar os critérios sociais/documentos aprovados pelo instituto.

Os resultados técnicos demonstram que esta cópia local funciona nos cenários testados; não significam que a versão hospedada esteja atualizada ou pronta para uso real.
