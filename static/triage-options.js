(() => {
  const configurations = [
    {
      field: 'screening_notes',
      options: ['Desemprego ou perda de renda', 'Problema de saúde com impacto na renda', 'Situação emergencial', 'Dificuldade temporária para obter alimentos'],
      empty: 'Sem observações'
    },
    {
      field: 'reason',
      options: ['Documentos necessários não apresentados', 'Cadastro já possui atendimento ativo', 'Endereço já possui atendimento ativo', 'Critérios de atendimento não atendidos'],
      empty: 'Selecione uma justificativa'
    }
  ];

  document.querySelectorAll('#interview-form, .triage-content form').forEach(form => {
    configurations.forEach(config => {
      const field = Array.from(form.elements).find(element =>
        element.tagName === 'TEXTAREA' &&
        (element.name === config.field || element.name.endsWith('-' + config.field))
      );
      if (!field) return;
      const choices = document.createElement('select');
      choices.id = field.id + '_choice';
      choices.setAttribute('aria-label', config.field === 'reason' ? 'Justificativa para não aprovação' : 'Informações essenciais da triagem');
      choices.add(new Option(config.empty, ''));
      config.options.forEach(option => choices.add(new Option(option, option)));
      choices.add(new Option('Outros', '__other__'));
      const existing = field.value;
      choices.value = !existing ? '' : config.options.includes(existing) ? existing : '__other__';
      const custom = document.createElement('div');
      const label = document.createElement('label');
      label.htmlFor = field.id;
      label.textContent = config.field === 'reason' ? 'Descreva a justificativa' : 'Descreva as informações';
      field.parentNode.insertBefore(choices, field);
      field.parentNode.insertBefore(custom, field);
      custom.append(label, field);
      function update() {
        const isOther = choices.value === '__other__';
        custom.hidden = !isOther;
        field.required = isOther;
        if (!isOther) field.value = choices.value;
      }
      choices.addEventListener('change', () => {
        if (choices.value === '__other__') field.value = '';
        update();
      });
      update();
    });
  });
})();
