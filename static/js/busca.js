// Busca em tempo real na barra do topo.
// Melhoria progressiva: sem este script a busca continua funcionando pelo Enter ou pelo botão "Buscar".
// O servidor devolve um trecho de HTML já escapado pelos templates (mesma view /busca/, ?parcial=1),
// então nenhum texto digitado pelo usuário é montado como HTML aqui.
(function () {
  'use strict';

  var form = document.querySelector('.search-form');
  if (!form || !window.fetch) return;

  var input = form.querySelector('input[name="q"]');
  var panel = document.getElementById('busca-resultados');
  var DELAY_MS = 250;
  var MIN_CHARS = 2;
  var timer = null;
  var controller = null;
  var lastQuery = null;

  function normalize(value) {
    return value.trim().split(/\s+/).join(' ');
  }

  function showPanel() {
    if (!panel.innerHTML.trim()) return;
    panel.hidden = false;
    input.setAttribute('aria-expanded', 'true');
  }

  function hidePanel() {
    panel.hidden = true;
    input.setAttribute('aria-expanded', 'false');
  }

  function clear() {
    if (controller) controller.abort();
    lastQuery = null;
    panel.innerHTML = '';
    hidePanel();
  }

  function search(query) {
    if (query === lastQuery) {
      showPanel();
      return;
    }
    if (controller) controller.abort();
    controller = new AbortController();

    var url = form.action + '?' + new URLSearchParams({ q: query, parcial: '1' }).toString();
    fetch(url, { credentials: 'same-origin', signal: controller.signal })
      .then(function (response) {
        // Sessão expirada: o Django redireciona para o login; não exibe essa página no painel
        if (!response.ok || response.redirected) throw new Error('busca indisponível');
        return response.text();
      })
      .then(function (html) {
        lastQuery = query;
        panel.innerHTML = html;
        if (document.activeElement === input || form.contains(document.activeElement)) showPanel();
      })
      .catch(function (error) {
        if (error.name !== 'AbortError') clear();
      });
  }

  input.addEventListener('input', function () {
    clearTimeout(timer);
    var query = normalize(input.value);
    if (query.length < MIN_CHARS) {
      clear();
      return;
    }
    timer = setTimeout(function () { search(query); }, DELAY_MS);
  });

  input.addEventListener('focus', showPanel);

  // Setas navegam pelos resultados; Esc fecha e volta para o campo
  form.addEventListener('keydown', function (event) {
    var links = Array.prototype.slice.call(panel.querySelectorAll('a'));
    var index = links.indexOf(document.activeElement);

    if (event.key === 'Escape') {
      hidePanel();
      input.focus();
    } else if (event.key === 'ArrowDown' && !panel.hidden && links.length) {
      event.preventDefault();
      links[Math.min(index + 1, links.length - 1)].focus();
    } else if (event.key === 'ArrowUp' && index !== -1) {
      event.preventDefault();
      if (index === 0) input.focus();
      else links[index - 1].focus();
    }
  });

  // Fecha ao clicar ou navegar com Tab para fora da busca
  document.addEventListener('click', function (event) {
    if (!form.contains(event.target)) hidePanel();
  });
  form.addEventListener('focusout', function (event) {
    if (event.relatedTarget && !form.contains(event.relatedTarget)) hidePanel();
  });
})();
