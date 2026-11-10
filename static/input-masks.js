/* Formatação de entrada. O servidor continua validando os dados enviados. */
(() => {
  function cpfMask(value) {
    if (!/^[\d.\s-]*$/.test(value)) return value;
    const digits = value.replace(/\D/g, '');
    if (digits.length > 11) return value;
    return [digits.slice(0, 3), digits.slice(3, 6), digits.slice(6, 9)]
      .filter(Boolean).join('.') + (digits.length > 9 ? '-' + digits.slice(9) : '');
  }

  function rgMask(value) {
    const compact = value.replace(/[.\s-]/g, '');
    if (!/^\d{8}[\dXx]$/.test(compact)) return value;
    return compact.replace(/^(\d{2})(\d{3})(\d{3})([\dXx])$/, '$1.$2.$3-$4').toUpperCase();
  }

  function phoneMask(value) {
    if (!/^\+?[\d().\s-]*$/.test(value)) return value;
    const digits = value.replace(/\D/g, '');
    const international = value.startsWith('+55');
    if (value.startsWith('+') && !international) return value;
    const local = international ? digits.slice(2) : digits;
    if (local.length > 11) return value;
    const prefix = international ? '+55 ' : '';
    if (local.length <= 2) return prefix + local;
    const subscriber = local.slice(2);
    const split = local.length === 11 ? 5 : 4;
    const number = subscriber.length > split ?
      subscriber.slice(0, split) + '-' + subscriber.slice(split) : subscriber;
    return prefix + '(' + local.slice(0, 2) + ') ' + number;
  }

  function applyMask(input, format) {
    const original = input.value;
    const formatted = format(original);
    if (formatted === original) return;
    const active = input === document.activeElement;
    const position = input.selectionStart;
    const symbolsBefore = (original.slice(0, position).match(/[\da-z]/gi) || []).length;
    input.value = formatted;
    if (!active || position === null) return;
    let caret = 0;
    let count = 0;
    while (caret < formatted.length && count < symbolsBefore) {
      if (/[\da-z]/i.test(formatted[caret])) count++;
      caret++;
    }
    input.setSelectionRange(caret, caret);
  }

  for (const input of document.querySelectorAll('form input[type="text"][name], form input[type="tel"][name]')) {
    const match = input.name.match(/^(.*-)?(cpf_number|identity_number|number|phone)$/);
    if (!match) continue;
    const [, prefix = '', field] = match;
    const typeField = input.form.elements.namedItem(prefix + (field === 'identity_number' ? 'identity_kind' : 'kind'));
    const documentType = () => field === 'cpf_number' ? 'CPF' : typeField?.value?.toUpperCase();

    function update() {
      if (field === 'phone') {
        input.inputMode = 'tel';
        input.autocomplete = 'tel';
        applyMask(input, phoneMask);
      } else if (documentType() === 'CPF') {
        input.inputMode = 'numeric';
        applyMask(input, cpfMask);
      } else {
        input.inputMode = 'text';
        if (documentType() === 'RG') applyMask(input, rgMask);
      }
    }

    update();
    input.addEventListener('input', event => {
      if (!event.isComposing) update();
    });
    input.addEventListener('compositionend', update);
    typeField?.addEventListener('change', update);
  }
})();
