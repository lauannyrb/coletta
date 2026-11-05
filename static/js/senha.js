(function () {
  'use strict';

  var template = document.getElementById('botao-senha');
  if (!template) return;

  document.querySelectorAll('.input-wrap input[type="password"]').forEach(function (input) {
    var button = template.content.firstElementChild.cloneNode(true);
    var showIcon = button.querySelector('[data-icon="mostrar"]');
    var hideIcon = button.querySelector('[data-icon="ocultar"]');

    input.parentNode.classList.add('input-wrap--password');
    input.parentNode.appendChild(button);
    button.setAttribute('aria-controls', input.id);

    button.addEventListener('click', function () {
      var visible = input.type === 'password';
      input.type = visible ? 'text' : 'password';
      button.setAttribute('aria-pressed', String(visible));
      showIcon.hidden = visible;
      hideIcon.hidden = !visible;
      input.focus();
    });

    if (input.form) input.form.addEventListener('submit', function () {
      input.type = 'password';
    });
  });
})();
