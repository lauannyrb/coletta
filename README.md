# Coletta

Organizador pessoal de coleções: cada usuário cadastra suas coleções (discos, câmeras, bonecas, álbuns...)
e os itens de cada uma, em um acervo privado e isolado dos demais usuários.

Projeto desenvolvido como atividade avaliativa da disciplina **Projeto Aplicado: Práticas de Mercado**
(pós-graduação Lato Sensu em Segurança da Informação e Análise Forense — UNCISAL), seguindo os princípios
de *Secure by Design* e *Secure by Default*.

> **Status:** em desenvolvimento. Este README também é o relatório técnico da entrega e será completado
> ao longo do projeto. O andamento está em [`PLANO.md`](PLANO.md).

## Sumário
1. [Funcionalidades](#1-funcionalidades)
2. [Stack](#2-stack)
3. [Arquitetura](#3-arquitetura)
4. [Como rodar localmente](#4-como-rodar-localmente)
5. [Segurança da aplicação (OWASP Top 10:2025)](#5-segurança-da-aplicação-owasp-top-102025)
6. [Infraestrutura](#6-infraestrutura)
7. [CI/CD](#7-cicd)
8. [Repositório e proteção de segredos](#8-repositório-e-proteção-de-segredos)
9. [Desenvolvimento com IA](#9-desenvolvimento-com-ia)
10. [Evidências](#10-evidências)

## 1. Funcionalidades

- Cadastro, login com e-mail e senha, e logout.
- Tela inicial com resumo do acervo (total de coleções, total de itens, coleções recentes).
- Criar, listar, editar e excluir coleções.
- Criar, listar, editar e excluir itens de uma coleção.
- Busca por nome de coleção ou item.
- Isolamento total: um usuário nunca acessa dados de outro.

## 2. Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.14 (gerenciado com [uv](https://docs.astral.sh/uv/)) |
| Framework | Django 6.1 |
| Front-end | Templates do Django + CSS puro (sem CDN) |
| Banco de dados | SQLite |
| Servidor de aplicação | Gunicorn (systemd) |
| Web server | Nginx (proxy reverso + HTTPS) |
| CI/CD | GitHub Actions |

## 3. Arquitetura

```
Navegador ──HTTPS──▶ Nginx ──socket Unix──▶ Gunicorn ──▶ Django ──▶ SQLite
                      │
                      └── arquivos estáticos (staticfiles/)
```

Estrutura do código:

```
coletta/
├── accounts/    # usuário personalizado (login por e-mail), cadastro, login, logout
├── colecoes/    # coleções, itens, tela inicial, busca
├── config/      # settings, urls, wsgi
├── templates/   # templates HTML
└── static/      # CSS e fontes servidos localmente
```

## 4. Como rodar localmente

Pré-requisito: [uv](https://docs.astral.sh/uv/) instalado.

```bash
git clone git@github.com:lauannyrb/coletta.git
cd coletta

uv venv                                  # cria o .venv com Python 3.14 (.python-version)
uv pip install -r requirements.txt

cp .env.example .env                     # depois edite o .env (veja abaixo)
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver
```

No `.env`, gere uma `SECRET_KEY` própria e, para desenvolvimento, use `DEBUG=True`:

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key as g; print(g())"
```

Testes:

```bash
.venv/bin/python manage.py test
```

## 5. Segurança da aplicação (OWASP Top 10:2025)

Categorias mitigadas. Os trechos de código de cada uma serão referenciados aqui conforme forem implementados.

| Categoria | Mitigação |
|---|---|
| **A01 – Broken Access Control** | Páginas privadas exigem login; toda consulta é filtrada pelo dono do dado; recurso de outro usuário retorna 404 (prevenção de IDOR) |
| **A07 – Authentication Failures** | Hash de senha do Django; validadores de senha; limite de tentativas de login (django-axes); mensagem de erro genérica; rotação de sessão no login; logout via POST |
| **A05 – Injection** | ORM com consultas parametrizadas; validação por Forms; escape automático nos templates |
| **A02 – Security Misconfiguration** | `DEBUG` desligado por padrão; segredos no `.env`; HSTS, CSP e cabeçalhos de segurança; `check --deploy` |
| **A03 – Software Supply Chain Failures** | Dependências fixadas em `requirements.txt`; `pip-audit` no pipeline |
| **A09 – Security Logging and Alerting Failures** | Registro de falhas de login (django-axes) e logging do Django |

_TODO: apontar arquivos e linhas de cada mitigação e incluir o teste de acesso cruzado entre usuários._

## 6. Infraestrutura

_TODO: provedor de nuvem, VM e sistema operacional._

Requisitos que serão atendidos:
- Ubuntu Server ou Debian (versão estável mais recente), no free tier.
- Acesso SSH somente por chave; senha e login de root desabilitados.
- Firewall liberando apenas as portas 22, 80 e 443.
- Fail2Ban na porta 22 (`maxretry = 4`, `bantime = 24h`).
- Nginx como proxy reverso, com redirecionamento automático de HTTP para HTTPS.
- Certificado Let's Encrypt emitido para o IP público via Certbot 5.4+, com renovação automática.
- TLS 1.2/1.3 e troca de chaves pós-quântica (PQC, `X25519MLKEM768`).

## 7. CI/CD

_TODO: descrever o workflow `.github/workflows/deploy.yml`._

A cada `git push origin main`, o GitHub Actions:
1. Roda as verificações: `manage.py check --deploy`, testes automatizados e `pip-audit`.
2. Se tudo passar, faz o deploy no servidor por SSH: atualiza o código, instala dependências, aplica
   migrações, coleta os estáticos e reinicia o Gunicorn.

As credenciais de acesso ao servidor ficam somente em **GitHub Secrets**.

## 8. Repositório e proteção de segredos

- Repositório público, com acesso via chave SSH e 2FA na conta do GitHub.
- `.gitignore` bloqueia `.env`, chaves, banco de dados local, ambiente virtual e arquivos de IDE.
- Configurações sensíveis (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`) lidas do `.env`; o repositório
  contém apenas o modelo [`.env.example`](.env.example), sem valores reais.

## 9. Desenvolvimento com IA

O projeto foi desenvolvido com auxílio do **Claude Code**. As regras de projeto e de segurança passadas à IA
estão em [`CLAUDE.md`](CLAUDE.md) (requisitos, regras de negócio e regras de isolamento de dados).

_TODO: exemplos de uso da IA para gerar, revisar e corrigir código._

## 10. Evidências

_TODO: capturas de tela do SSL.org, DigiCert PQC checker, Fail2Ban, pipeline do GitHub Actions e teste
de acesso cruzado (404)._
