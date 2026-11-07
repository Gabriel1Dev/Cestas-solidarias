# Validação da versão online

Executada em 06/11/2026 com dados fictícios. A versão local anterior foi preservada.

## Resultados

- **30 testes da aplicação aprovados** na execução final, em 39,445 segundos.
- **7 verificações integradas de concorrência, backup e recuperação aprovadas**, em bancos PostgreSQL locais criados especificamente para os testes.
- `manage.py check`: nenhum problema.
- `manage.py makemigrations --check --dry-run`: nenhuma migração pendente.
- `collectstatic`: Bootstrap e CSS locais preparados.
- `check --deploy --fail-level ERROR`, com configuração operacional: nenhum erro. Permanecem dois avisos sobre HSTS em subdomínios e inscrição em preload. Essas opções não foram habilitadas automaticamente; o domínio de hospedagem e sua política devem ser conferidos antes de alterá-las.
- Migrações e fluxo mínimo também **validados no Neon com PostgreSQL 17**, em branch separada. Foram exercitados os seis períodos, entrega única e backup assinado; os dados fictícios foram revertidos por transação. Confirmados 14 gatilhos de proteção.
- As mesmas migrações foram aplicadas ao banco de produção novo no Neon. Ele não recebeu usuários, pessoas ou famílias reais.

Resultados locais detalhados em `TESTES.txt`. A execução usa Python 3.12.14, Django 5.2.19 e PostgreSQL 18.6 temporário, além da verificação remota em PostgreSQL 17. O runtime PostgreSQL de teste ficou apenas em `work/`, sem serviço instalado no Windows e sem inclusão no pacote de entrega.

## Cobertura

As regras originais continuam cobertas: seis períodos; mês parcial; virada de ano; fevereiro e aniversários no dia 31; proibição de renovação, extensão e sétimo período; faltas sem acúmulo; troca de responsável sem reinício; documentos normalizados; reconhecimento de pessoa existente; endereço coincidente sem bloqueio automático; análise administrativa de ex-dependente; importação histórica; controle do recebedor; autoria e correções auditadas; login; permissões e CSRF.

A suíte online verifica compartilhamento entre duas sessões de celulares; limitação de tentativas no login; suspensão persistente do atendimento; backup restrito ao administrador; diferenciação entre arquivo gerado e guarda externa confirmada; rejeição de backup alterado; rejeição de conexão remota sem TLS. Os gatilhos e restrições são PostgreSQL, não simulações SQLite.

A suíte integrada verifica: duas conexões disputando a mesma entrega, com uma gravação; importação em outro banco com histórico preservado; destino existente recusado; recuperação restrita a administrador; comprovante do arquivo exato; cópia prévia e banco original preservados; ambos os bancos suspensos até liberação explícita. Os bancos de teste têm nomes aleatórios e foram removidos pelo próprio ensaio, sem abrir bancos reais da ONG.

## Infraestrutura confirmada

O Neon foi conectado durante o trabalho. A organização disponível informa plano Free. Foi criado o projeto **Cestas Solidarias**, em São Paulo, PostgreSQL 17, com branch **producao** e outra de **validacao-inicial**. Computação configurada no menor tamanho solicitado, com suspensão segundo o padrão permitido da conta gratuita. Nenhum plano pago foi contratado. A branch de validação foi mantida, sem dados fictícios persistidos; futuras alterações devem continuar isoladas da produção.

A Vercel foi conectada, a autorização do espaço foi concluída e a aplicação foi publicada em **produção**, estado **READY**, no endereço https://cestas-solidarias-seven.vercel.app. A configuração de dependências foi ajustada após a primeira compilação apontar ausência de Django; as listas do projeto e do instalador foram conferidas como iguais. O endereço permanente e o hostname único fornecido pela plataforma são aceitos sem curinga geral. Os segredos foram gerados e configurados somente no ambiente de produção. Nenhum usuário administrativo foi criado automaticamente com senha fixa.

O fluxo de backup automático foi implementado como arquivo de workflow privado, mas **não foi instalado nem executado no GitHub**. Não há confirmação de guarda externa nesta entrega. Os testes demonstram geração e recuperação; não comprovam disponibilidade de um dispositivo ou conta independente real.

## Pendências antes do atendimento real

Criar o primeiro administrador pelo link privado, conferir o atendimento após login e no Android real, instalar e exercitar o backup externo, ensaiar recuperação operacional e aprovar as hipóteses descritas no guia. O workflow de backup está fixado em commits dos repositórios oficiais das ações, mas ainda não foi ativado.

A tela de login publicada foi aberta e conferida no navegador. Na largura de 390 px, o documento apresentou largura de conteúdo de 390 px, sem transbordamento horizontal. Os campos e o botão estavam presentes, e os arquivos CSS locais responderam HTTP 200. A recusa anterior para localhost não foi contornada; esta conferência aconteceu no endereço online da aplicação após a autorização da Vercel. O formulário inicial foi verificado por HTTP com/sem token; a criação de credenciais foi deixada para o próprio usuário. As duas novas provas automatizadas confirmam que o token é obrigatório e que o link é desativado após a primeira conta.

No deployment final: login HTTP 200; famílias sem autenticação HTTP 302 para login; configuração sem token HTTP 404; configuração pelo link privado HTTP 200; respostas com dados de sessão sem cache. A busca de logs de erro/fatal da publicação final, na janela de dez minutos consultada, não encontrou registros. Isso não é monitoramento contínuo. Não há drain/serviço externo de observabilidade instalado. Não foram feitos testes em Android físico, falha de provedor/disco ou perda de contas externas. Não há promessa de perda zero ou gratuidade permanente de terceiros.

## Auditoria posterior de usabilidade

Foram executados 32 testes da aplicação, sete verificações integradas e 84 combinações de responsividade. O relatório mais recente é AUDITORIA-USABILIDADE.md. Foram corrigidos campos de data, rolagem horizontal, saída no celular, contraste, áreas de toque, seção opcional de pessoa existente, confirmação indisponível e codificação CSV. Publicação atual: dpl_7GUxTXmgHhBoFTfzTuxcNbfmjvBC, READY.
