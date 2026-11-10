/* Animate menu navigation while leaving the browser in charge of loading pages. */
(() => {
  const content = document.querySelector('.app-workspace > main.main-shell');
  if (!content) return;
  let leaving = false;

  window.addEventListener('pageshow', () => {
    leaving = false;
    content.classList.remove('page-leaving');
  });

  document.addEventListener('click', event => {
    if (event.defaultPrevented || event.button !== 0 ||
        event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;

    const link = event.target.closest('.sidebar-nav a[href], .bottom-nav a[href]');
    if (!link || link.hasAttribute('download') || (link.target && link.target !== '_self')) return;

    const destination = new URL(link.href, location.href);
    if (destination.origin !== location.origin ||
        (destination.pathname === location.pathname && destination.search === location.search)) return;

    event.preventDefault();
    if (leaving) return;
    leaving = true;
    content.classList.add('page-leaving');
    window.setTimeout(() => location.assign(destination.href), 140);
    window.setTimeout(() => {
      leaving = false;
      content.classList.remove('page-leaving');
    }, 1200);
  });
})();
