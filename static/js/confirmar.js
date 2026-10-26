// Confirmação de exclusão em modal.
// Links com data-confirm abrem o <dialog id="modal-excluir"> (app_base.html), que envia um POST com o token
// CSRF para a mesma URL da página de confirmação. Sem este script, o link abre essa página normalmente.
// Os textos vêm de atributos já escapados pelo template e entram via textContent, nunca como HTML.
(function () {
  'use strict';

  var dialog = document.getElementById('modal-excluir');
  if (!dialog || typeof dialog.showModal !== 'function') return;

  var form = dialog.querySelector('form');
  var label = dialog.querySelector('[data-modal-label]');
  var title = dialog.querySelector('[data-modal-title]');
  var text = dialog.querySelector('[data-modal-text]');
  var button = dialog.querySelector('[data-modal-button]');
  var opener = null;

  document.addEventListener('click', function (event) {
    var link = event.target.closest('a[data-confirm]');
    // Ctrl/Cmd + clique ou botão do meio: deixa abrir a página de confirmação em outra aba
    if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) return;
    event.preventDefault();

    opener = link;
    form.action = link.href;
    label.textContent = link.dataset.confirm;
    title.textContent = link.dataset.confirmName || '';
    text.textContent = link.dataset.confirmText || '';
    button.textContent = link.dataset.confirmButton || 'Excluir';
    dialog.showModal();
    dialog.querySelector('[data-modal-focus]').focus();
  });

  Array.prototype.forEach.call(dialog.querySelectorAll('[data-modal-cancel]'), function (cancel) {
    cancel.addEventListener('click', function () { dialog.close(); });
  });

  // Clique no fundo escurecido fecha (o Esc já é tratado pelo próprio <dialog>)
  dialog.addEventListener('click', function (event) {
    if (event.target === dialog) dialog.close();
  });

  dialog.addEventListener('close', function () {
    if (opener) opener.focus();
  });

  // Evita duplo envio
  form.addEventListener('submit', function () {
    form.querySelector('[type="submit"]').disabled = true;
  });
})();
