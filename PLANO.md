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
- [ ] Criar repositório público no GitHub (SSH/PAT, 2FA) e fazer o primeiro commit
- [ ] Conferir com `git status` que `.env`, `db.sqlite3` e `.venv/` não aparecem

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
- [ ] Guardar prints das evidências para o README

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
- [ ] Reinstalar `/usr/local/bin/coletta-deploy` no servidor e conferir os cabeçalhos em produção

## Fase 7 — README (relatório técnico)
- [x] Visão geral, stack e arquitetura
- [x] Passo a passo da infraestrutura (VM, SSH, firewall, Fail2Ban, Nginx, Certbot, PQC)
- [x] OWASP Top 10:2025: categorias mitigadas, com arquivo e linha de cada uma
- [x] Demonstração do teste de acesso cruzado (404)
- [x] Como rodar localmente
- [ ] Salvar as capturas em `docs/evidencias/` (ssl-org.png, ssl-org-cadeia.png, digicert-pqc.png,
      fail2ban-ban.png, pipeline.png, tela-login.png, tela-inicio.png)
- [ ] Confirmar 2FA ativo na conta do GitHub (o README afirma)

## Fase 8 — Visual e extras
- [x] Ajuste visual fiel ao protótipo do Figma (totais com detalhes reais, avatar, busca lavanda, painel do login)
- [ ] Imagens (capa e foto de item), somente se sobrar tempo
