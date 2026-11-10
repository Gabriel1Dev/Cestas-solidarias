# Implantação e manutenção — Cestas Solidárias

O [sistema de produção](https://cestas-solidarias-seven.vercel.app/) usa o projeto **cestas-solidarias** da equipe Vercel **gabriel1devs-projects**, com framework Django. O código está em [Gabriel1Dev/Cestas-solidarias](https://github.com/Gabriel1Dev/Cestas-solidarias).

O banco fica no projeto Neon **Cestas Solidarias**, região de São Paulo, branch **producao**, banco **cestas**, PostgreSQL 17. As migrações 0001 a 0011 estão aplicadas. As variáveis de produção ficam na Vercel. Use a conexão direta para migrações e a conexão pooled para a aplicação.

## Cópias de segurança

A rotina ativa fica no [repositório privado cestas-solidarias-backups](https://github.com/Gabriel1Dev/cestas-solidarias-backups). O agendamento consulta a hora da última cópia de hora em hora. O intervalo pode ser ajustado em **Configurações e backup**. O workflow usa um usuário PostgreSQL dedicado que lê os registros e confirma o envio. A primeira cópia foi confirmada em 10/11/2026. O agendamento antigo no repositório público foi desativado.

Confira a última execução bem-sucedida em **Actions** no repositório privado. O artefato contém **cestas.dump** e o checksum **cestas.dump.sha256**. O backup preserva cadastros, contas e histórico. Sessões e contadores de tentativas de login são descartados.

Se a exportação JSON do aplicativo recusar uma entrega antiga ligada a uma família que a migração marcou como pendente, use a cópia PostgreSQL. A coordenação pode revisar a ficha na triagem, preservando a entrega histórica.

## Recuperação

1. Baixe a cópia pelo repositório privado e confira o SHA-256.
2. Prepare um banco PostgreSQL 17 vazio e separado. Restaure com **pg_restore --exit-on-error --no-owner --no-privileges --dbname=CONEXAO_DO_BANCO_NOVO cestas.dump**. Passe a conexão de forma segura, sem registrá-la no repositório.
3. Confira migrações, contagens, gatilhos, acesso e histórico. Planeje a troca do banco da Vercel após essa conferência e preserve o banco anterior para retorno.

O ensaio local usa dados fictícios. A estrutura do arquivo de produção foi conferida no agendamento.

## Rotina de manutenção

- A responsável usa a conta da coordenação. A opção **Alterar senha** no menu da conta exige a senha atual. Em caso de perda de acesso, o técnico pode usar **python manage.py changepassword USUARIO** com a conexão direta de produção em um terminal privado.
- Use **python tests/run_all.py** com **CESTAS_TEST_DATABASE_URL** apontando para o PostgreSQL local para validar código e recuperação.
- Para mudar o esquema, ensaie a migração em banco isolado e confirme uma cópia externa antes de aplicá-la em produção. Para desfazer uma publicação de código, promova o último deployment saudável da Vercel. Reverta mudanças de banco pelo procedimento de recuperação.
