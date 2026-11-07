## Organização por função — 06/11/2026

- Visão geral: resumo e atalhos para as quatro tarefas principais.
- Consultar famílias: busca por nome/documento/endereço e situação, com cadastro e histórico sem botões de alteração ou entrega.
- Cadastrar família: acesso direto ao formulário existente.
- Retiradas: inicia com famílias que podem retirar; abre diretamente a confirmação de entrega. O nome da família abre os dados do atendimento para manutenção cadastral.
- Relatórios: exportação em PDF com filtros.

As listas de consulta e retiradas usam cartões no celular. Links antigos de listagem /familias/ redirecionam à consulta, preservando filtros. Não há migração ou mudança nos cadastros, nas regras de benefício, nos usuários ou nas permissões existentes.

Validação: 33 testes automatizados e sete verificações integradas PostgreSQL aprovados. Em dados fictícios online, conferidos busca, histórico sem ações de alteração e acesso ao formulário de entrega. Consulta, retiradas e início verificados em 320, 390, 768 e 1440 pixels, sem transbordamento da página. A avaliação é técnica; não substitui observação de uso com voluntários.

---

## Atualização: relatórios em PDF e remoção de Equipe

A seção Equipe e suas rotas foram removidas a pedido do usuário. As contas existentes e os autores dos registros continuam preservados. A gestão excepcional de contas fica com o responsável técnico, pelas ferramentas administrativas do Django, sem uma seção no atendimento.

O menu Relatórios abre uma tela com busca por nome/documento/endereço e seleção de situação. Baixar relatório em PDF gera um arquivo A4 paisagem com nome do instituto, data e autor da emissão, filtros, resumo, tabela das famílias e páginas numeradas. Os cabeçalhos se repetem nas páginas seguintes. A exportação exige login, é auditada e não substitui backup. A exportação CSV anterior foi descontinuada.

Para executar os testes, instale também requirements-dev.txt. A geração usa ReportLab e fontes incluídas na própria dependência; não precisa de serviços externos ou mensalidades.

---

# Cestas Solidárias — versão online para celulares Android

Esta versão atende à decisão tomada após a entrega inicial: voluntários usam **seus próprios celulares Android**, uma pessoa por vez, com internet disponível, e precisam compartilhar o mesmo histórico. Ninguém precisa instalar Python ou manter um computador ligado na ONG. O acesso será pelo navegador, com contas individuais. É possível criar um atalho do endereço na tela inicial do Android; isso não torna o sistema offline.

**Situação da entrega:** publicado em https://cestas-solidarias-seven.vercel.app, com banco no Neon e segredos configurados somente na hospedagem. O login e a proteção dos cadastros foram verificados em produção. O primeiro administrador deve ser criado pelo usuário através do link privado de configuração fornecido no chat; nenhuma senha padrão foi definida. O backup externo automático ainda não está ativo. A versão local e seu ZIP foram preservados separadamente. Veja `IMPLANTACAO.md` para continuar sem recriar a infraestrutura.

## Escolha técnica e custos

Mantidos Python, Django 5.2 LTS, templates e Bootstrap incluído no projeto. O SQLite em arquivo foi trocado por **PostgreSQL compartilhado**, pois o armazenamento local das funções da Vercel não serve como arquivo persistente de banco. As restrições, gatilhos, transações, bloqueio de manutenção e recuperação foram adaptados para PostgreSQL. Não usa IA, APIs pagas ou recursos essenciais de CDN. A hospedagem serve os arquivos estáticos preparados junto com o projeto.

O alvo de implantação é **Vercel para a aplicação e Neon para o banco**, ambos inicialmente em planos gratuitos. Isso depende da confirmação das condições aplicáveis à conta e à ONG. Não foi contratado plano ou fornecido cartão. Não há promessa de gratuidade permanente, disponibilidade contínua ou capacidade ilimitada: se o uso ultrapassar cotas, o serviço pode ficar indisponível até sua recomposição ou revisão da solução. **Não habilite migração automática para plano pago.** Se o uso não for elegível ao plano gratuito, não prossiga com uma contratação sem decisão explícita do responsável.

Na consulta de 06/11/2026, a página do Neon mostrava Free sem cartão e sem prazo definido, com limites de armazenamento, processamento e transferência. A Vercel restringe o Hobby a uso pessoal/não comercial; valide a situação do atendimento interno da ONG antes de publicar. O agendamento proposto usa GitHub Actions privado e também está sujeito às cotas gratuitas de execução e armazenamento. A retenção das cópias precisa caber nelas. Não publique o repositório para contornar custos, pois cópias e configurações exigem controle de acesso.

Referências oficiais: [Django na Vercel](https://vercel.com/docs/frameworks/full-stack/django), [SQLite na Vercel](https://vercel.com/kb/guide/is-sqlite-supported-in-vercel), [condições Hobby](https://vercel.com/docs/limits/fair-use-guidelines), [Neon Free](https://neon.com/pricing), [cobrança de GitHub Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions). Confira novamente antes da implantação, pois as condições podem mudar.

## Publicar — procedimento do responsável técnico

As instruções abaixo são para quem prepara o sistema; os voluntários só precisarão do endereço e da conta individual.

1. A autorização e a publicação na Vercel já foram concluídas. O projeto de banco no Neon já está preparado, conforme `IMPLANTACAO.md`: reutilize-o. Use apenas planos gratuitos elegíveis e um repositório **privado** se escolher integração Git e backup agendado. Não inclua dados reais, arquivos de backup ou credenciais no repositório.
2. Instale Python 3.12 no seu computador de desenvolvimento e prepare o ambiente nesta pasta:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

3. Configure os segredos como variáveis do ambiente, sem colocá-los no código ou enviar senhas pelo chat. `DATABASE_URL` é a conexão PostgreSQL do Neon, com TLS. Para migrações, ensaios e manutenção, prefira o endereço direto do banco. A conexão com pooler é permitida no atendimento: o bloqueio é transacional, não depende de uma sessão persistente.

| Variável | Valor necessário |
|---|---|
| `DATABASE_URL` | Conexão PostgreSQL privada, com `sslmode=require` ou verificação TLS mais forte |
| `DJANGO_SECRET_KEY` | Chave aleatória com pelo menos 40 caracteres, guardada fora do repositório |
| `CESTAS_HOSTS` | Host exato de produção, por exemplo `seu-projeto.vercel.app`, sem protocolo |
| `CESTAS_ORIGINS` | Origem HTTPS exata, por exemplo `https://seu-projeto.vercel.app` |
| `CESTAS_BACKUP_SIGNING_KEY` | Opcional: chave independente, com 40 ou mais caracteres; se ausente/vazia, usa a chave Django |

Gere as chaves localmente com o gerador criptográfico do Python. Preserve as chaves em local seguro separado do banco; elas não são incluídas no backup. Se a chave de assinatura for alterada, os arquivos anteriores precisam da chave original para validação. A amostra `.env.example` contém somente marcadores e não é carregada automaticamente. Nunca use seus marcadores como credenciais reais.

4. Aponte o ambiente do seu computador para o banco de produção recém-criado, confirme o host/banco e execute:

```powershell
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py check --deploy --fail-level ERROR
```

O administrador pode ser criado interativamente, sem senha padrão. Nesta implantação também foi preparado um link privado de configuração inicial: abra-o e escolha seu próprio usuário e senha. Ele deixa de funcionar quando a primeira conta é criada. A alternativa de linha de comando continua disponível. Migrações **não rodam automaticamente nos builds**, para que uma publicação de teste não altere a produção por acidente. Na atualização, faça backup e ensaio antes de aplicar novas migrações. As migrações desta versão são PostgreSQL e não devem ser executadas sobre o SQLite da entrega local.

5. Importe o repositório privado na Vercel, com esta pasta como raiz. Ela contém `manage.py`, `requirements.txt`, `pyproject.toml`, `vercel.json` e a entrada WSGI. Defina as variáveis no painel, com host/origem finais exatos, e publique a versão conferida. A integração Django da Vercel detecta a aplicação e prepara os arquivos estáticos. Use `DATABASE_URL` separada para ambientes de teste; não dê ao preview credenciais do banco real. **Não configure `CESTAS_LOCAL_TEST` na Vercel**: essa combinação é rejeitada pela aplicação.
6. Abra o endereço HTTPS no Android. Confira login, família fictícia, os seis períodos, confirmação de uma entrega e bloqueio da segunda. Confira também o logout e a negativa de acesso por conta sem permissão. Faça a primeira cópia completa e configure a guarda externa antes de inserir dados reais.

Não basta o endereço ser desconhecido para proteger os dados. Todas as páginas de cadastro, busca, exportação e backup exigem conta autorizada. O administrador cria e desativa usuários pela própria aplicação; não há painel genérico para renovar benefícios. O acesso HTTP é redirecionado para HTTPS em operação. Senhas são armazenadas como hashes pelo Django. O login limita tentativas incorretas por identificação de usuário/origem; após cinco falhas na janela, aguarda 15 minutos. Uma conta sem perfil de atendente ou administrador não acessa o atendimento.

## Uso diário no Android

1. Abra o endereço e entre com sua própria conta.
2. Busque nome ou documento antes de criar cadastro.
3. Confira responsável, integrantes, situação e período.
4. Confirme quem retirou e grave a entrega uma vez.
5. Saia da conta ao terminar. O próximo voluntário abre o mesmo endereço no celular dele e vê os dados compartilhados.

As alterações são gravadas no banco online, não em arquivos particulares de cada telefone. Sem internet, não registre entregas em uma cópia independente: isso comprometeria o controle central. Não há fila offline ou sincronização posterior nesta versão. Se uma operação falhar por conexão, consulte novamente a família antes de tentar confirmar, para verificar se a retirada já foi gravada.

Os botões e campos foram ampliados nas telas pequenas. A tela de login publicada foi conferida no navegador em largura de 390 px, sem transbordamento horizontal do documento. A validação no Android real, das telas após login e com os voluntários permanece pendente; os testes HTTP não substituem essa conferência. O documento `REGRAS_E_USO.md` detalha os seis períodos, as hipóteses provisórias, correções auditadas e a migração dos papéis.

## Backup e guarda externa

### Manual

O administrador usa **Configurações e backup → Baixar backup completo**. O arquivo JSON assinado contém pessoas, documentos, famílias, vínculos, benefícios, períodos, entregas, auditoria, configurações, contas e grupos. Não é o CSV de relatório e não é um simples TXT de cadastros. A exportação ocorre sob bloqueio transacional compartilhado entre todas as instâncias, sem depender de disco persistente no servidor.

O JSON inclui dados pessoais e hashes de senha: mantenha-o privado. A assinatura detecta alterações no conteúdo; **ela não criptografa o arquivo**. Guarde a cópia em dispositivo ou conta independente da hospedagem e preserve a chave de assinatura por procedimento separado. Não compartilhe backups por links públicos. Um download gerado não comprova guarda independente: a interface mostra geração e confirmação externa separadamente.

O download pela função tem um limite preventivo de 4 MB. Para bases maiores, o responsável usa seu computador, conectado ao banco com credenciais administrativas, sem esse limite de resposta web:

```powershell
.\.venv\Scripts\python.exe manage.py backup --output 'E:\BackupsONG\backup-2026-11-06.json'
```

O diretório deve existir; um arquivo existente não é sobrescrito. Depois de verificar que a cópia foi realmente guardada no dispositivo independente:

```powershell
.\.venv\Scripts\python.exe manage.py confirmar_backup 'E:\BackupsONG\backup-2026-11-06.json' --destino 'Dispositivo externo da ONG'
```

Isso registra local, data e hash, sem prometer que o equipamento continuará disponível. Não use a confirmação antes de copiar. O administrador técnico com credenciais de banco é responsável por esse registro; os atendentes não possuem essas credenciais.

### Automático

Foi incluído `.github/workflows/backup.yml`, preparado para um repositório **privado** no GitHub. Ele verifica de hora em hora se o intervalo desejado venceu (padrão 24 horas), gera o arquivo completo, envia um artefato privado e **só confirma a guarda depois de upload bem-sucedido**. Falhas tentam registrar indicação na aplicação; se o próprio banco estiver indisponível, confira também a execução do GitHub. Agendamentos podem atrasar, e o funcionamento real deve ser testado.

Configure os segredos do repositório:

- `CESTAS_DATABASE_URL`: conexão do banco, com TLS.
- `CESTAS_DJANGO_SECRET_KEY`: a mesma chave da aplicação.
- `CESTAS_BACKUP_SIGNING_KEY`: se uma chave independente foi definida na aplicação, use o mesmo valor aqui; caso contrário pode ficar ausente.

Habilite Actions, execute manualmente a primeira ocorrência, baixe o artefato e confira a confirmação na aplicação. Padrão provisório: 30 dias de retenção, ajustável entre 2 e 90 em Configurações, limitado pelas regras da conta/repositório. Cada execução cria outro artefato; versões antigas expiram segundo essa retenção. O trabalho só roda quando a guarda anterior está fora do intervalo. Confira cotas gratuitas e o espaço consumido; o código não habilita cobrança ou upgrade.

**Este agendamento ainda não está instalado nem ativo.** Até uma execução real e conferida, não considere concluída a proteção externa. O próprio backup do provedor, se disponível no plano escolhido, também não substitui uma cópia controlada pela ONG em conta/dispositivo independente. Mantenha cópias periódicas fora do GitHub se a política da instituição exigir outro meio.

## Recuperação com preservação do banco original

A recuperação é feita pelo responsável técnico; não há upload e substituição de banco pela tela. São necessários acesso administrativo ao banco, conta de administrador da aplicação, chave de assinatura e novos bancos privados. Use o mesmo código e migrações que geraram a cópia. Os arquivos de backup da edição SQLite não são importados diretamente; essa migração exige procedimento próprio e não era necessária nesta pasta, que não tinha dados reais.

1. **Ensaio:** crie um banco PostgreSQL vazio e separado, aplique nele as migrações desta versão e volte `DATABASE_URL` para a base atual. Defina `CESTAS_DRILL_DATABASE_URL` para esse banco de ensaio. Nunca use produção como destino. Execute:

```powershell
.\.venv\Scripts\python.exe manage.py ensaiar_restauracao 'E:\BackupsONG\backup.json' --comprovante 'E:\BackupsONG\comprovante-ensaio.json'
```

O arquivo é validado por assinatura, formato, versão das migrações, regras e seis períodos. A importação é feita no banco separado, em transação, com checagem de restrições e contagens. O destino permanece suspenso. Ele deve estar vazio de usuários, famílias e histórico; a ferramenta recusa substituição de dados existentes. Guarde o comprovante, que identifica o arquivo exato. O ensaio deixa dados privados no destino: proteja o banco e remova-o depois pelo procedimento do provedor quando não for mais necessário.

2. **Conferência operacional:** antes do primeiro uso real e nas revisões periódicas, confira também famílias, datas e histórico em uma instalação separada apontada para o banco de ensaio. Libere somente essa cópia com o comando de retomada para conferir no navegador, com acesso privado. Essa conferência visual não foi executada nesta entrega.
3. **Preparação da recuperação real:** crie outro banco vazio e aplique as mesmas migrações. Volte `DATABASE_URL` à produção e defina `CESTAS_RESTORE_DATABASE_URL` para o novo destino. Suspenda o agendamento de backup até concluir a troca. Escolha um caminho privado para preservar uma cópia do banco atual; ele não pode já existir.
4. **Recuperar:**

```powershell
.\.venv\Scripts\python.exe manage.py restaurar 'E:\BackupsONG\backup.json' --usuario SEU_ADMIN --comprovante 'E:\BackupsONG\comprovante-ensaio.json' --copia-atual 'E:\BackupsONG\backup-antes-recuperacao.json' --confirmar
```

O comando pede senha do administrador ativo na produção. Ele rejeita arquivo diferente do ensaiado e alteração das regras originais de famílias que ainda existem na base atual. Sob bloqueio compartilhado, guarda cópia do estado corrente, registra auditoria e ativa a suspensão persistente da produção. Depois importa em transação no **novo** banco, que também permanece suspenso. **Não sobrescreve nem exclui o banco original.** Se a importação falhar, a origem permanece preservada e suspensa até decisão explícita do administrador.
5. Confira contagens e amostras. Troque `DATABASE_URL` da hospedagem para o novo banco e republique a configuração; atualize o segredo correspondente do agendamento. As sessões antigas não constam do backup, exigindo novo login. Para liberar, aponte também o ambiente administrativo ao banco escolhido e execute:

```powershell
.\.venv\Scripts\python.exe manage.py retomar_atendimento --usuario SEU_ADMIN
```

O comando pede a senha de uma conta administrativa que exista **na base escolhida**, registra a liberação e só então permite o atendimento. Confira a conexão antes de liberar. Não libere o banco antigo e o novo ao mesmo tempo: isso criaria dois históricos divergentes. Mantenha o antigo suspenso, disponível para retorno. Para abortar antes da troca, retome explicitamente a base original; nenhuma família foi removida dela. Depois de concluir a conferência, faça nova cópia e reative o agendamento.

Como em qualquer restauração, registros posteriores ao instante do backup não aparecem na cópia recuperada. A base original e a cópia prévia ajudam a conferir e recuperar esses registros, sem fusão automática. Nem o provedor nem este procedimento garantem perda zero. Programe ensaios e acompanhe as cópias externas.

## Testes e manutenção

Os testes de unidade usam banco de teste Django. A suíte integrada cria bancos temporários com prefixo próprio, aplica as migrações reais, disputa uma entrega por duas conexões e exerce backup, ensaio, bloqueio e recuperação preservando a origem. A execução final está em `VALIDACAO.md` e nos arquivos de resultados. Não usa dados reais.

Para repetir, tenha PostgreSQL local de testes com permissão de criar bancos temporários e defina `CESTAS_TEST_DATABASE_URL` para uma conexão **em loopback**. Não use a conexão remota de produção:

```powershell
.\.venv\Scripts\python.exe tests\run_all.py
```

A suíte integrada recusa servidor remoto e remove somente bancos aleatórios que ela própria criou. O papel de produção não precisa dessa permissão por causa dos testes; use um ambiente separado para validar o código. Não execute `flush`, não remova gatilhos e não edite o benefício diretamente no banco para fazer uma renovação. O proprietário das credenciais técnicas ainda pode adulterar um banco fora da aplicação; restrinja essas credenciais.

Na atualização: preserve a versão anterior, gere uma cópia externa, ensaie em banco separado, aplique migrações pela etapa administrativa e publique o código. As regras de negócio e o fluxo de atendimento continuam descritos em `REGRAS_E_USO.md`. A configuração do servidor, as chaves e as credenciais não são procedimentos para os voluntários.

Pendências: acompanhar as condições e cotas dos planos gratuitos; criar o primeiro administrador e as contas reais; ativar/testar backup externo; validar no Android e com os voluntários; aprovar documentos, contagem mensal, conceito de família compartilhando endereço e análise de ex-dependentes formando outra família. A versão entregue não mudou essas hipóteses por conta própria.


### Primeiro acesso desta implantação

O endereço permanente é https://cestas-solidarias-seven.vercel.app. O link privado de criação do administrador foi entregue somente no chat e não está no código ou neste pacote. A variável `CESTAS_SETUP_TOKEN` está guardada como segredo na Vercel. Não a copie para o repositório. Quando existir qualquer conta no banco, a configuração inicial é bloqueada, inclusive se a conta for desativada. A senha é escolhida pelo usuário no navegador, com as validações do Django. O endereço permanente deve ser usado pelos voluntários; o link de configuração é apenas para o responsável inicial.

As dependências estão fixadas tanto em `requirements.txt` quanto em `pyproject.toml`: a Vercel prioriza o segundo. Mantenha as duas listas iguais ao atualizar. Esta publicação foi feita pelo envio direto dos arquivos através da integração Vercel, sem repositório Git remoto. Não há atualização automática por push configurada. Os IDs e o estado da publicação estão em `IMPLANTACAO.md`.
