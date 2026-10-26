# CLAUDE.md — Coletta

Este arquivo dá o contexto do projeto para o Claude Code. Leia antes de qualquer tarefa.

## 1. Contexto

O **Coletta** é um organizador pessoal de coleções, desenvolvido como atividade avaliativa da disciplina
**"Projeto Aplicado: Práticas de Mercado"** (pós-graduação Lato Sensu em Segurança da Informação e Análise
Forense, UNCISAL). Escopo oficial da disciplina:
https://github.com/ziraldocardoso/Projeto_aplicado-praticas_de_mercado/blob/main/Escopo_e_elementos_obrigatorios.md

**Prioridade máxima: economizar tempo.** A nota depende principalmente de infraestrutura, pipeline CI/CD e
mitigações de segurança, não da quantidade de funcionalidades. Manter o escopo pequeno, completo e seguro.
Não adicionar funcionalidades fora do escopo da v1 sem pedido explícito.

## 2. Requisitos obrigatórios da disciplina

### Eixo 1 — Infraestrutura (Cloud, Free Tier)
- Qualquer provedor de nuvem, usando apenas recursos gratuitos.
- SO obrigatório: **Ubuntu Server ou Debian**, última versão estável.
- Web server obrigatório: **Nginx** (escolhido) ou Apache.
- Aplicação acessível publicamente por **IP público** (sem domínio).
- SSH **somente com chave**; autenticação por senha desabilitada.
- Expor apenas as portas necessárias (80, 443 e 22).
- **Fail2Ban** na porta 22: `maxretry = 4`, `bantime = 24h`.
- HTTPS com **Certbot 5.4+**, certificado Let's Encrypt **emitido para o IP público**, com renovação automática.
- Redirecionamento automático de todo HTTP para HTTPS.
- Testes de TLS para acesso por **IP** (nosso caso):
  - **SSL.org** (https://www.ssl.org/): "Certificate Trusted: **YES**" e "Algorithm / Key Type & Size:
    **Good signature · Acceptable key**".
  - Suporte a **PQC (Post-Quantum Cryptography)** confirmado no **DigiCert PQC checker**
    (https://www.digicert.com/pqc-checker).
  - Qualys SSL Labs com nota A + PQC só é exigido se for usado domínio (não é o caso).

### Eixo 2 — Repositório
- GitHub, conta gratuita, repositório **público**.
- Commit/push via chave SSH ou PAT; 2FA recomendado.
- `README.md` detalhado, que funciona como **relatório técnico da entrega**.
- `.gitignore` obrigatório. **Proibido commitar**: `.env`, chaves SSH, credenciais de nuvem, senhas hardcoded,
  bancos de dados locais. Vazamento de credencial = penalidade imediata.

### Eixo 3 — Desenvolvimento
- Stack livre. Desenvolvimento com auxílio de IA (Antigravity ou equivalente).
- Mínimo exigido: **tela de login, página interna acessível só após autenticação, logout funcional**.
- Mitigar ativamente **no mínimo 3 categorias da OWASP Top 10:2025**, documentando no README quais são e
  onde/como o código as previne.

### CI/CD
- **GitHub Actions** fazendo deploy automático para o servidor a cada `git push origin main`.
- Credenciais (chave SSH do servidor etc.) **somente em GitHub Secrets**, nunca no workflow.

## 3. Produto — escopo da v1

Catálogo pessoal de coleções. Cada usuário tem seu próprio acervo.

**Incluído:** cadastro; login com e-mail e senha; logout; tela inicial com resumo do acervo; listagem de
coleções; CRUD de coleções; visualização dos itens de uma coleção; CRUD de itens; busca simples por nome de
coleção ou item; isolamento total de dados entre usuários.

**Fora do escopo:** compra/venda, trocas, rede social, preço de mercado, notificações, estatísticas avançadas,
compartilhamento público, app móvel, recuperação de senha por e-mail, mover itens entre coleções.

**Imagens (capa e foto de item):** adiadas. Só implementar se sobrar tempo, depois de todo o resto pronto
(ver seção 8).

### Telas
1. **Login:** e-mail, senha, botão entrar, link para cadastro, mensagens de erro claras.
2. **Cadastro:** nome, e-mail, senha, confirmação de senha.
3. **Tela inicial:** boas-vindas, total de coleções, total de itens, coleções recentes, ação "nova coleção",
   acesso a "Minhas coleções", sair. Valores sempre reais, nunca fixos.
4. **Minhas coleções:** cards com nome, descrição curta, quantidade de itens; criar, abrir, editar, excluir.
5. **Detalhes da coleção:** itens (nome, categoria) e ação para adicionar item.
6. **Formulários** de coleção e item; **confirmação de exclusão** (avisar que os itens serão removidos).
7. **Busca** com resultados e estado "nenhum resultado".

As telas seguem um **protótipo no Figma** feito pelo usuário:
https://www.figma.com/design/0DTj601qsIuCwQ0y7ZPmFL/Coletta
Frames: **Login**, **Início (Dashboard)** e **Brand Guide** (cores, tipografia, ícones, componentes e estados).
As demais telas seguem o Brand Guide. No Figma o nome aparece como "Colletta": no código usar sempre **Coletta**.

**Identidade visual (Brand Guide):** fonte **Plus Jakarta Sans** (400–800), servida localmente pela pasta
`static/`; cantos de 12px (botões, inputs) e 16–24px (cards, modais); ícones de traço fino (1.75–2px).
Tokens: roxo primário `#7655C8`, roxo escuro `#4D378B`, lavanda clara `#EEE8FA`, fundo `#FAF8FC`,
superfície `#FFFFFF`, bordas `#E8E1F0`, texto principal `#29233A`, texto secundário `#777184`.
Contraste medido (WCAG): `#7655C8` no branco = 5.38:1 (AA, **não** AAA como diz o guia); `#777184` no
lavanda = 3.92:1 (**reprova**), usar texto secundário só sobre branco/fundo ou escurecê-lo.

**Elementos do Figma que NÃO entram na v1** (fora do escopo ou sem dado real):
- Login: "Esqueci minha senha", botões Google/Passkey, "Lembrar de mim", "4.2k itens salvos hoje".
- Início: "Sincronizado", sino de notificações, "Plano Curador", selo "Ativa", atalho ⌘K, banner de dica
  sobre fotos, logo e usuário repetidos. "4 categorias" e "+3 este mês" ficam para depois.
- Cards de coleção sem foto (imagens adiadas): usar o card com a estrela do Brand Guide.
- Sair: botão com texto "Sair" dentro de formulário POST, não só ícone.
- Faltam no Figma: estado vazio do Início (RN30), versão mobile e as demais telas (seguir o Brand Guide).

## 4. Stack e decisões tomadas

| Item | Decisão |
|---|---|
| Linguagem | **Python 3.14**, gerenciado com **uv** (`.python-version` fixa 3.14) |
| Framework | **Django 6.1** |
| Front-end | **Templates do Django** (renderização no servidor). Sem SPA, sem Vue/React |
| CSS | **CSS puro**, sem framework e sem build: um `static/css/app.css` com a paleta do Brand Guide em variáveis CSS (`--color-primary` etc.) |
| Banco | **SQLite** |
| Servidor de app | **Gunicorn** como serviço systemd |
| Web server | **Nginx** como proxy reverso + arquivos estáticos |
| Config | `python-dotenv`, variáveis no `.env` (fora do Git) |

Motivos: o Django já entrega autenticação, hash de senha, CSRF, ORM parametrizado, migrações e validação de
formulários, o que reduz muito o trabalho e o risco. Python 3.14 é a versão mais nova suportada pelo Django 6.1
(o 3.15 ainda não é suportado). O sistema do desenvolvedor é Arch Linux desatualizado: **não depender do
Python do sistema**; usar sempre o Python do uv.

## 5. Estado atual

O andamento detalhado fica em **`PLANO.md`** (checklist por fase). Manter os dois arquivos coerentes.

Já feito:
- Projeto criado com `django-admin startproject config .`; apps `accounts` e `colecoes` registrados.
- `.venv` com uv (Python 3.14), `requirements.txt` gerado com `uv pip freeze`.
- `.gitignore` criado (venv, `.env`, chaves, `db.sqlite3`, `staticfiles/`, `media/`, `.idea/`).
- `SECRET_KEY`, `DEBUG` e `ALLOWED_HOSTS` lidos do `.env` via `python-dotenv` (`DEBUG` é `False` por padrão;
  sem `SECRET_KEY` o Django não sobe). Modelo em `.env.example`.
- `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Maceio"`; `templates/` e `static/` configurados,
  `STATIC_ROOT = staticfiles/`.
- Usuário personalizado `accounts.User` (login por e-mail, `AUTH_USER_MODEL = "accounts.User"`), com testes.
- Modelos `Collection` e `CollectionItem` criados e migrados.

- **Fase 1 (autenticação) concluída:**
  - Templates: `base.html` → `auth_base.html` (login/cadastro, painel decorativo) e `app_base.html`
    (sidebar + botão "Sair" em POST). Parciais em `templates/partials/` (`field.html`, `icon.html` com SVGs,
    `messages.html`, `form_errors.html`, `logo.html`). CSS em `static/css/app.css`; fonte em `static/fonts/`.
  - Rotas: `/entrar/` (`LoginView` + `LoginForm`), `/sair/` (`LogoutView`, só POST), `/cadastro/`
    (`accounts.views.signup`), `/` (`colecoes.views.home`, provisória).
  - django-axes: 5 falhas por IP → bloqueio de 1h (429, template `accounts/bloqueado.html`), sem reset no
    sucesso. Rate limit do cadastro: 10 POST/h por IP (`accounts/ratelimit.py`, cache em arquivo `.cache/`).
  - IP do cliente via `accounts.utils.get_client_ip`: usa `X-Real-IP` só com `BEHIND_PROXY=True`.
  - 16 testes em `accounts/tests.py`.

- **Fase 2 (servidor) quase concluída:** app no ar em https://137.131.137.14 (usuário `coletta`, código em
  `/srv/coletta/app`, banco/cache em `/var/lib/coletta`, Gunicorn via `coletta.socket`/`coletta.service`,
  Nginx com `deploy/nginx/coletta.conf`). Certbot 5.8 (snap), certificado ECDSA de 6 dias com
  `renew_hook = systemctl reload nginx`. PQC confirmado: `Negotiated TLS1.3 group: X25519MLKEM768`.
  Fail2Ban em `mode = aggressive`.

  Validado em 2026-10-25: SSL.org (Trusted: Yes; sha384 / EC 256 · Good signature · Good key; só TLS 1.2 e
  1.3; cadeia completa) e DigiCert PQC checker (Pass: TLS 1.3 + quantum-safe key exchange).

  Fail2Ban testado de outro IP (celular): banido. No modo aggressive uma tentativa de SSH gera ~2 linhas de
  falha, então o ban ocorre por volta da 2ª tentativa (maxretry continua 4) — explicar no README.

- **Fase 3 (CI/CD) concluída:** `.github/workflows/deploy.yml` (checks → deploy → `curl` no site), Actions
  fixadas por SHA. Deploy por SSH como `coletta` com chave restrita no `authorized_keys`
  (`restrict,command="/usr/local/bin/coletta-deploy"`): o workflow envia o SHA, o script só aceita commits
  da `origin/main`. `sudo` do `coletta` limitado a `systemctl restart coletta.service`
  (`/etc/sudoers.d/coletta-deploy`). `/usr/local/bin/coletta-deploy` é cópia de `deploy/coletta-deploy`
  feita à mão: **se o script mudar no repositório, reinstalar no servidor** (`sudo install -o root -g root
  -m 755 ...`).

- **Fases 4 e 5 concluídas:** rotas em `colecoes/urls.py` (`/colecoes/`, `/colecoes/nova/`,
  `/colecoes/<pk>/`, `.../editar/`, `.../excluir/`, `/colecoes/<pk>/itens/novo/`, `/itens/<pk>/editar/`,
  `/itens/<pk>/excluir/`, `/busca/?q=`). Views em funções com `@login_required`; helpers
  `_get_own_collection` / `_get_own_item` fazem o `get_object_or_404` filtrado pelo dono. Exclusão: GET mostra
  a confirmação, só POST exclui. Mudança em item atualiza `collection.updated_at` (`_touch`). Filtro de
  template `ha_quanto_tempo` (`colecoes/templatetags/colecoes_extras.py`). 41 testes (16 de autenticação +
  25 de CRUD, totais, busca e isolamento com 404).

- **Fase 6 (endurecimento):** em `config/settings.py`, com `DEBUG=False`: `SECURE_SSL_REDIRECT`, cookies
  `Secure`, `CSRF_TRUSTED_ORIGINS` derivado do `ALLOWED_HOSTS` e CSP aplicada (`SECURE_CSP`); com
  `DEBUG=True` a CSP é só report-only (as páginas de debug usam estilo inline). HSTS só no Nginx
  (`security.W004` silenciado). Sessão de 8h. `LOGGING` manda `axes`, `django.security` e `django.request`
  para o journal (`journalctl -u coletta.service`). `/admin/` só com `DEBUG=True`. Páginas `404.html`,
  `500.html` e `403_csrf.html` (base `error_base.html`). CI roda os testes com `DEBUG=True` (senão o
  redirect HTTPS quebraria o cliente de testes) e o `check --deploy` com `--fail-level WARNING`.

- **Fase 7:** `README.md` escrito como relatório técnico, com links `arquivo#Lnn` para cada mitigação da
  OWASP. **Se mudar código citado no README, conferir os números de linha.** Evidências em
  `docs/evidencias/` (a usuária salva as capturas).

- **Fase 8 (visual):** totais da Início com detalhe real (`total_categories` sem diferenciar caixa,
  `items_this_month`, `last_collection`), avatar com iniciais (filtro `iniciais`), estrela nos `.eyebrow`,
  busca lavanda, painel do login com selo e cards inclinados. 43 testes.

- **Capas das coleções** (decidido: só coleções, itens sem foto): campo `Collection.cover`; upload passa
  sempre por `colecoes/images.py::process_cover` (só JPEG/PNG/WEBP via `Image.open(formats=...)`, 2 MB,
  25 MP, regravado em WEBP 1600 px sem EXIF, nome `capas/<uuid>.webp`). `MEDIA_ROOT` = `MEDIA_DIR`
  (produção: `/var/lib/coletta/media`), permissões 600/700, **sem MEDIA_URL**: servida só por
  `collection_cover` (dono). Arquivo antigo apagado no `CollectionForm.save` e no `post_delete`. Pillow 13.0
  mesmo sendo recente: a 12.3 tinha CVEs alcançáveis. 54 testes.

- **Fase 9 (aplicação mais completa, a pedido da usuária, inspirada nas telas "Nova Coleção" e "Adicionar
  Item" do Figma):** campos fixos novos (seção 6), campos personalizados por coleção (texto/número, até 10),
  ficha do item (`/itens/<pk>/`), página de campos (`/colecoes/<pk>/campos/`), detalhe da coleção com resumo
  por estado + filtros (`estado`, `edicao`) e ordenação (`ordem`: lista fechada `ITEM_ORDERINGS`),
  formulários em duas colunas com breadcrumb, faixa da coleção e "continuar adicionando". Busca também em
  tags e edição. A prévia ao vivo dos formulários foi descartada. 73 testes.

- **Busca em tempo real** (pedido da usuária): `static/js/busca.js` (carregado com
  `defer` no `app_base.html`) chama `/busca/?q=...&parcial=1`, que devolve `partials/search_live.html`
  (até `LIVE_SEARCH_LIMIT = 5` coleções e 5 itens + total). Melhoria progressiva: sem JS o formulário
  funciona igual. Setas navegam, Esc fecha.
- **Filtros e exclusão em modal** (pedido da usuária): barra de filtros com selects em pílula, chips dos
  filtros ativos (`active_filters`, cada um com link que remove só ele) e aplicação automática
  (`static/js/filtros.js`, carregado pelo `{% block scripts %}`; sem JS aparece o botão Aplicar). Exclusões
  abrem um `<dialog>` único no `app_base.html` (`static/js/confirmar.js`): links com `data-confirm`,
  `data-confirm-text` e `data-confirm-button`; POST com CSRF para a mesma URL. As páginas
  `*_confirm_delete.html` continuam como alternativa sem JS (não é exigência da disciplina ter página
  própria, só a confirmação).
- **Prévia da capa** (pedido da usuária): a área tracejada do formulário de coleção é o `<label>` do campo
  de arquivo (input visualmente oculto, classe `cover-input`); `static/js/capa.js` mostra a prévia via
  `URL.createObjectURL` e avisa formato/tamanho (o servidor valida de novo). Por isso a CSP tem
  `img-src 'self' blob:` (só imagens).
- **Validação antes do envio** (`static/js/validacao.js`, formulários com `data-validate`): impede o envio
  com obrigatório vazio (o navegador não reenvia arquivos, então a capa se perderia); mensagens no mesmo
  visual do Django, ícone vindo de `<template id="icone-alerta">`. Se o servidor recusar com imagem enviada,
  o card avisa para escolher de novo (`form.cover_was_sent`). Categoria da coleção nova começa vazia
  ("Selecione uma categoria"), senão o padrão `outros` passava sem escolha.
- **Seed de demonstração:** `manage.py seed_demo [--reset]` (só com `DEBUG=True`; senhas aleatórias
  mostradas no terminal; contas `@demo.coletta.local`: Ana com 7 coleções/29 itens/capas e Bia com 1
  coleção para o teste de 404). 81 testes.

Próximo passo: publicar (migração 0003 renomeia `category` → `edition` preservando dados); capturas em
`docs/evidencias/`.

### Estrutura esperada
```
coletta/
├── .github/workflows/deploy.yml
├── accounts/            # usuário, cadastro, login, logout
├── colecoes/            # coleções, itens, tela inicial, busca
├── config/              # settings, urls, wsgi
├── templates/           # base.html, parciais, páginas
├── static/              # CSS, fontes e libs baixadas localmente
├── .python-version
├── requirements.txt
├── manage.py
├── README.md
└── .gitignore
```

## 6. Modelo de dados

**User** (`accounts.User`, `AbstractBaseUser` + `PermissionsMixin`): `email` (único, salvo em minúsculas,
`USERNAME_FIELD`), `name`, `is_active`, `is_staff`, `date_joined`. O manager normaliza o e-mail para
minúsculas e `get_by_natural_key` usa `email__iexact`.

**Collection:** `user` (FK → User, CASCADE, `related_name="collections"`), `name` (máx. 100), `category`
(obrigatória, `Collection.Category`: brinquedos, musica, fotografia, livros, jogos, arte, moedas, outros),
`start_year` (opcional, 1900 até o ano atual), `tags` (texto normalizado `rara,anos-2000`; propriedade
`tag_list`), `description` (opcional, máx. 1000), `cover` (opcional), `created_at`, `updated_at`.
Ordenação: `-updated_at`.

**CollectionItem:** `collection` (FK → Collection, CASCADE, `related_name="items"`), `name` (máx. 100),
`edition` (subcategoria/edição, máx. 60; antes se chamava `category`, renomeado na migração 0003 sem perder
dados), `year` (opcional), `condition` (`CollectionItem.Condition`: lacrado, excelente, bom, regular,
danificado), `location` (local de guarda), `description` (rótulo "notas do colecionador"), datas.

**CollectionField** (campo personalizado): `collection` (FK, `related_name="custom_fields"`), `name`
(máx. 40, único por coleção sem diferenciar caixa), `field_type` (texto/número; não muda depois de criado).
Máximo `CollectionField.MAX_PER_COLLECTION = 10`.

**ItemFieldValue:** `item` (FK, `related_name="field_values"`), `field` (FK), `value` (máx. 200; números
guardados no formato brasileiro, ex.: `1500,5`). Único por (item, campo).

Item, campo e valor **não têm `user`**: pertencem ao usuário por meio da coleção.

## 7. Regras de negócio

### Usuários e autenticação
- **RN01** E-mail único, comparação sem diferenciar maiúsculas/minúsculas.
- **RN02** Nome, e-mail e senha obrigatórios; validar formato do e-mail; validadores de senha do Django ativos.
- **RN03** Credenciais inválidas: mensagem genérica, sem dizer se o erro foi no e-mail ou na senha.
- **RN04** Só usuários autenticados acessam a tela inicial e recursos privados.
- **RN05** Logout invalida a sessão e redireciona ao login.
- **RN06** Um usuário nunca consulta, altera ou exclui dados de outro, mesmo adivinhando IDs.
- **RN07** Permissões e dados sempre validados no back-end.

### Coleções
- **RN08/RN10** Nome obrigatório e não vazio após remover espaços; descrição opcional.
- **RN09** A coleção é sempre vinculada ao usuário autenticado (nunca a um `user_id` vindo do formulário).
- **RN11/RN12** Só o dono edita ou exclui.
- **RN13** Excluir coleção exclui os itens (CASCADE); a interface avisa antes.
- **RN14** Contagem de itens sempre real.
- **RN15** Coleção vazia é permitida.
- **RN16** Nomes repetidos são permitidos.

### Itens
- **RN17** Nome obrigatório e não vazio após remover espaços.
- **RN18** Todo item pertence a uma coleção existente.
- **RN19** Permissão herdada: qualquer operação com item exige que a coleção seja do usuário autenticado.
- **RN20** Descrição e categoria opcionais.
- **RN21/RN22** Editar e excluir apenas itens das próprias coleções; totais atualizados.
- **RN23** Não há "mover item" na v1.
- **RN24** Imagens (se implementadas): tipos e tamanhos validados no servidor, sem acesso a arquivos de terceiros.

### Tela inicial e busca
- **RN25–RN27** Totais consideram apenas o usuário atual, sem duplicação.
- **RN28** Recentes ordenadas por `updated_at` decrescente.
- **RN29** Busca só no acervo do usuário; ignora espaços extras; case-insensitive (`icontains`).
- **RN30** Estado vazio com explicação e ação para criar a primeira coleção.

### Integridade e erros
- **RN31** ID inexistente ou de outro usuário → resposta segura (**404**, sem revelar se o registro existe).
- **RN32** Falha na exclusão não pode aparecer como sucesso.
- **RN33** Back-end valida formatos, comprimentos e obrigatórios.
- **RN34** Mensagens de erro sem detalhes técnicos.
- **RN35** Totais e listas atualizados após criar/excluir.

## 8. Regras de implementação (segurança)

### Isolamento de dados (o ponto mais importante)
- Toda view privada usa `@login_required` (ou `LoginRequiredMixin`).
- **Toda** consulta de coleção filtra pelo dono:
  `get_object_or_404(Collection, pk=pk, user=request.user)`.
- **Toda** consulta de item filtra pela coleção do dono:
  `get_object_or_404(CollectionItem, pk=pk, collection__user=request.user)`.
- Ao criar item, a coleção de destino também é buscada com `user=request.user`; nunca confiar em
  `collection_id` vindo do navegador.
- Listagens, totais e busca sempre partem de `request.user.collections` ou filtram por `collection__user`.
- Acesso a recurso de outro usuário retorna **404**, não 403.
- Nunca incluir `user` ou `collection` como campo editável nos `ModelForm`.

### Autenticação
- Usar `django.contrib.auth.login()` (rotaciona a sessão após o login) e `logout()` (limpa a sessão).
- **Logout via POST** com token CSRF (botão dentro de um `<form method="post">`), não por link GET.
- `AuthenticationForm` já usa mensagem genérica (RN03).
- **django-axes** para limitar tentativas de login e registrar falhas.
- Rate limit também no cadastro (o sistema fica num IP público).
- Validadores de senha do Django (`AUTH_PASSWORD_VALIDATORS`) ativos.

### Formulários e entrada
- Sempre usar Forms/ModelForms do Django; nunca SQL cru.
- `CharField` dos forms já remove espaços extras (`strip=True`); validar que o nome não ficou vazio.
- Proteção CSRF ativa em todos os POST.
- Exclusões somente por POST.

### Configuração de produção (`settings.py`, condicionado a `DEBUG = False`)
- `ALLOWED_HOSTS` com o IP público; `CSRF_TRUSTED_ORIGINS = ["https://<IP>"]`.
- `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` (Django atrás do Nginx).
- `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY = True`.
- `SECURE_HSTS_SECONDS`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS = "DENY"`.
- **Content Security Policy** restrita a `'self'` (o Django 6.x tem suporte nativo a CSP; conferir na
  documentação a configuração exata).
- `python manage.py check --deploy` deve passar sem avisos relevantes.

### Front-end
- CSS, JS e fontes servidos localmente pela pasta `static/` (sem CDN), para manter a CSP restrita.
- Nada de JavaScript inline nos templates.
- `base.html` com navbar e área de mensagens (`django.contrib.messages`); componentes repetidos como parciais
  com `{% include %}`.
- Implementar estados: vazio, sem resultados, erros de formulário, confirmação de exclusão.
- Responsivo; não comunicar erros apenas por cor.

### Imagens (somente se sobrar tempo)
- Arquivos fora da pasta pública do Nginx, com nomes aleatórios.
- Validar tipo pelo conteúdo (não só extensão) e tamanho máximo.
- Servir por view do Django que confere o dono.
- Ajustar `client_max_body_size` no Nginx.

## 9. Mapeamento OWASP Top 10:2025 (para o README)

| Categoria | Como o Coletta mitiga |
|---|---|
| **A01 – Broken Access Control** | `@login_required`; toda consulta filtrada pelo dono (`user=request.user` / `collection__user=request.user`); 404 para recursos de terceiros (prevenção de IDOR) |
| **A07 – Authentication Failures** | Hash de senha do Django; validadores de senha; django-axes (limite de tentativas); mensagem genérica; rotação de sessão no login; logout via POST que destrói a sessão; cookies `Secure`/`HttpOnly` |
| **A05 – Injection** | ORM com consultas parametrizadas; validação via Forms; autoescape dos templates |
| **A02 – Security Misconfiguration** (extra) | `DEBUG = False`, segredos no `.env`, HSTS, CSP, cabeçalhos de segurança, `check --deploy` |
| **A03 – Software Supply Chain Failures** (extra) | Dependências fixadas no `requirements.txt`; `pip-audit` no pipeline do GitHub Actions bloqueia o deploy se houver vulnerabilidade conhecida |
| **A09 – Security Logging and Alerting Failures** (extra) | Registro de falhas de login pelo django-axes + logging do Django |

O README deve apontar os arquivos e trechos de código de cada mitigação e incluir a demonstração do teste de
acesso cruzado (usuário B tentando acessar `/colecoes/<id>/` do usuário A e recebendo 404).

## 10. Infraestrutura e deploy

### Servidor
- **Oracle Cloud (OCI), Always Free**: VM `VM.Standard.E2.1.Micro` (x86_64, 1 GB RAM + swap de 2 GB),
  **Ubuntu 26.04 LTS**, **OpenSSL 3.5.5** (suporta `X25519MLKEM768` nativamente).
- IP público: **137.131.137.14** (região São Paulo). Acesso: `ssh -i ~/.ssh/coletta_oci ubuntu@137.131.137.14`.
- Arquivos de configuração do servidor versionados em `deploy/` (copiados manualmente para o servidor).
  Debian foi descartado porque a OCI não tem imagem oficial dele (exigiria importar imagem própria).
- Particularidades da OCI: usuário padrão `ubuntu`; recursos Always Free só na *home region*; as portas
  precisam ser liberadas em **dois lugares**: Security List/NSG da VCN **e** o iptables da própria imagem
  (`/etc/iptables/rules.v4`, que por padrão só libera a 22). Não usar `ufw` junto com essas regras.
- Python 3.14 instalado via **uv** no servidor (mesma versão do desenvolvimento).
- Usuário próprio para a aplicação (não rodar como root).
- Gunicorn via systemd, escutando em socket Unix; Nginx como proxy reverso e servindo `staticfiles/`.
- Nginx deve enviar `proxy_set_header X-Real-IP $remote_addr;` e o `.env` de produção ter
  `BEHIND_PROXY=True`; sem isso o django-axes e o rate limit enxergam o mesmo IP para todos.
- `CACHE_DIR` de produção fora da pasta sobrescrita pelo deploy (ex.: `/var/lib/coletta/cache`).
- `.env` de produção criado manualmente no servidor, com `SECRET_KEY` diferente da de desenvolvimento.
- `db.sqlite3` de produção fora da pasta sobrescrita pelo deploy (ou protegido dela) e incluído em backup.
- Firewall/Security Group: apenas 22, 80 e 443.
- SSH: `PasswordAuthentication no`, `PermitRootLogin no`.
- Fail2Ban no sshd: `maxretry = 4`, `bantime = 24h`.

### HTTPS e PQC
- Certbot 5.4+ emitindo certificado para o IP. Certificados de IP da Let's Encrypt valem só **~6 dias
  (160 horas)** e exigem o perfil ACME **`shortlived`** (conferir na documentação do Certbot a flag exata).
  Fonte: https://letsencrypt.org/2026/01/15/6day-and-ip-general-availability
- A renovação automática é obrigatória na prática: confirmar o timer do Certbot ativo e testar com
  `certbot renew --dry-run`.
- Nginx: redirect 80 → 443, apenas TLS 1.2/1.3, cifras fortes, HSTS.
- PQC: a troca de chaves híbrida (`X25519MLKEM768`) depende de OpenSSL recente no servidor (verificar
  `openssl version`; 3.5+). Configurar `ssl_ecdh_curve` incluindo `X25519MLKEM768` antes das curvas clássicas.
- Validar no SSL.org (certificado confiável, assinatura e chave aceitáveis) e no DigiCert PQC checker.

### GitHub Actions (`.github/workflows/deploy.yml`)
Disparo: push na `main`.
1. **Checks:** checkout, instalar uv e Python 3.14, instalar dependências, `python manage.py check --deploy`
   (com variáveis de teste), `python manage.py test`, `pip-audit` no `requirements.txt`.
2. **Deploy** (só se os checks passarem): conexão SSH com chave em Secret; no servidor: atualizar código,
   instalar dependências, `migrate`, `collectstatic --noinput`, reiniciar o serviço do Gunicorn.

Secrets previstos: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_KNOWN_HOSTS`.
Usar `known_hosts` fixo vindo do Secret (não desabilitar `StrictHostKeyChecking`). O usuário de deploy deve
ter apenas a permissão `sudo` necessária para reiniciar o serviço.

## 11. Testes importantes
- Cadastro válido; recusa de e-mail duplicado (inclusive com maiúsculas diferentes).
- Login correto e incorreto (mensagem genérica).
- Logout e bloqueio das páginas privadas depois dele.
- CRUD de coleção e de item.
- Excluir coleção remove os itens.
- Totais da tela inicial corretos após criar/excluir.
- Busca retorna só dados do usuário atual.
- Usuário B não acessa, edita nem exclui coleção do usuário A (404).
- Usuário B não acessa nem modifica item de coleção do usuário A (404).
- Usuário B não consegue criar item numa coleção do usuário A.
- Validação de campos vazios, só com espaços e longos demais.

## 12. Ordem de trabalho
Seguir as fases do `PLANO.md`. Em resumo:
0. Base: segredos no `.env`, usuário personalizado, modelos, repositório no GitHub.
1. `base.html`, cadastro, login, logout.
2. Servidor: VM, SSH, firewall, Fail2Ban, Nginx, Gunicorn, Certbot, PQC, SSL.org, DigiCert.
3. GitHub Actions (deploy automático).
4. Tela inicial, CRUD de coleções e itens, busca e estados.
5. Testes de isolamento entre usuários.
6. Configurações de produção e `check --deploy`.
7. README (relatório técnico + OWASP + evidências).
8. Ajuste visual conforme o Figma; imagens somente se sobrar tempo.

O servidor e o pipeline vêm cedo de propósito: são o que mais pesa na nota e o que mais pode dar problema.

## 13. Decisões pendentes
Nenhuma no momento.

## 14. Convenções para o Claude Code
- Responder e comentar em **português do Brasil**; nomes de código (modelos, campos, funções) em inglês,
  textos da interface em português.
- **Nunca** colocar segredos no código nem commitar `.env` ou `db.sqlite3`.
- Antes de adicionar uma dependência nova, perguntar e justificar; depois, atualizar o `requirements.txt`
  com `uv pip freeze > requirements.txt`.
- Sempre usar o Python do `.venv` (uv), nunca o do sistema.
- Toda view nova que lide com coleções, itens ou campos deve seguir as regras de isolamento da seção 8
  (helpers `_get_own_collection`, `_get_own_item`, `_get_own_field` em `colecoes/views.py`).
- O README cita código por `arquivo#Lnn`: ao mudar um arquivo citado, recalcular e conferir as linhas.
- Não ampliar o escopo além da v1 sem pedido explícito.
