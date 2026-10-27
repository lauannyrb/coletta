# Plano de execução — Coletta

Checklist de execução da v1. Regras, requisitos e decisões estão no `CLAUDE.md`; este arquivo só diz
**o que fazer e em que ordem**. Marcar `[x]` conforme for concluindo.

Estratégia: a nota depende principalmente de infraestrutura, CI/CD e segurança. Por isso o servidor e o
pipeline sobem **cedo** (logo depois do login funcionar), e as funcionalidades seguintes já são entregues
pelo deploy automático. Assim, problemas de infraestrutura aparecem com tempo para resolver.

## Fase 0 — Base do projeto
- [x] `.gitignore`
- [x] Criar `.env` local e `.env.example` (sem valores reais); mover `SECRET_KEY`, `DEBUG` e
      `ALLOWED_HOSTS` do `settings.py` para o `.env` com `python-dotenv` (`DEBUG=False` por padrão)
- [x] Gerar uma `SECRET_KEY` nova (a atual já esteve em texto puro no `settings.py`)
- [x] `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Maceio"`
- [x] Registrar apps `accounts` e `colecoes`; `TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`;
      `STATICFILES_DIRS`, `STATIC_ROOT = BASE_DIR / "staticfiles"`
- [x] Modelo `accounts.User` (login por e-mail) + `AUTH_USER_MODEL` — **antes da primeira migração**
- [x] Modelos `Collection` e `CollectionItem`; `makemigrations` e `migrate`
- [x] Criar repositório público no GitHub (SSH/PAT) e fazer o primeiro commit (2FA: ver Fase 10)
- [x] Conferir com `git status` que `.env`, `db.sqlite3` e `.venv/` não aparecem

## Fase 1 — Autenticação
- [x] `base.html` com navbar, área de mensagens e parciais
- [x] Cadastro (nome, e-mail, senha, confirmação), com e-mail único case-insensitive
- [x] Login por e-mail com mensagem genérica de erro
- [x] Logout via POST + CSRF
- [x] Página inicial protegida por `@login_required` (provisória)
- [x] django-axes (limite de tentativas no login) e rate limit no cadastro
- [x] Testes: cadastro, e-mail duplicado, login certo/errado, logout bloqueia páginas privadas

## Fase 2 — Servidor (cedo, para dar tempo de errar)
- [x] Escolher provedor e distro: Oracle Cloud (Always Free) + Ubuntu Server LTS
- [x] Criar VM free tier
- [x] Usuário próprio para a aplicação (não root)
- [x] SSH só com chave: `PasswordAuthentication no`, `PermitRootLogin no`
- [x] Firewall / Security Group: somente 22, 80, 443 (Security List da OCI + `/etc/iptables/rules.v4`)
- [x] Fail2Ban no sshd: `maxretry = 4`, `bantime = 24h`
- [x] Filtro do Fail2Ban em `mode = aggressive` (o `normal` não contava as tentativas dos robôs)
- [x] Teste 2 do Fail2Ban (2026-10-25): celular em dados móveis banido (`177.58.26.39`); no modo
      aggressive uma tentativa gera ~2 falhas no log, então o ban vem por volta da 2ª tentativa
- [x] uv + Python 3.14; clonar o projeto; `.env` de produção com `SECRET_KEY` própria
- [x] `db.sqlite3` de produção fora da pasta sobrescrita pelo deploy
- [x] Gunicorn como serviço systemd (socket Unix)
- [x] Nginx: proxy reverso + `staticfiles/`; `proxy_set_header X-Real-IP $remote_addr` e
      `BEHIND_PROXY=True` no `.env` (IP real para o django-axes e o rate limit)
- [x] Certbot 5.4+ com certificado para o IP (perfil `shortlived`, ~6 dias); timer de renovação ativo;
      `certbot renew --dry-run`
- [x] Redirect 80 → 443; TLS 1.2/1.3; HSTS
- [x] PQC: `openssl version` ≥ 3.5; `ssl_ecdh_curve` com `X25519MLKEM768` primeiro
- [x] Validar: SSL.org (Trusted: Yes; Good signature · Good key; TLS 1.2/1.3) e DigiCert PQC checker (Pass)
- [x] Guardar prints das evidências para o README (salvar os arquivos: ver Fase 10)

## Fase 3 — CI/CD
- [x] Usuário de deploy com `sudo` restrito a reiniciar o serviço do Gunicorn
- [x] Secrets no GitHub: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_KNOWN_HOSTS`
- [x] `.github/workflows/deploy.yml`, job de checks: uv + Python 3.14, dependências, `check --deploy`,
      `manage.py test`, `pip-audit`
- [x] Job de deploy (só se os checks passarem): atualizar código, dependências, `migrate`,
      `collectstatic --noinput`, reiniciar o Gunicorn
- [x] Testar com `git push origin main` e conferir a mudança no IP público (pipeline verde em 2026-10-25)

## Fase 4 — Funcionalidades (já entregues pelo pipeline)
- [x] Tela inicial: boas-vindas, totais reais, coleções recentes, "nova coleção"
- [x] CRUD de coleções (cards, formulário, confirmação de exclusão avisando sobre os itens)
- [x] Detalhe da coleção + CRUD de itens
- [x] Busca (coleções e itens do usuário, `icontains`, estado "nenhum resultado")
- [x] Busca em tempo real (sugestões enquanto digita, `static/js/busca.js` + `?parcial=1`)
- [x] Filtros com aplicação automática e chips removíveis; exclusão em modal (`<dialog>` + POST com CSRF)
- [x] Prévia da capa ao escolher a imagem (`static/js/capa.js`, CSP `img-src blob:`)
- [x] Validação antes do envio (mantém a capa escolhida), categoria obrigatória de fato
- [x] Seed de demonstração (`manage.py seed_demo`, só em desenvolvimento)
- [x] Saudação com os dois primeiros nomes; "Voltar ao item" e rascunho do formulário de item ao gerenciar campos
- [x] Estados vazios e erros de formulário
- [x] Todas as consultas filtradas pelo dono (regras da seção 8 do `CLAUDE.md`)

## Fase 5 — Testes de isolamento (feitos junto com a Fase 4, em `colecoes/tests.py`)
- [x] Usuário B não vê, edita nem exclui coleção de A (404)
- [x] Usuário B não vê nem modifica item de A (404)
- [x] Usuário B não cria item em coleção de A
- [x] Totais e busca consideram só o usuário atual
- [x] Validação de campos vazios, só com espaços e longos demais

## Fase 6 — Endurecimento de produção
- [x] Cookies `Secure`/`HttpOnly`, sessão de 8h, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`
- [x] `SECURE_SSL_REDIRECT`, `nosniff`, `X_FRAME_OPTIONS = "DENY"`, CSP nativa do Django restrita a `'self'`
      (HSTS fica no Nginx; `security.W004` silenciado com justificativa)
- [x] Logging de falhas de login (django-axes, IP visível e e-mail mascarado) e de `django.security`
- [x] Páginas 404, 500 e 403 (CSRF) próprias, sem detalhes técnicos
- [x] `/admin/` só existe com `DEBUG=True`
- [x] `check --deploy` sem avisos; `--fail-level WARNING` no workflow e no `deploy/coletta-deploy`
- [x] Conferir os cabeçalhos em produção (2026-10-26: CSP, HSTS, X-Frame-Options, nosniff, cookies `Secure`)
- [x] `/usr/local/bin/coletta-deploy` igual ao do repositório (conferido com `diff` em 2026-10-26)

## Fase 7 — README (relatório técnico)
- [x] Visão geral, stack e arquitetura
- [x] Passo a passo da infraestrutura (VM, SSH, firewall, Fail2Ban, Nginx, Certbot, PQC)
- [x] OWASP Top 10:2025: categorias mitigadas, com arquivo e linha de cada uma
- [x] Demonstração do teste de acesso cruzado (404)
- [x] Como rodar localmente
- [x] Capturas em `docs/evidencias/` (2FA do GitHub: ver Fase 10)

## Fase 8 — Visual e extras
- [x] Ajuste visual fiel ao protótipo do Figma (totais com detalhes reais, avatar, busca lavanda, painel do login)
- [x] Capa das coleções (só a coleção; itens sem foto): Pillow 13, validação pelo conteúdo, regravação em
      WEBP, nome aleatório, fora da pasta pública, servida só ao dono
- [x] Servidor: criar `/var/lib/coletta/media`, `MEDIA_DIR` no `.env`, Nginx com `client_max_body_size 3m`

## Fase 9 — Aplicação mais completa (inspirada nas telas novas do Figma)
- [x] Coleção: categoria principal, ano de início, tags
- [x] Item: subcategoria/edição, ano, estado de conservação, local de guarda, notas
- [x] Campos personalizados por coleção (texto e número, até 10), com isolamento e testes de acesso cruzado
- [x] Ficha do item; detalhe da coleção com resumo por estado, filtros e ordenação
- [x] Formulários em duas colunas, breadcrumb, faixa da coleção, "continuar adicionando"
- [x] README: funcionalidades, modelo de dados (Mermaid) e segurança atualizados
- [x] Publicar e conferir em produção (capas em `/var/lib/coletta/media` com 600/700, Nginx com `client_max_body_size 3m`)

## Fase 10 — Checagem final antes da entrega (2026-10-26)

Varredura comparando o projeto com o escopo oficial da disciplina (checklist de 9 itens).

**Conferido e OK:**
- [x] Aplicação no ar por IP; HTTP → HTTPS (301); certificado Let's Encrypt para o IP (válido até 01/11, renovação automática)
- [x] TLS só 1.2/1.3 (SSL.org); PQC `X25519MLKEM768` (DigiCert); portas abertas: só 22, 80 e 443
- [x] Cabeçalhos em produção: CSP restrita, HSTS, X-Frame-Options DENY, nosniff, cookies `Secure`
- [x] Página interna exige login (302 → /entrar/); `/admin/`, `/media/`, `.env` e `.git` dão 404
- [x] Repositório público; nenhum arquivo sensível ou segredo real em todo o histórico do Git; `.gitignore` completo
- [x] Workflow usa só GitHub Secrets e `StrictHostKeyChecking=yes`; últimos 3 deploys verdes
- [x] Todas as views com `@login_required` e consultas pelo dono; sem SQL cru; `pip-audit` sem vulnerabilidades
- [x] README: 6 categorias da OWASP com arquivo e linha; auditoria com IA registrada (seção 9)

**Falta (tarefas da usuária):**
- [x] Salvar as 7 capturas em `docs/evidencias/` com os nomes que o README usa (hoje as imagens aparecem
      quebradas no GitHub): `ssl-org.jpg` ✔, `ssl-org-cadeia.jpg` ✔, `digicert-pqc.png` ✔, `fail2ban-ban.png` ✔,
      `pipeline.png` ✔, `tela-login.png` ✔, `tela-inicio.png` ✔ (extras ✔: `tela-colecoes.png`, ✔: `ssh-somente-chave.png`, `pipeline-run.png`, `pipeline-deploy.png`)
- [x] Opcional, mas reforça A01 e a renovação: `isolamento-404.png` (conta B abrindo coleção da conta A) e
      `certbot-renovacao.png` (`sudo certbot renew --dry-run` + `systemctl list-timers | grep certbot`)
- [x] 2FA ativo na conta do GitHub (app autenticador + códigos de recuperação; `github-2fa.png`)
- [x] Servidor: `diff` do `coletta-deploy` sem diferenças
- [x] Renovação testada: `certbot renew --dry-run` OK e `snap.certbot.renew.timer` ativo (`certbot-renovacao.png`)
- [ ] Antes de entregar: se a data passar de 01/11, abrir o site e conferir o cadeado
- [x] Commit final com as evidências e `git push` (`f36d3eb`: pipeline verde, imagens publicadas no GitHub)

