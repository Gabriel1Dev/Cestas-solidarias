# Estado para continuar a implantação

Data: 06/11/2026. O projeto online está separado da entrega local. Nenhuma senha ou conexão privada é guardada neste arquivo.

## Neon

- Organização: Gabriel — plano Free confirmado.
- Projeto: **Cestas Solidarias**.
- Região: São Paulo (`aws-sa-east-1`).
- PostgreSQL: 17.
- Projeto: `odd-cloud-91306564`.
- Branch de produção: `producao`, `br-purple-moon-b6kwhxjb`.
- Branch isolada: `validacao-inicial`, `br-blue-mouse-b6zrs03h`.
- Banco: `cestas`; papel proprietário: `cestas_owner`.
- Esquema completo aplicado nas duas branches, com 14 gatilhos de proteção. A base já possui cadastro de usuário e registros de atendimento; não trate a produção como vazia. Não recriar projeto ou trocar a branch ao continuar.

Obtenha a conexão pelo aplicativo Neon autorizado. Use endereço direto para migrações e pooled para o atendimento. Não coloque a conexão no repositório. As chaves operacionais estão configuradas como segredos de produção na Vercel. Não as substitua sem um procedimento de recuperação e preservação das assinaturas anteriores.

## Vercel

- Conta: `gabriel1dev`; espaço `gabriel1devs-projects`.
- Autorização do espaço concluída, sem reconexão da conta.
- Espaço: `team_EliQl5AdBDCSdmocrOFd77hq`.
- Projeto: **cestas-solidarias**, `prj_zmB8tvfSU0ogcsme96RcB1bYtTfU`.
- Endereço permanente: https://cestas-solidarias-seven.vercel.app.
- Deployment final: `dpl_DuPZGtLTgnZk4LSr4kHcNbxysa5Y`, estado **READY**, produção.
- Framework: Django; envio direto de arquivos, sem commit/repositório Git remoto.
- Conexão do banco, chave Django, chave de assinatura dos backups e token inicial estão como segredos de produção. Os hosts/origens exatos estão configurados na hospedagem. Não há segredos neste documento.
- O administrador inicial já foi criado pelo usuário. O link inicial fica bloqueado após a primeira conta; não existe senha padrão.
- Login e arquivos estáticos responderam HTTP 200 sem conta Vercel; famílias sem login redirecionam à autenticação; configuração inicial sem token retorna 404; com o link privado retorna formulário.
- A consulta dos logs da publicação final não encontrou erros fatais/de execução na janela verificada. Não há serviço externo de monitoramento/drain configurado.

## Dados e backup

O administrador inicial já foi criado pelo usuário. Ainda falta o agendamento de backup externo. Não há senha padrão. Configure o workflow somente em repositório privado, com os segredos e cotas verificados, e confirme o primeiro upload. O arquivo de origem e o guia estão nesta entrega. Não considere o atendimento liberado para uso real antes da conferência no Android e da cópia externa.

## Atualização de relatórios — 06/11/2026

Publicação READY com Equipe removida e relatórios PDF. Validada em ambiente separado com dados fictícios: 32 testes e sete verificações de recuperação aprovados; tela em 320, 390, 768 e 1440 pixels, sem transbordamento; download PDF realizado e renderizado. Produção conferida sem alterar registros reais: login HTTP 200, rotas antigas de usuários 404 e relatórios protegidos por autenticação.

## Organização por função

Atualização de consulta, cadastro, retiradas e relatórios documentada em MODULOS.md.
