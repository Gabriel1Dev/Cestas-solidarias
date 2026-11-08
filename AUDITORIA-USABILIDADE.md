# Auditoria de usabilidade e responsividade

## Verificação incremental de 08/11/2026

Playwright local, PostgreSQL de teste e registros fictícios. Login e triagem foram exercitados em 390 px; cadastro e tela de entrega em 320 px; triagem em 768 px; início, ficha e relatórios em 1366 px. Em todas as telas verificadas, a largura do documento permaneceu igual à viewport. Depois de gerar os arquivos estáticos, console do navegador terminou sem erros ou avisos.

A triagem permitiu ajustar a duração inicial e concluir a aprovação. Esta rodada encontrou e corrigiu o build dos arquivos estáticos: `workflow.css` não estava copiado para `staticfiles`, resultando em 404; foi incluído `collectstatic --noinput` no build da Vercel e a resposta local passou a HTTP 200.

Esta rodada é complementar e não repete a matriz antiga inteira. Os voluntários ainda precisam validar o fluxo em Android físico.

Execução local em 07/11/2026 com usuário e família fictícios, no Chromium via Playwright. Esta conferência não acessou a hospedagem.

## Matriz de telas

Verificadas as telas Início, Agenda, Consulta, Novo atendimento, Relatórios, Triagens, Configurações/backup e Auditoria, nas larguras 320, 360, 390, 412, 768, 1024 e 1440 px, com altura de 844 px. São 56 combinações. Após corrigir o estado sem resultados da Consulta, todas mantiveram a página dentro da largura disponível e renderizaram a área principal.

## Fluxo pelo navegador

- Login com conta temporária de teste e acesso ao menu.
- Formulário de atendimento: campos rotulados, CPF válido e documento, pergunta sobre crianças, duração inicial, endereço, moradores, frequência escolar, motivo, notas e confirmações de documentos.
- Envio do cadastro e confirmação visual de estado **Aguardando triagem**, sem liberar entrega.
- Ficha exibiu dados de residência, triagem, documentos conferidos e períodos mensais nas datas de segundo sábado.
- Relatório familiar foi baixado como PDF; console sem erros ou avisos após a exportação.

## Correção aplicada

A busca vazia da Consulta tinha uma tabela de largura intrínseca que ultrapassava a viewport em larguras inferiores a 436 px. O estado vazio passou a ser renderizado como mensagem própria; o layout responsivo foi repetido e as 56 combinações passaram.

## Limites da avaliação

Os fluxos foram exercitados com uma conta temporária e dados inventados numa base local. A coordenação e os voluntários ainda precisam avaliar a linguagem e os passos num Android real. Isso é necessário para confirmar a clareza para pessoas com pouca familiaridade com tecnologia e não pode ser substituído por uma medição automática de largura.
