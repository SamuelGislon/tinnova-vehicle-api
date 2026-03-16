# Tinnova Vehicle API

API REST para gerenciamento de veículos, desenvolvida em **Python + FastAPI**, com **PostgreSQL**, **Redis** e **Alembic**.

## Sobre o projeto

O projeto foi desenvolvido como uma entrega técnica de backend com foco em:

- autenticação com JWT
- controle de acesso por perfil (`USER` e `ADMIN`)
- CRUD de veículos
- filtros, paginação e ordenação
- soft delete
- relatório de veículos ativos por marca
- conversão de preço de **BRL para USD** no momento da escrita
- cache de cotação USD/BRL com Redis e fallback entre provedores externos
- testes automatizados

## Como o projeto foi desenvolvido

A aplicação foi organizada em camadas para separar responsabilidades:

- `app/api`: rotas e dependências
- `app/services`: regras de negócio
- `app/repositories`: acesso a dados
- `app/db/models`: modelos ORM
- `app/schemas`: contratos de entrada e saída
- `app/integrations`: integrações externas e cache
- `app/core`: configuração, segurança, logging e tratamento de erros

## Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- Redis
- JWT
- Pytest
- Docker / Docker Compose

## Requisitos para executar

- Docker
- Docker Compose

## Como executar o projeto

### 1. Copiar o arquivo de ambiente

```bash
cp .env.example .env
```

### 2. Subir os containers

```bash
docker compose up --build -d
```

### 3. Aplicar as migrations

```bash
docker compose exec api alembic upgrade head
```

### 4. Criar os usuários iniciais

```bash
docker compose exec api python -m app.scripts.seed_users
```

### 5. Acessar a documentação

- Swagger UI: `http://localhost:8000/docs`

## Autenticação

### Credenciais iniciais

Essas credenciais vêm do arquivo `.env`.

**Admin**
- username: `admin`
- password: `Admin123!`

**User**
- username: `user`
- password: `User123!`

### Login

```http
POST /api/v1/auth/login
```

Exemplo com `curl`:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"
```

A resposta retorna um `access_token` que deve ser enviado no header:

```http
Authorization: Bearer SEU_TOKEN
```

## Perfis de acesso

- `USER`: pode consultar dados
- `ADMIN`: pode consultar, criar, atualizar e remover logicamente

## Testes

### Rodar todos os testes

```bash
docker compose exec api pytest
```

### Rodar com cobertura

```bash
docker compose exec api pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```