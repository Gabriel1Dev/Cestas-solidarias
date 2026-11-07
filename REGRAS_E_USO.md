## Atualização: relatórios em PDF e remoção de Equipe

A seção Equipe e suas rotas foram removidas a pedido do usuário. As contas existentes e os autores dos registros continuam preservados. A gestão excepcional de contas fica com o responsável técnico, pelas ferramentas administrativas do Django, sem uma seção no atendimento.

O menu Relatórios abre uma tela com busca por nome/documento/endereço e seleção de situação. Baixar relatório em PDF gera um arquivo A4 paisagem com nome do instituto, data e autor da emissão, filtros, resumo, tabela das famílias e páginas numeradas. Os cabeçalhos se repetem nas páginas seguintes. A exportação exige login, é auditada e não substitui backup. A exportação CSV anterior foi descontinuada.

Para executar os testes, instale também requirements-dev.txt. A geração usa ReportLab e fontes incluídas na própria dependência; não precisa de serviços externos ou mensalidades.

---

# Guia de atendimento e regras

## 3. Guia breve de uso

**Equipe:** o administrador cria contas individuais em Equipe. Atendentes cadastram/consultam famílias, corrigem cadastros com motivo, registram entregas e exportam CSV. Administradores também gerenciam usuários, configurações, backups e auditoria. Uma conta ativa sem o grupo `Atendentes` e sem privilégio de administrador não tem acesso ao atendimento. Desative contas que deixaram a equipe; preserve a autoria histórica. Não há painel Django Admin genérico que permita editar benefícios ou entregas.

**Cadastrar:** informe responsável, documento, nascimento, contato, endereço e **início original** do atendimento. O sistema cria identificador permanente e seis períodos imediatamente. Confira o início no papel: ele não poderá ser trocado para estender o benefício. Documento coincidente informa a pessoa já cadastrada; não crie outra identidade. Consulte pelo documento e reutilize a família existente. Os identificadores de pessoas aparecem na ficha da família.

**Integrantes:** inclua parentesco e nascimento. Documentos são opcionais por padrão. Uma pessoa existente é vinculada pelo identificador, sem apagar vínculos anteriores. Vínculos com outra família exigem análise e motivo por um administrador. Documentos são normalizados (letras maiúsculas, sem espaços/pontuação/acentos), e o número normalizado é único em todos os tipos: coincidências entre emissores ou tipos exigem conferência humana, não geração de outro número fictício.

**Possível duplicidade:** nome, nascimento ou endereço coincidentes aparecem como alerta na ficha. Endereço igual não bloqueia automaticamente. A busca aceita nome, documento e endereço. Se uma pessoa não possuía documento no papel, compare com atenção os vínculos antes de criar outra pessoa; nomes sozinhos não estabelecem identidade. A aplicação não consegue provar que duas declarações com documentos diferentes são a mesma família. Essa identificação exige análise do instituto.

**Retirada:** busque a família, abra a ficha, confira a situação e clique Confirmar entrega. Na confirmação, confira família, número do período e pessoa que retirou. Somente integrante vinculado pode retirar nesta versão; se o instituto aceitar terceiros, essa necessidade precisa ser validada antes de alterar o fluxo. A gravação verifica novamente datas, vínculos e duplicidade no servidor. Clique duplo/envio repetido não cria segunda cesta. A restrição única do banco protege também gravações concorrentes.

**Trocar responsável:** inclua/reutilize a pessoa como integrante identificado e use Editar cadastro. Informe motivo. O identificador da família, o início e os períodos permanecem iguais. Responsáveis originais ou atuais não podem simplesmente recriar a família para iniciar outro ciclo.

**Ex-dependentes:** não há proibição vitalícia de formar outra família. Um administrador pode reconhecer uma pessoa já cadastrada como responsável de outra família **com análise documentada de que se trata de uma unidade familiar distinta**. Isso não é mecanismo de renovação da família anterior. A definição operacional e o procedimento de revisão ainda precisam ser aprovados pelo instituto. Caso seja a mesma família, consulte e atualize o registro permanente; não aprove um novo cadastro. Uma análise humana incorreta não pode ser resolvida apenas pelo documento ou endereço.

**Correções:** nomes, nascimento, endereço, telefone e responsável exigem motivo e guardam antes/depois. Documentos anteriores ficam como identificadores para evitar que uma correção elimine a ligação com a pessoa; acrescente o documento correto e explique a origem. Se um número antigo pertencia a outra pessoa, suspenda novos cadastros relacionados e peça análise técnica para correção assistida, com backup e auditoria; a interface não faz fusão ou transferência automática. Entregas não são removidas nem reabertas. Administradores podem anexar uma anotação de correção à entrega, preservando o original e sem liberar nova retirada. Erro no início original também exige análise técnica documentada; não há edição de vigência pela interface.

**Painel e CSV:** o painel mostra famílias em atendimento, retiradas no mês, pendências, proximidade de término (30 dias) e encerrados. Os totais de entregas usam a data efetiva, inclusive registros históricos. Exportar relatório gera um CSV com famílias, datas e situação. Ambos os perfis de atendimento estão autorizados ao relatório; o acesso exige login e é auditado. Os arquivos exportados contêm dados pessoais: guarde-os em local privado. CSV não inclui o banco completo nem substitui backup.

## 4. Regras fixas e hipóteses provisórias

As regras fixas não são configurações: benefício da família; uma cesta por período; seis períodos consecutivos; sem acúmulo por falta, extensão ou renovação. Depois do último limite, novas entregas correntes são bloqueadas, mas cadastro, entregas e auditoria permanecem. É permitido importar uma entrega histórica válida dentro dos períodos originais, mesmo depois do encerramento; isso registra o papel, não uma retirada atual.

Premissas iniciais: documento obrigatório do responsável; documentos de dependentes opcionais; telefone opcional; tipos CPF, RG e Outro; mês do calendário; primeiro mês parcial conta como mês 1. Exemplo: início em 31/01/2025 gera primeiro período 31/01 e último período em junho; o bloqueio começa em 01/07/2025. **Seis meses não foram convertidos em 180 dias.**

O modo alternativo usa aniversários mensais ancorados na data original. Exemplo: 31/01/2024 → 29/02 → 31/03. O cálculo usa sempre a âncora original, evitando deriva do dia após fevereiro. Datas finais no banco são limites exclusivos; a ficha mostra o último dia incluído.

Em Configurações, o administrador ajusta tipos de documento, documentos de dependentes, obrigatoriedade de telefone, nome do instituto, contagem **dos novos benefícios**, destinos/intervalo/retenção de backup. Cada benefício guarda modo, versão da política e as seis fronteiras de datas. Alterar configuração não recalcula atendimentos ou entregas passadas. A identidade visual inicial é provisória; cores e marca visual ficam em `static/app.css` e `templates/base.html`.

Validações pendentes com o instituto: conceito de família que compartilha endereço; critérios e responsáveis pela análise de ex-dependente formando família distinta; documentos aceitos e eventuais colisões entre tipos; documentos de dependentes; calendário ou aniversário; contatos obrigatórios; retirada por terceiros; política de correções excepcionais de cadastro e início; nome/marca; acesso aos CSV; equipamento/rede; responsáveis por backup, destino externo, intervalo, retenção e calendário de ensaios.

## 5. Migrar os cadastros do papel

1. Escolha um lote pequeno e confira duplicidades antes de digitar.
2. Cadastre uma família com sua **data original**, inclusive se já encerrada. Cadastro no sistema e início do benefício são datas distintas.
3. Inclua integrantes. Reutilize identidades existentes quando houver documentos coincidentes; não copie a mesma pessoa com grafia diferente.
4. Na ficha, use Registrar retirada do papel. Informe data efetiva, quem retirou e referência à folha/caderno ou outra fonte. O sistema registra quem digitou e quando, além da data passada.
5. Confira os seis períodos e as entregas com outra pessoa da equipe. Não presuma que ausência de anotação prova uma falta; os relatórios representam apenas os registros conhecidos.
6. Faça backup validado após cada lote. Guarde o papel durante a conferência segundo o procedimento do instituto.

