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
- [ ] `base.html` com navbar, área de mensagens e parciais
- [ ] Cadastro (nome, e-mail, senha, confirmação), com e-mail único case-insensitive
- [ ] Login por e-mail com mensagem genérica de erro
- [ ] Logout via POST + CSRF
- [ ] Página inicial protegida por `@login_required` (provisória)
- [ ] django-axes (limite de tentativas no login) e rate limit no cadastro
- [ ] Testes: cadastro, e-mail duplicado, login certo/errado, logout bloqueia páginas privadas

## Fase 2 — Servidor (cedo, para dar tempo de errar)
- [ ] Escolher provedor e distro (Ubuntu ou Debian, versão estável mais recente)
- [ ] Criar VM free tier; usuário próprio para a aplicação (não root)
- [ ] SSH só com chave: `PasswordAuthentication no`, `PermitRootLogin no`
- [ ] Firewall / Security Group: somente 22, 80, 443
- [ ] Fail2Ban no sshd: `maxretry = 4`, `bantime = 24h`
- [ ] uv + Python 3.14; clonar o projeto; `.env` de produção com `SECRET_KEY` própria
- [ ] `db.sqlite3` de produção fora da pasta sobrescrita pelo deploy
- [ ] Gunicorn como serviço systemd (socket Unix)
- [ ] Nginx: proxy reverso + `staticfiles/`
- [ ] Certbot 5.4+ com certificado para o IP (perfil `shortlived`, ~6 dias); timer de renovação ativo;
      `certbot renew --dry-run`
- [ ] Redirect 80 → 443; TLS 1.2/1.3; HSTS
- [ ] PQC: `openssl version` ≥ 3.5; `ssl_ecdh_curve` com `X25519MLKEM768` primeiro
- [ ] Validar: SSL.org (certificado confiável, assinatura e chave aceitáveis) e DigiCert PQC checker
- [ ] Guardar prints das evidências para o README

## Fase 3 — CI/CD
- [ ] Usuário de deploy com `sudo` restrito a reiniciar o serviço do Gunicorn
- [ ] Secrets no GitHub: `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`, `SSH_KNOWN_HOSTS`
- [ ] `.github/workflows/deploy.yml`, job de checks: uv + Python 3.14, dependências, `check --deploy`,
      `manage.py test`, `pip-audit`
- [ ] Job de deploy (só se os checks passarem): atualizar código, dependências, `migrate`,
      `collectstatic --noinput`, reiniciar o Gunicorn
- [ ] Testar com `git push origin main` e conferir a mudança no IP público

## Fase 4 — Funcionalidades (já entregues pelo pipeline)
- [ ] Tela inicial: boas-vindas, totais reais, coleções recentes, "nova coleção"
- [ ] CRUD de coleções (cards, formulário, confirmação de exclusão avisando sobre os itens)
- [ ] Detalhe da coleção + CRUD de itens
- [ ] Busca (coleções e itens do usuário, `icontains`, estado "nenhum resultado")
- [ ] Estados vazios e erros de formulário
- [ ] Todas as consultas filtradas pelo dono (regras da seção 8 do `CLAUDE.md`)

## Fase 5 — Testes de isolamento
- [ ] Usuário B não vê, edita nem exclui coleção de A (404)
- [ ] Usuário B não vê nem modifica item de A (404)
- [ ] Usuário B não cria item em coleção de A
- [ ] Totais e busca consideram só o usuário atual
- [ ] Validação de campos vazios, só com espaços e longos demais

## Fase 6 — Endurecimento de produção
- [ ] Cookies `Secure`/`HttpOnly`, `SECURE_PROXY_SSL_HEADER`, `CSRF_TRUSTED_ORIGINS`
- [ ] HSTS, `nosniff`, `X_FRAME_OPTIONS = "DENY"`, CSP restrita a `'self'`
- [ ] Logging de falhas de login (django-axes + logging do Django)
- [ ] `check --deploy` sem avisos relevantes

## Fase 7 — README (relatório técnico)
- [ ] Visão geral, stack e arquitetura
- [ ] Passo a passo da infraestrutura (VM, SSH, firewall, Fail2Ban, Nginx, Certbot, PQC)
- [ ] Evidências: SSL.org, DigiCert, Fail2Ban, pipeline verde
- [ ] OWASP Top 10:2025: categorias mitigadas, com arquivo e trecho de código de cada uma
- [ ] Demonstração do teste de acesso cruzado (404)
- [ ] Como rodar localmente

## Fase 8 — Visual e extras
- [ ] Ajuste visual fiel ao protótipo do Figma
- [ ] Imagens (capa e foto de item), somente se sobrar tempo
