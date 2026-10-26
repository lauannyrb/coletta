// Filtros do detalhe da coleção: aplica assim que uma opção é escolhida.
// Melhoria progressiva: sem este script o botão "Aplicar" continua visível e funcionando.
(function () {
  'use strict';

  var form = document.querySelector('form[data-auto-submit]');
  if (!form) return;

  form.classList.add('is-auto');

  form.addEventListener('change', function () {
    // URL limpa: não envia filtros vazios nem a ordenação padrão
    Array.prototype.forEach.call(form.querySelectorAll('select'), function (select) {
      if (!select.value || (select.name === 'ordem' && select.value === 'recentes')) select.disabled = true;
    });
    form.submit();
  });
})();
