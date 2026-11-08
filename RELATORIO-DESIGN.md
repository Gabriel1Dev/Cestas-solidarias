# Revisão visual — referência 3

GATE: FAIL 34 (rodada 2). A análise foi feita em uma captura estática da interface autenticada, com dados fictícios. Nenhuma exceção foi cadastrada.

A ferramenta verifica também regras de páginas promocionais, como hero em tela cheia, imagens nos cartões e uma seção por tela. A captura estática não reproduz a navegação autenticada. O contraste sinalizado na primeira rodada foi corrigido.

## Apontamentos abertos

- **hero-fill** — main#conteudo > div.overview-alert "! Cópia de segurança pendente. Confira a": the next section shows on the first screen: it starts at 235px on a 900px screen (the hero ends at 205px)
- **flush** — main#conteudo > div.overview-heading > a.btn.btn-primary "＋ Cadastrar família": its button sits 0px above the rule on top of div.overview-alert
- **flush** — main#conteudo > section.overview-metrics > div.metric-grid > a.overview-metric:nth-of-type(1) "Entregas para hoje ↗ 0 famílias agendada": its button sits 0px above the lower edge of section.overview-metrics, where the ground changes to section.overview-panel.overview-work
- **flush** — section.overview-panel.overview-work > div.overview-panel-footer > a > span "→": its button sits -350px above the rule on top of section.overview-panel.overview-find
- **nav** — (the first screen): no nav bar across the top of the first screen (a header with the brand, the section links and the main action)
- **card-visual** — main#conteudo > section.overview-metrics > div.metric-grid "Entregas para hoje ↗ 0 famílias agendada": 3 cards hold only text: no picture, icon, UI fragment or effect in any of them
- **button-styles** — main#conteudo > div.overview-heading > a.btn.btn-primary "＋ Cadastrar família": one button style (soft, fill #0a7382, outline #0a7382) with labels in 2 sizes: 14, 19px ("＋ Cadastrar família", "Buscar família")
- **heading-scale** — section.overview-metrics > div.metric-grid > div.overview-metric > strong "0": the figure "0" is set at 32px, larger than the section headings (h2 19px)
- **focus-ring** — button:focus:not(:focus-visible): "button:focus:not(:focus-visible)" in bootstrap.min.css removes the focus outline and sets nothing in its place
- **focus-ring** — .form-control-plaintext:focus: ".form-control-plaintext:focus" in bootstrap.min.css removes the focus outline and sets nothing in its place
- **focus-ring** — .form-range:focus: ".form-range:focus" in bootstrap.min.css removes the focus outline and sets nothing in its place
- **moment-none** — (the page): a software page (--type) deals no moment: every kind carries one, two on a long page (moments.md)
- **hero-screen** — main#conteudo > div.overview-heading "VISÃO GERAL / ATENDIMENTOSeu espaço de a": the hero ends at 205px on a 900px screen, 695px above the fold: it ends at the fold, 1px either way (SR-1)
- **hero-screen** — main#conteudo > div.overview-alert "!Cópia de segurança pendente. Confira a ": 665px of the next section shows on the first screen (from 235px on a 900px screen): nothing below the hero shows at load (SR-1)
- **section-height** — main#conteudo > div.overview-alert "!Cópia de segurança pendente. Confira a ": the section is 54px tall (0.1 screens), 846px short of one screen (900px): every section after the hero is one screen or two, 2px either way (SR-2)
- **section-air** — main#conteudo > div.overview-alert / main#conteudo > section.overview-metrics: 40px of air between the content of these two sections: 128-480px (64-600px WARN) (every gap out of the band at 1440px, top to bottom: 40px after "!Cópia de segurança ", 51px after "Visão geralAtualizad") (SR-3)
- **section-air** — main#conteudo > section.overview-metrics / main#conteudo > div.overview-columns: 51px of air between the content of these two sections: 128-480px (64-600px WARN) (SR-3)
- **one-section** — main#conteudo > div.overview-heading > div > h1 "Seu espaço de atendimento": the screen at scroll 0px (stride 0) shows 207px of section 3 and the heading of section 1 whole and the content of 3 sections, over 24px each beside section 4: a screen shows one section (another may peek 8px, 24px WARN) (SR-4)
- **one-section** — h2#overview-title "Visão geral": the screen at scroll 142px (the top of section 2) shows 207px of section 3 and the heading of section 3 whole and the content of 3 sections, over 24px each beside section 4: a screen shows one section (another may peek 8px, 24px WARN) (SR-4)
- **one-heading** — h2#find-title "Encontrar família": the section holds 2 h2 headings: one per section, first in its .wrap (SR-5)
- **one-heading** — h2#work-title "Entregas de hoje": headings of two sections show whole on one screen at 3 of 3 scroll positions (100%; at scroll 0, 50, 100px), here with "Visão geral": at most 3% on a desktop (SR-5)
- **container-edges** — main#conteudo > div.overview-alert "!Cópia de segurança pendente. Confira a ": the content of section 2 runs 346px from the left and 59px from the right (read from its outermost blocks: no .wrap): the page's container starts at 290px; 346 and 59px are not one margin; the margin is 64-120px at 1440px (one container, equal margins, 2px either way) (SR-6)
- **container-edges** — div.main-shell > header.topbar "Instituto • Cestas SolidáriasGestão de a": the nav's content runs 288px from the left and 40px from the right (read from its outermost blocks: no .wrap): 288 and 40px are not one margin; the margin is 64-120px at 1440px (one container, equal margins, 2px either way) (and 3 more like it: "VISÃO GERAL / ATENDIMENT", "Visão geralAtualizado em", "Entregas de hojeFamílias") (SR-6)
- **container-edges** — a.skip-link "Pular para o conteúdo": a <a> at the top of the page, outside header.nav, main, footer.closing and nav.actionbar (SR-6)
- **container-edges** — aside.sidebar "CestasSOLIDÁRIASATENDIMENTO ⌂ Início ⌕ C": a <aside> at the top of the page, outside header.nav, main, footer.closing and nav.actionbar (and 5 more like it: "Instituto • Cestas Solid", "VISÃO GERAL / ATENDIMENT", "!Cópia de segurança pend") (SR-6)
- **container-edges** — main#conteudo > div.overview-alert > span "!": a box runs 307-333px, outside the container lines of section 2 at 346-1381px: full width is for background layers and grounds only (SR-6)
- **container-edges** — h2#find-title "Encontrar família": the h2 starts 711px right of the container's left: every h1 and h2 starts on it, 2px either way (and 3 more like it: x 475, x 315, "Entregas de hoje") (SR-6)
- **container-edges** — main#conteudo > div.overview-columns > section.overview-panel.overview-work "Entregas de hojeFamílias com retirada au": a box over half the container wide runs 290-960px, not on the container's lines at 290-1398px (SR-6)
- **flush** — main#conteudo > section.overview-metrics > div.metric-grid > a.overview-metric:nth-of-type(2) "Atendimentos ativos ↗ 0 famílias aprovad": its button sits 0px above the lower edge of section.overview-metrics, where the ground changes to section.overview-panel.overview-work
- **fold-cut** — h2#work-title "Entregas de hoje": a 16px line is sliced by the bottom of the first screen (16px of it below the fold)
- **no-visual** — main#conteudo > section.overview-metrics "Visão geral": no picture, effect or mock in this section; a feature section needs a visual
- **no-visual** — main#conteudo > div.overview-columns > section.overview-panel.overview-work "Entregas de hoje": no picture, effect or mock in this section; a feature section needs a visual
- **text-only** — main#conteudo > div.overview-columns > section.overview-panel.overview-find "Encontrar família": the closing section is only text: no picture, icon, mock or effect in it
- **container** — page: no .wrap

A conferência visual usou uma captura de celular a 390 px; a suíte Django passou em 43 testes e houve 7 verificações PostgreSQL. Uma verificação adicional confirmou o contador no reagendamento. O uso com voluntários em Android físico continua pendente.
