# Guia de atendimento — Alimento é Vida

## Uso no dia a dia

O sistema é acessado pelo navegador do celular Android e precisa de internet. Cada colaborador usa sua própria conta; os registros ficam numa base compartilhada. Entre pelo endereço que a coordenação fornecer e adicione a página à tela inicial do telefone para abri-la como atalho. Não compartilhe senhas.

O menu separa as tarefas: **Início** mostra o resumo, **Cadastrar família** inicia um atendimento, **Triagem** permite à coordenação analisar solicitações, **Agenda** mostra entregas próximas, **Retiradas** registra a cesta do dia, **Consulta** localiza cadastros e **Relatórios** gera PDF. As telas de consulta não fazem alterações. A tela de cadastro e o histórico guardam apenas as informações necessárias ao atendimento.

## Cadastro e triagem

1. Antes de cadastrar, pesquise pelo CPF, nome e endereço. Reutilize a família existente quando for a mesma unidade familiar. O CPF válido do responsável é obrigatório; informe também RG ou outro documento de identificação. O sistema impede CPF repetido e impede duas famílias com benefício ativo no mesmo endereço. Coincidências de endereço aparecem para análise, e não devem ser contornadas criando outro cadastro.
2. Registre nome, nascimento, contato, endereço, quantidade de moradores, motivo principal da solicitação e informações essenciais da situação social. Se houver crianças, informe a frequência escolar ou por que a informação não se aplica. Não escreva detalhes pessoais que não sejam necessários para decidir o atendimento.
3. Confirme que CPF e identificação foram vistos e que o comprovante de endereço foi conferido. O sistema não recebe imagens nem anexos. O cadastro fica **Aguardando triagem**; nenhuma cesta pode ser entregue antes da decisão.
4. A coordenação confere documentos e dados, corrige o essencial no formulário de triagem e registra uma justificativa. Pode aprovar ou recusar. A decisão, o responsável e o horário ficam no histórico. Dados incompletos precisam ser corrigidos antes da aprovação.

## Duração, agenda e entrega

- Com crianças, a duração inicial autorizada pode ser de 1, 2 ou 3 meses. Sem crianças, é uma cesta. A duração e a condição da família ficam registradas no benefício.
- Cada período tem uma entrega mensal agendada para o segundo sábado. O horário padrão é configurável pela coordenação. A primeira data é o próximo segundo sábado a partir do início do atendimento.
- Na tela **Retiradas**, confira o nome da família e quem está recebendo. Registre a entrega somente na data autorizada. O sistema impede duas entregas para o mesmo período.
- Se a família faltar, a cesta não acumula nem passa automaticamente para outro dia. Em doença ou emergência, somente a coordenação pode autorizar uma data alternativa, com justificativa e registro de comprovante quando solicitado. O atendente registra a entrega na data autorizada.
- Ao terminar o período autorizado, somente a coordenação pode conceder prorrogação excepcional. Ela escolhe quantos meses autorizar e registra a justificativa. Cada autorização fica no histórico; os novos períodos seguem a agenda do segundo sábado e não podem se sobrepor a outro benefício no endereço.

## Consulta, relatórios e proteção de dados

Pesquise famílias por nome, CPF ou endereço na aba **Consulta** e use o histórico para conferir triagem, períodos e entregas. A aba **Relatórios** exporta os resultados filtrados em PDF. Relatórios e fichas contêm dados pessoais: não os deixe em celular compartilhado, grupos de mensagem ou pastas públicas. Avise a coordenação se um aparelho com sessão aberta for perdido e encerre a sessão após o atendimento.

As ações críticas e correções são registradas com autoria e justificativa. Não apague nem recrie famílias para corrigir dados ou reiniciar um prazo. Peça à coordenação para corrigir o cadastro mantendo o histórico. O sistema gerencia atendimento e entregas; não controla doações, estoque ou montagem das cestas.

## Acesso e operação técnica

A coordenação/responsável técnico cria e desativa contas individuais, mantém a hospedagem e configura o horário de distribuição. O primeiro acesso administrativo precisa ser configurado antes do uso. A equipe deve testar o fluxo com dados fictícios antes de registrar famílias reais.

Uma cópia de segurança gerada pela aplicação não significa que ela foi guardada fora do sistema. O responsável técnico precisa ativar e testar o destino externo e também ensaiar a recuperação. Nunca use arquivo de teste, dados reais ou credenciais de produção ao testar em outro ambiente.

## Hipóteses operacionais que a coordenação deve confirmar

O projeto implementa a duração de até três meses quando há crianças e uma cesta quando não há, conforme a orientação recebida. Antes do atendimento real, a coordenação deve confirmar critérios locais de vulnerabilidade, documentos aceitos, tratamento de exceções, quem pode receber a cesta, como determinar que pessoas no mesmo endereço formam famílias distintas e o horário do segundo sábado. O sistema registra a conferência e as decisões, mas não substitui avaliação social nem cria esses critérios.
