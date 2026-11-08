# Cestas Solidárias — Alimento é Vida

Aplicação web em português para atendimento familiar e registro da distribuição mensal de cestas. Foi pensada para voluntários usando celulares Android próprios, com internet, um atendimento por vez e histórico compartilhado.

## Estado desta cópia

O código local contém as alterações para os requisitos do cliente e onze migrações. **Esta cópia ainda não foi enviada ao GitHub nem publicada na Vercel.** O endereço de produção documentado em `IMPLANTACAO.md` corresponde ao código já hospedado e pode não incluir estas mudanças. Não use essa versão para operação conforme as novas regras até atualizar a publicação e validar a base correta.

**Atenção na atualização da base:** a migração de fluxo marca cadastros existentes como aguardando triagem. A coordenação precisa revisar os atendimentos ativos e aprová-los na aba Triagens antes que novas retiradas sejam liberadas. Preserve o banco anterior e ensaie a atualização em uma cópia antes de migrar a produção.

## Fluxo de trabalho

1. O atendente consulta CPF, nome ou endereço para localizar registros existentes.
2. Registra a solicitação com CPF e documento de identificação do responsável, endereço, número de moradores, presença de crianças, frequência escolar, motivo da solicitação e conferência dos documentos. Nenhum arquivo é anexado.
3. A solicitação fica pendente. A coordenação revisa e aprova ou recusa, registrando justificativa.
4. Após aprovação, são criados períodos mensais agendados para o segundo sábado. A regra de duração inicial é 1 a 3 meses quando há crianças e uma cesta quando não há crianças.
5. O atendente registra a entrega efetiva, separando a data prevista da real. Falta não acumula cesta nem muda a data automaticamente. Reagendamento exige justificativa da coordenação; prorrogação após o fim é rápida e autoriza 1, 2 ou 3 meses sem justificativa visível.
6. A equipe consulta o histórico e pode gerar relatório em PDF.

O escopo cobre atendimento e entregas. Doações, estoque e montagem das cestas não são controlados pelo sistema. Consulte `REGRAS_E_USO.md` para o guia da equipe, `MODULOS.md` para a navegação e `IMPLANTACAO.md` para infraestrutura e publicação.

## Executar localmente

Requisitos: Python conforme `.python-version` e PostgreSQL. Use uma base de desenvolvimento/teste separada, nunca a base hospedada com famílias reais.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
$env:DATABASE_URL = 'postgresql://usuario:senha@localhost:5432/cestas_dev?sslmode=disable'
$env:DJANGO_SECRET_KEY = 'uma-chave-local-apenas-para-desenvolvimento'
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Abra `http://127.0.0.1:8000/`. O aplicativo requer conexão ao PostgreSQL mesmo no desenvolvimento local. Em hospedagem, configure os segredos e use TLS para a conexão remota, seguindo `IMPLANTACAO.md`.

## Testes

Com um PostgreSQL de teste local capaz de criar bases temporárias, defina `CESTAS_TEST_DATABASE_URL` para `localhost` e rode:

```powershell
python tests\run_all.py
```

A execução local de 08/11/2026 passou em 50 testes Django e 7 verificações integradas de PostgreSQL, incluindo migração 0011 e restauração de backup antigo. `manage.py check` também passou. O navegador verificou fluxos de login e triagem em 390 px, páginas de atendimento/consulta em 320–768 px e desktop em 1366 px, sem transbordamento horizontal nem erros no console. Os resultados estão em `VALIDACAO.md` e `AUDITORIA-USABILIDADE.md`.

## Proteção de dados

Não inclua famílias reais em ambientes de demonstração ou teste. Não publique o repositório. Mantenha as credenciais em variáveis de ambiente/segredos da hospedagem, restrinja relatórios PDF e configure e teste uma cópia externa antes do uso real. O login é individual; desativar a autenticação exporia dados pessoais.
