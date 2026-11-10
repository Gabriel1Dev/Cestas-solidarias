# Compatibilidade com o Projeto Alimento é Vida

## Revisão de interface — 08/11/2026

Navegação simplificada: agenda acessível pelo início e retiradas; configurações e histórico pelo menu da conta. As rotas e permissões permanecem, conferidas em banco local isolado; 17 testes passaram.

Navegação: a página inicial mostra resumo e atalhos, enquanto a busca cadastral fica na consulta; retiradas mantém acesso direto às entregas. Sem alteração das regras ou permissões. Django check e 17 testes de fluxo passaram em banco isolado.

Integração local do pacote do colaborador: app.css copiado integralmente, menu SVG adaptado às rotas atuais, com acesso da coordenação preservado. Django check e 17 testes de fluxo passaram; nove rotas autenticadas responderam em banco local isolado. A revisão visual renderizada permanece pendente. Sem publicação nesta rodada.

Verificação visual e de controles: busca com recuo e foco no contêiner, controles de 44 px, seletor de relatório de 48 px e ações do diálogo padronizadas. `manage.py check` sem erros e 50 testes Django passaram em banco isolado. Impeccable não encontrou ocorrências nos CSS; verificações dependentes de página renderizada permanecem pendentes.

Integração visual do pacote do colaborador: busca com ícone e recuo preservados, mantendo os filtros de triagem e regras atuais. A versão principal e o novo espelho foram sincronizados; 17 testes de fluxo passaram em banco local isolado. A auditoria de CSS isolado não substitui a conferência visual renderizada.

Revisão posterior de consistência visual: estilos compartilhados para painéis, filtros, botões, tabelas e relatórios; renderização autenticada de nove rotas conferida com banco local isolado. A conferência visual autenticada no navegador permanece pendente por bloqueio de acesso ao endereço local.

Ajustados o fundo da entrada, superfícies de atendimento, foco de teclado, resumo de erros e atalhos móveis para consulta e entregas. As regras de atendimento, triagem, prorrogação e datas permanecem as decisões documentadas abaixo. Em banco local isolado, 17 testes de fluxo e política passaram e `manage.py check` não apontou problemas. O navegador interno bloqueou o acesso ao ambiente local; a revisão visual e de interação autenticada permanece pendente.

## Atualização local de 08/11/2026

O usuário decidiu que uma pessoa usará uma conta, CPF existente será confirmado com histórico preservado, prorrogação será após o encerramento por 1 a 3 meses sem justificativa, e data real poderá ser diferente da prevista, sem entrega automática por ausência. Essas decisões substituem as interpretações anteriores sobre registro de entregas e justificativa de prorrogação.

As alterações deste ciclo permanecem locais e não foram publicadas. A confirmação de CPF leva ao histórico; se o atendimento aprovado terminou, a coordenação pode prorrogar de 1 a 3 meses, sem justificativa, preservando o cadastro. Cadastros pendentes ou recusados não iniciam novo ciclo por essa confirmação.

A coordenação revisa e pode ajustar composição familiar e duração inicial (1 a 3 meses, limitado a uma cesta sem crianças) durante a triagem. Períodos são recalculados somente enquanto o caso está pendente e sem entrega/prorrogação; a ação é auditada. Autorização excepcional exige horário. A migração 0011 preenche horários antigos com o horário previsto do período, ou com o horário institucional como alternativa, e torna o campo obrigatório. Backups antigos recebem o mesmo fallback durante restauração.

Datas previstas e reais são armazenadas separadamente; a data real pode ser passada ou diferente da previsão, desde que não anteceda o início do atendimento nem seja futura. Cada período aceita uma cesta. Importações históricas são restritas à coordenação, exigem data passada e são verificadas também no banco. O PDF não conta triagens nem recusas como atendimento ativo.

Validação local concluída em 08/11/2026: 50 testes Django e 7 verificações PostgreSQL passaram; migração 0011 aplicada em banco de teste. Playwright verificou login/triagem em 390 px, cadastro/entrega em 320 px, triagem em 768 px e início/ficha/relatórios em 1366 px, sem transbordamento nas telas verificadas. `collectstatic` corrigiu o asset CSS ausente. Não foi aplicado em produção, publicado ou enviado ao GitHub; dados reais/backups externos não foram inspecionados. Testes de interface não substituem validação com a equipe.

Parecer de 07/11/2026 (auditoria inicial): **parcialmente compatível; havia falhas funcionais e regras adicionais a revisar**. As atualizações locais acima tratam os itens identificados; a Vercel ainda não foi verificada.

Fonte: `REQUISITOS-CLIENTE-ORIGINAL.txt`, cópia integral do documento enviado pelo usuário. Aplicação avaliada: código local que originou o deployment `dpl_7rbnCGcTB2d46ya7D6jqtR3A7xAq`, confirmado READY e associado a https://cestas-solidarias-seven.vercel.app/. Nesta auditoria não houve alteração de código de produção, migração, publicação ou escrita em dados reais. Foram criados documentação e um script local de diagnóstico.

## Decisões do usuário que delimitam o escopo

- Controlar apenas atendimento e entregas. Doações, estoque, compras e montagem não fazem parte do sistema solicitado.
- Bloquear apenas atendimentos simultâneos no mesmo endereço; permitir reutilização do endereço após encerramento.
- Exigir CPF para novos atendimentos, inclusive responsáveis antes identificados apenas por RG.
- Coordenação define a quantidade de meses em cada autorização excepcional.
- Registrar confirmação e informações essenciais dos comprovantes, sem anexar arquivos.
- Uso em vários celulares Android com internet, banco compartilhado, login e uso simples.
- Não enviar ao GitHub sem solicitação explícita.

Estas decisões são esclarecimentos do usuário, não texto original do cliente. Se mudarem, revisar a matriz.

## Matriz de requisitos

| Documento | Requisito | Situação atual e evidência |
|---|---|---|
| 1 e 11 | Acolhimento e finalidade social | Linguagem de acolhimento no login; não é possível validar a prática humana por testes técnicos. Identidade visual ainda usa Cestas Solidárias, sem o nome oficial em todos os locais. |
| 2 | Uma cesta por CPF e endereço; sem duplicidade | CPF validado e normalizado; cadastro permanente por pessoa; uma entrega por período no banco. Endereço normalizado e bloqueado quando há sobreposição em `services.check_address_availability`. Grafias semanticamente equivalentes, como Rua versus R., não são deduplicadas automaticamente. Reutilização do mesmo CPF após encerramento é mais restrita que o documento: ver decisões pendentes. |
| 2–3 | Cadastro, triagem e avaliação socioeconômica | Implementados: status pendente, aprovação/recusa exclusiva da coordenação, motivo e histórico. Entrega normal depende de aprovação. |
| 3 | CPF, identificação e comprovante de endereço | CPF válido e identificação adicional exigidos; aprovação exige confirmação dos documentos e endereço. Ausência de anexos é decisão expressa do usuário. |
| 3 | Moradores, crianças, frequência escolar, motivo | Campos e validações presentes em FamilyForm e serviços; frequência ou justificativa obrigatória com crianças. Razões: desemprego, saúde, acidente/emergência, outras. |
| 4A | Até três meses com crianças | Cadastro e triagem oferecem 1–3 períodos. A coordenação pode corrigir quantidade/composição antes da aprovação; alterações são auditadas. |
| 4B | Uma cesta sem crianças | Implementado um período inicial, uma entrega por período. |
| 4C | Continuidade excepcional por avaliação da coordenação | Coordenação pode autorizar, após o encerramento, prorrogações sucessivas de 1–3 meses sem justificativa visível. A autorização e autoria ficam registradas. |
| 5 | Montagem no primeiro sábado | Fora do escopo operacional acordado; não há módulo de montagem. Não confundir com falta no módulo de atendimento. |
| 5–6 | Entregas no segundo sábado com data e horário | Datas regulares e horário padrão são registrados; exceção de data exige horário. Horários faltantes em autorizações antigas são completados na migração/restauração. |
| 6 | Faltas não geram reposição automática | Ausência não cria cesta nem prorroga atendimento. A coordenação registra a data real quando a entrega efetivamente ocorrer, sem duplicar período. |
| 6 | Exceção de data/horário por coordenação e justificativa | Permissão e justificativa implementadas; confirmação de comprovante disponível quando solicitado. Só uma exceção por período, dentro do período mensal e sem possibilidade de revisão: restrições não explicitadas pelo cliente. |
| 7–8 | Composição e origem das doações | Informações institucionais; estoque/doações/montagem foram excluídos do escopo pelo usuário. A lista de alimentos fica preservada no documento original, sem gestão no aplicativo. |
| 9 | Aproximadamente 25 atendimentos por CPF, não necessariamente famílias | Não é limite de capacidade. O PDF separa cadastros listados de atendimentos aprovados em andamento; pendentes e recusados ficam fora dos indicadores ativos. |
| 10 | Coordenação responsável | Perfil administrativo concentra aprovações e exceções. Nenhuma pessoa deve receber privilégios automaticamente com base apenas no nome escrito no documento. |

## Pendências confirmadas na auditoria inicial (correções locais; não verificadas em produção)

### Registro histórico — corrigido localmente

A rota histórica exige coordenação; serviço e gatilho recusam hoje/futuro, e o banco exige autoria de administrador para importação passada. Data real de entrega pode diferir da prevista pelo requisito posterior. A importação antiga continua disponível com justificativa e autoria auditada.

### Horário de exceção — corrigido localmente

Formulário e modelo exigem horário. Migração preenche nulos legados com horário previsto do período ou horário institucional; restauração de backups antigos aplica o mesmo fallback. As telas usam o horário autorizado.

### Duração na triagem — corrigido localmente

A coordenação pode corrigir moradores, presença de crianças, frequência escolar e duração antes de aprovar. Validação limita a 1–3 meses ou uma cesta sem crianças. A alteração de períodos só ocorre para triagem pendente, sem entrega nem prorrogação, e fica registrada no histórico. Teste web cobre mudança de 3 para 2 meses.

### Indicadores do PDF — corrigido localmente

Os totais ativos, disponíveis e encerrados contam apenas atendimentos aprovados nos estados adequados; triagem pendente e recusada não são exibidas como atendimento ativo.

### Data real, reagendamento e restauração — alinhados à decisão posterior

A data real pode divergir da prevista; serviço e gatilho validam atendimento aprovado, data não futura, início original e unicidade da cesta por período. Backups preservam previsão e data real. A ausência não cria lançamento automático; a equipe registra a entrega quando ocorre.
## Decisões já tomadas e limites técnicos

- CPF existente abre o histórico; atendimento encerrado é continuado na mesma ficha por autorização sucessiva de 1, 2 ou 3 meses após o período terminar, sem justificativa visível.
- O banco usa limite técnico de 32.767 períodos para manter identificadores seguros. Não há limite operacional de 120 períodos.
- Uma autorização de reagendamento por período continua sendo uma regra de implementação; pode ser revisada se a coordenação precisar alterar a exceção.
- A duração inicial é de até três entregas mensais, ancoradas no segundo sábado e ajustadas pela triagem. Ausência não acumula cesta nem cria prorrogação.
- A equipe registra confirmação e informações essenciais; não há anexos no sistema, conforme decisão do usuário.
## Evidências e limites

- Antes desta auditoria: 43 testes e 7 verificações PostgreSQL passaram na integração visual; isso não cobria os desvios acima.
- Auditoria inicial: quatro diagnósticos em `work/audit_client_requirements.py` reproduziram horário vazio, bypass histórico, duração não revisável e discrepância de gatilho/backup. As correções locais e sua cobertura constam acima; a produção não foi verificada.
- Análise estática de modelos, formulários, serviços, views, templates, cálculo de datas, triggers, validação de backup e PDF.
- `manage.py check --deploy --fail-level ERROR` retornou quatro avisos de SSL/HSTS/cookies porque a checagem foi executada com `CESTAS_LOCAL_TEST=1`; as configurações de segurança do ambiente hospedado não foram verificadas nesta rodada.
- Sem consulta aos dados pessoais de produção. Não verificados: configuração real do horário, cadastros antigos, evidência de backups externos ou validação com voluntários.

## Checklist permanente para mudanças

1. Relacionar mudança aos itens do documento e às decisões do usuário.
2. Preservar CPF/endereço sem sobreposição, triagem, duração e uma entrega por período.
3. Exercitar usuário atendente e coordenação; testar também URLs alternativas, POST manual e registro histórico.
4. Conferir agenda, exceções, horários e não reposição automática.
5. Alinhar regras de serviço, banco, backup e restauração.
6. Conferir indicadores, filtros, PDF e terminologia de atendimento por CPF.
7. Validar celular, navegação, erros e permissões no navegador.
8. Registrar resultados, limitações e pendências; não marcar conformidade total com lacunas abertas.

Cadastro para entrevista: CPF verificado no início, teclado apropriado para CPF e telefone, pergunta escolar condicional e uma cesta preenchida ao selecionar domicílio sem crianças. Django check e 17 testes passaram em banco isolado. No Chromium a 390 px, foram conferidos a ordem, o modo de entrada, a verificação de CPF por Enter e as mudanças da seção de crianças.

Na entrevista, a data predefinida fica em um ajuste recolhido, e a duração fica recolhida quando o domicílio sem crianças recebe uma cesta. Chromium a 390 px confirmou a edição da data, o envio do valor de duração e a exibição das perguntas condicionais.

Prévia local configurada para aceitar CPF e RG nos novos registros. O cadastro mantém CPF e seleciona RG automaticamente quando ele é o único tipo complementar aceito. Chromium confirmou o campo Número do RG e o tipo enviado. O formulário de configurações apresentou falha preexistente ao auditar o horário de distribuição. A configuração foi feita apenas no banco local isolado.

O aviso de backup no Início oferece download direto pela rota administrativa existente. Chromium a 390 px confirmou o download do JSON e a permanência no Início usando banco isolado. A confirmação da guarda externa segue separada.

Relatórios: indicadores gerais de cadastro e triagem, gráfico mensal de entregas pela data real e PDF com a paleta do sistema. Os filtros continuam restritos à exportação. Validados os totais com dados fictícios revertidos em banco isolado, exportação filtrada e vazia, download no Chromium e layout a 320, 390 e 1440 px. PDF fictício paginado conferido com Poppler.

Relatórios: a situação da triagem usa gráfico de rosca com contagens e percentuais, animado ao abrir a página quando há cadastros. O gráfico mensal e a exportação seguem separados. Django check e teste de exportação PDF passaram em PostgreSQL local. No Chromium, giro e preenchimento foram confirmados com números fictícios a 320 e 1440 px e o estado vazio a 390 px. Sem escrita em dados reais.
Triagem e cadastro: frequência escolar com opções selecionáveis e preservação de valores anteriores. Aprovação dispensa justificativa, recusa exige justificativa. Identificação duplicada informa o tipo do documento. Django check e 13 testes do fluxo passaram em banco isolado.
Cadastro e revisão: informações essenciais da triagem opcionais por decisão do usuário. O motivo principal continua solicitado. Django check e 13 testes do fluxo passaram em banco isolado.
Cadastro e triagem: opções predefinidas para informações essenciais e justificativa de não aprovação, com campo Outros. Observações existentes são preservadas. Django check e 13 testes do fluxo passaram em banco isolado.
Cadastro organizado em quatro etapas no navegador, preservando os campos e envio originais. Navegação inicial conferida no navegador local; Django check e 13 testes passaram em banco isolado. Falta validação do fluxo completo com a pessoa responsável.
Aviso de CPF existente recebeu ajustes de posicionamento e apresentação para telas pequenas. Django check sem erros. Validação visual do diálogo pendente.
