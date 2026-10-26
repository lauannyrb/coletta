// Validação no navegador antes do envio, nos formulários com data-validate.
// Evita recarregar a página por um campo obrigatório esquecido (o que faria perder a imagem escolhida).
// É só conveniência: o servidor valida tudo de novo, e as mensagens seguem o mesmo visual das do Django.
(function () {
  'use strict';

  var iconTemplate = document.getElementById('icone-alerta');

  function messageFor(element) {
    var v = element.validity;
    if (v.valueMissing) return 'Este campo é obrigatório.';
    if (v.badInput) return 'Informe um número válido.';
    if (v.rangeUnderflow) return 'Informe um valor maior ou igual a ' + element.min + '.';
    if (v.rangeOverflow) return 'Informe um valor menor ou igual a ' + element.max + '.';
    if (v.tooLong) return 'Use no máximo ' + element.maxLength + ' caracteres.';
    return element.validationMessage;
  }

  function clearError(element) {
    var field = element.closest('.field');
    var list = field && field.querySelector('[data-client-error]');
    if (!list) return;
    list.remove();
    element.removeAttribute('aria-invalid');
    if (!field.querySelector('.field-errors')) field.classList.remove('field--error');
  }

  function showError(element) {
    var field = element.closest('.field');
    if (!field) return;
    clearError(element);
    // Erro que já veio do servidor para este campo: não duplica
    if (field.querySelector('.field-errors')) return;

    var list = document.createElement('ul');
    list.className = 'field-errors';
    list.id = element.id + '_client_error';
    list.setAttribute('data-client-error', '');
    var item = document.createElement('li');
    if (iconTemplate) item.appendChild(iconTemplate.content.cloneNode(true));
    item.appendChild(document.createTextNode(messageFor(element)));
    list.appendChild(item);

    var anchor = field.querySelector('.input-wrap') || element;
    anchor.insertAdjacentElement('afterend', list);
    field.classList.add('field--error');
    element.setAttribute('aria-invalid', 'true');
    var described = element.getAttribute('aria-describedby') || '';
    if (described.indexOf(list.id) === -1) {
      element.setAttribute('aria-describedby', (described + ' ' + list.id).trim());
    }
  }

  Array.prototype.forEach.call(document.querySelectorAll('form[data-validate]'), function (form) {
    form.addEventListener('submit', function (event) {
      var invalid = Array.prototype.filter.call(form.elements, function (element) {
        return element.willValidate && !element.checkValidity();
      });
      if (!invalid.length) return;

      event.preventDefault();
      invalid.forEach(showError);
      invalid[0].focus();
    });

    // Ao corrigir o campo, a mensagem do navegador some
    ['input', 'change'].forEach(function (type) {
      form.addEventListener(type, function (event) {
        if (event.target.willValidate && event.target.checkValidity()) clearError(event.target);
      });
    });
  });
})();
