# Relatório de testes — usabilidade e responsividade

Execução em 06/11/2026. Testes técnicos realizados com contas e dados fictícios, em ambiente online separado, ligado à branch `validacao-inicial` do Neon. A produção não recebeu os cadastros de teste. Antes de publicar correções, foi gerada e validada cópia assinada da base atual, mantida privadamente em `work/` e excluída dos pacotes.

## Resultado consolidado

| Verificação | Resultado |
|---|---|
| Suíte Django/PostgreSQL | **32 testes aprovados**; execução final: 41,453 s |
| Concorrência e recuperação em bases descartáveis | **7 verificações aprovadas** |
| Telas × larguras, após correções | **84 combinações aprovadas** para largura do documento e datas pré-preenchidas |
| Fluxos pelo navegador | Cadastro, integrante, edição, entrega, repetição, busca, encerramento, login, logout, permissões, CSV e backup exercitados |
| Teclado | Login por Enter e abertura/fechamento da seção opcional por Enter funcionaram |
| Contraste dos textos de orientação amostrados | De **3,12–3,84:1** para **5,98–6,43:1** |

## Matriz de responsividade

Foram verificadas as larguras **320, 360, 390, 412, 768, 1024 e 1440 px**, com altura de 844 px na matriz. Cada largura foi aplicada às seguintes 12 telas:

1. Painel de atendimento.
2. Busca/lista de famílias.
3. Cadastro de família.
4. Ficha de família com nome e endereço longos.
5. Edição da família.
6. Inclusão de integrante.
7. Confirmação de entrega.
8. Registro histórico de entrega.
9. Correção dos dados da pessoa.
10. Configurações e backup.
11. Equipe.
12. Auditoria.

Após o carregamento completo, foram comparadas a largura de conteúdo e a largura útil do documento, além do valor efetivo dos campos de data preenchidos. **Nenhum caso final apresentou rolagem horizontal da página nem data preenchida invisível.** Tabelas largas continuam podendo rolar dentro de seu próprio contêiner, comportamento intencional para preservar a leitura dos registros. Os valores individuais estão em `responsividade.json`.

## Problemas encontrados e corrigidos

| Problema observado | Correção e confirmação |
|---|---|
| Painel/lista provocavam rolagem horizontal a 320 px | O texto acessível absoluto dentro da tabela escapava do contêiner. O contêiner passou a estabelecer seu posicionamento; matriz final sem transbordamento. |
| Datas existentes apareciam vazias no navegador | Os campos HTML de data recebiam texto localizado. Os widgets agora enviam ISO `AAAA-MM-DD`, mantendo a apresentação do navegador e dos históricos em português. Regressão específica e conferência DOM passaram. |
| Campos de reutilização confundiam o cadastro comum | Campos foram agrupados em seção opcional, fechada inicialmente. Os rótulos explicam que o número é interno, não CPF, e que uma pessoa nova não precisa desses dados. Abrir por teclado funcionou. |
| Caixas de seleção pequenas nas configurações | Área do controle ampliada para 44 × 44 px. |
| Textos de ajuda e orientação com pouco contraste | Cores escurecidas. Amostras do cadastro passaram para razões entre 5,98 e 6,43 contra o fundo. Isso não representa auditoria WCAG completa. |
| Botão Sair oculto no celular | Conta e botão passaram a aparecer na navegação móvel, com texto visível e alvo maior. Logout foi executado no celular e a tela de login reapareceu. |
| Confirmação ainda oferecida após entrega bloqueada | Botão passa a ficar desabilitado em retirada corrente indisponível. O bloqueio do servidor continua obrigatório e foi mantido/testado. |
| CSV recebia marcadores UTF-8 extras em linhas | A resposta passou a usar UTF-8 comum com um único marcador inicial. O download revelou o defeito; o teste de regressão e um segundo download real pela interface confirmaram exatamente um marcador no arquivo corrigido. |

## Percurso funcional observado no navegador

- Login com administrador fictício e painel com contadores coerentes com os registros de teste.
- Cadastro de família nova no celular, com seis períodos e início original preservado.
- Inclusão de dependente sem documento, conforme configuração inicial.
- Alteração de telefone com motivo; novo valor e auditoria apareceram na ficha.
- Confirmação mostrando família, período, recebedor e data visível.
- Gravação de uma retirada e mensagem de sucesso; a ficha passou a mostrar a retirada registrada.
- Novo envio para o mesmo período foi bloqueado, sem liberar outra cesta.
- Busca pelo documento encontrou exatamente a família criada.
- Ficha de benefício encerrado exibiu bloqueio e não ofereceu o link de confirmação.
- Seção de reutilização inicialmente fechada, com todos os controles de cadastro associados a rótulos; abertura por Enter confirmada.
- Saída da conta e novo login como atendente por Enter.
- Atendente não viu o menu administrativo e recebeu negativa ao abrir configurações diretamente.
- Download real do backup completo pela interface: JSON no formato esperado, assinatura presente e cinco famílias fictícias no arquivo.
- Download real do CSV, contendo a família fictícia; correção de codificação protegida por teste do conteúdo da resposta.

## Regressão, segurança e recuperação

A suíte cobre seis períodos, meses de tamanhos diferentes, virada de ano, entrega única, envio duplicado, encerramento, proibição de renovação/extensão, preservação após troca de responsável, documentos, vínculos, migração histórica, regras antigas preservadas, login, permissões, CSRF, anotações e autoria. Também cobre criação inicial do administrador, limitação de tentativas, suspensão de gravações, rejeição de cópia alterada, assinatura, confirmação externa e recusa de banco remoto sem TLS.

As sete verificações integradas exercitam gravações concorrentes, importação em banco separado, recusa de destino preenchido, exigência de administrador e comprovante do arquivo exato, cópia prévia, preservação da origem e manutenção da suspensão até liberação explícita.

## Evidências

- `responsividade.json`: 84 medições finais.
- `usabilidade-mobile.png`: cadastro no celular, seção opcional e botão Sair visível.
- `usabilidade-tablet.png`: ficha, integrantes, períodos e auditoria.
- `usabilidade-desktop.png`: painel no computador.
- `TESTES-USABILIDADE.txt`: execução final da suíte e recuperação.

## Limites da conclusão

Esta é uma **avaliação técnica e heurística**, com navegação real em um navegador e emulação de tamanhos. Não houve participante humano representando os voluntários, aparelho Android físico, leitor de tela, teste de zoom/sistema de fontes do Android, testes em vários navegadores ou medição de consumo/bateria/rede fraca. As capturas foram inspecionadas visualmente, mas a matriz não detecta todo problema de leitura ou compreensão.

Não foram feitos pentest, teste de carga destrutivo ou simulação de falha física/queda de provedor. Não se afirma certificação WCAG, ausência de qualquer defeito ou cobertura de todos os cenários possíveis. Antes do atendimento real, valide o percurso com os voluntários e seus próprios aparelhos.

O backup externo automático continua sem instalação e primeira execução confirmada. Os testes de geração e recuperação **não concluem essa proteção operacional**. Os cadastros fictícios e contas de ensaio ficam somente no ambiente de validação.

## Publicação das correções

Correções publicadas em produção em https://cestas-solidarias-seven.vercel.app. Deployment `dpl_7GUxTXmgHhBoFTfzTuxcNbfmjvBC`, estado READY. Login e CSS responderam HTTP 200, com as correções presentes. A consulta de logs de erro/fatal da versão final na janela de dez minutos não encontrou registros. O ambiente isolado permanece separado para repetição dos ensaios.
