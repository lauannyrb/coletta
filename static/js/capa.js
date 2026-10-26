// Prévia da capa no formulário de coleção.
// A imagem escolhida é mostrada direto do computador (URL blob:), antes de qualquer envio.
// A conferência no navegador é só conveniência: o servidor valida tudo de novo (colecoes/images.py).
(function () {
  'use strict';

  var field = document.querySelector('[data-cover-field]');
  if (!field || !window.URL || !URL.createObjectURL) return;

  var input = field.querySelector('input[type="file"]');
  var drop = field.querySelector('.cover-drop');
  var current = field.querySelector('[data-cover-current]');
  var preview = field.querySelector('[data-cover-preview]');
  var fileBox = field.querySelector('[data-cover-file]');
  var fileName = field.querySelector('[data-cover-name]');
  var warning = field.querySelector('[data-cover-warning]');
  var removeBox = document.querySelector('input[name="remove_cover"]');

  var MAX_BYTES = 2 * 1024 * 1024;
  var TYPES = ['image/jpeg', 'image/png', 'image/webp'];
  var objectUrl = null;

  function formatSize(bytes) {
    if (bytes < 1024 * 1024) return Math.max(1, Math.round(bytes / 1024)) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1).replace('.', ',') + ' MB';
  }

  function release() {
    if (objectUrl) URL.revokeObjectURL(objectUrl);
    objectUrl = null;
  }

  function showWarning(message) {
    warning.textContent = message;
    warning.hidden = !message;
  }

  function reset() {
    release();
    input.value = '';
    preview.hidden = true;
    preview.removeAttribute('src');
    fileBox.hidden = true;
    if (current) current.hidden = false;
    drop.classList.toggle('has-image', Boolean(current) && !(removeBox && removeBox.checked));
  }

  input.addEventListener('change', function () {
    var file = input.files && input.files[0];
    showWarning('');
    if (!file) {
      reset();
      return;
    }
    if (TYPES.indexOf(file.type) === -1) {
      reset();
      showWarning('Formato não aceito. Escolha uma imagem JPG, PNG ou WEBP.');
      return;
    }
    if (file.size > MAX_BYTES) {
      reset();
      showWarning('A imagem tem ' + formatSize(file.size) + '. O limite é 2 MB.');
      return;
    }

    release();
    objectUrl = URL.createObjectURL(file);
    preview.src = objectUrl;
    preview.hidden = false;
    if (current) current.hidden = true;
    drop.classList.add('has-image');

    fileName.textContent = file.name + ' · ' + formatSize(file.size);
    fileBox.hidden = false;
    // Escolheu uma capa nova: não faz sentido marcar "remover a capa atual"
    if (removeBox) removeBox.checked = false;
  });

  // Imagem que o navegador não consegue abrir (arquivo corrompido ou com extensão trocada)
  preview.addEventListener('error', function () {
    if (!objectUrl) return;
    reset();
    showWarning('Não foi possível ler esta imagem. Tente outro arquivo.');
  });

  field.querySelector('[data-cover-clear]').addEventListener('click', function () {
    reset();
    showWarning('');
    input.focus();
  });

  if (removeBox && current) {
    removeBox.addEventListener('change', function () {
      if (removeBox.checked) reset();
      current.classList.toggle('is-removing', removeBox.checked);
      drop.classList.toggle('has-image', !removeBox.checked || !preview.hidden);
    });
  }
})();
