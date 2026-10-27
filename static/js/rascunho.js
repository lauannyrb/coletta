// Rascunho do formulário de item: guarda o que foi digitado na sessionStorage desta aba e restaura ao voltar
// (ex.: ida até "Gerenciar campos" para criar um campo novo). Some ao salvar, ao cancelar ou ao fechar a aba.
// Só os campos de texto/seleção são guardados; o token CSRF nunca.
(function () {
  'use strict';

  var form = document.querySelector('form[data-draft]');
  if (!form) return;

  var key = 'coletta:rascunho:' + form.getAttribute('data-draft');
  var notice = form.querySelector('[data-draft-notice]');
  var storage;
  try {
    storage = window.sessionStorage;
    storage.getItem(key);
  } catch (error) {
    return; // navegador sem sessionStorage (ex.: bloqueado): o formulário funciona normalmente
  }

  function fields() {
    return Array.prototype.filter.call(form.elements, function (element) {
      return element.name && element.name !== 'csrfmiddlewaretoken' &&
        ['submit', 'button', 'file', 'hidden'].indexOf(element.type) === -1;
    });
  }

  function save() {
    var data = {};
    var filled = false;
    fields().forEach(function (element) {
      if (element.type === 'checkbox') {
        data[element.name] = element.checked;
      } else {
        data[element.name] = element.value;
        if (element.value.trim()) filled = true;
      }
    });
    if (filled) storage.setItem(key, JSON.stringify(data));
    else storage.removeItem(key);
  }

  function clear() {
    storage.removeItem(key);
  }

  // Restaura (campos novos que ainda não existiam no rascunho ficam vazios; campos removidos são ignorados)
  var saved = null;
  try {
    saved = JSON.parse(storage.getItem(key) || 'null');
  } catch (error) {
    clear();
  }
  if (saved) {
    fields().forEach(function (element) {
      if (!Object.prototype.hasOwnProperty.call(saved, element.name)) return;
      if (element.type === 'checkbox') element.checked = Boolean(saved[element.name]);
      else element.value = saved[element.name];
    });
    if (notice) notice.hidden = false;
  }

  // Só guarda depois que a pessoa mexe no formulário (abrir e sair da edição não cria rascunho)
  var dirty = Boolean(saved);
  var timer = null;
  form.addEventListener('input', function () {
    dirty = true;
    clearTimeout(timer);
    timer = setTimeout(save, 300);
  });
  form.addEventListener('change', function () {
    dirty = true;
    save();
  });
  // Antes de sair da página (ex.: clique em "Gerenciar campos"), garante o último caractere digitado
  window.addEventListener('pagehide', function () {
    clearTimeout(timer);
    if (dirty && !form.dataset.draftSent) save();
  });

  // Enviado: o rascunho não é mais necessário. Se o servidor recusar, os dados voltam preenchidos por ele.
  form.addEventListener('submit', function (event) {
    if (event.defaultPrevented) return; // bloqueado pela validação do navegador: mantém o rascunho
    form.dataset.draftSent = '1';
    clear();
  });

  var cancel = form.querySelector('[data-draft-discard-link]');
  if (cancel) cancel.addEventListener('click', function () {
    form.dataset.draftSent = '1';
    clear();
  });

  var discard = form.querySelector('[data-draft-discard]');
  if (discard) discard.addEventListener('click', function () {
    clear();
    dirty = false;
    form.reset(); // volta aos valores vindos do servidor (vazio no cadastro, dados atuais na edição)
    if (notice) notice.hidden = true;
    var first = form.querySelector('input:not([type="hidden"]), select, textarea');
    if (first) first.focus();
  });
})();
