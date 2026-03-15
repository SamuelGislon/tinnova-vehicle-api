# Tinnova Vehicle API

API REST para gerenciamento de veículos, desenvolvida em Python com FastAPI, SQLAlchemy, PostgreSQL, Redis e Alembic.

O projeto foi estruturado como uma entrega técnica de backend com foco em:

- organização e clareza arquitetural
- autenticação e autorização com JWT
- qualidade de código e testes automatizados
- tratamento padronizado de erros
- integração resiliente com cotação USD/BRL usando cache e fallback

## Visão geral do projeto

A API permite:

- CRUD completo de veículos
- autenticação com JWT
- controle de acesso por perfis `USER` e `ADMIN`
- filtros por marca, ano, cor, placa e faixa de preço
- paginação e ordenação
- soft delete
- relatório por marca
- integração com cotação USD/BRL
- cache da cotação em Redis
- fallback entre provedores externos
- payload padronizado de erro
- suíte de testes organizada em unit, integration e e2e

## Stack utilizada

- Python
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Redis
- httpx
- Pydantic
- JWT
- Pytest
- Docker / Docker Compose
- Ruff
- Black
- isort
- mypy

## Arquitetura da solução

A aplicação foi organizada em camadas, em um estilo de modular monolith:

- `app/api`  
  rotas, dependências e contratos HTTP

- `app/services`  
  regras de negócio e orquestração

- `app/repositories`  
  persistência e queries

- `app/db/models`  
  models ORM

- `app/schemas`  
  contratos Pydantic de entrada e saída

- `app/integrations`  
  clientes externos e cache

- `app/core`  
  config, segurança, exceptions, handlers e logging

- `app/utils`  
  utilitários puros

Essa organização foi escolhida para manter:

- boa separação de responsabilidades
- alta testabilidade
- facilidade de manutenção

## Decisões técnicas principais

### 1. RBAC com JWT

A API exige autenticação em todos os endpoints.

Perfis:

- `USER`: somente leitura
- `ADMIN`: acesso total

### 2. Preço de entrada em BRL e persistência em USD

Os endpoints de escrita recebem:

- `price_brl`

O valor persistido e retornado pela API é:

- `price_usd`

Isso foi feito para atender ao requisito de armazenamento em dólar, mantendo o input natural no contexto brasileiro.

### 3. Cotação com cache e fallback

A cotação USD/BRL segue esta ordem:

1. Redis
2. AwesomeAPI
3. Frankfurter

Se a API principal falhar por timeout, HTTP error ou payload inválido, o fallback é acionado.

### 4. Soft delete

O delete não remove o registro fisicamente.

A remoção lógica faz:

- `is_active = false`
- `deleted_at = timestamp UTC`

Registros inativos:

- não aparecem na listagem
- não aparecem no relatório
- retornam `404` no detalhe

### 5. Tratamento padronizado de erros

A API responde com um payload de erro estável, com:

- código interno
- mensagem
- detalhes
- path
- method
- timestamp
- request_id

## Why this solution

Esta solução foi desenhada para equilibrar:

- clareza arquitetural
- testabilidade
- pragmatismo

Não há overengineering. O projeto evita padrões excessivos e prioriza o que realmente agrega valor em um teste técnico:

- boa separação de camadas
- contratos bem definidos
- segurança
- resiliência
- cobertura de testes
- documentação reproduzível

## Trade-offs

Algumas decisões foram mantidas simples de propósito:

- SQLite em memória nos testes de integração, em vez de PostgreSQL real para toda a suíte
- modular monolith, em vez de arquitetura distribuída ou excessivamente abstrata
- logging objetivo, sem stack de observabilidade extra
- tipagem forte no que agrega valor real, sem transformar o projeto em algo pesado demais

Esses trade-offs foram escolhidos para maximizar qualidade e clareza sem comprometer a produtividade nem a legibilidade.

## Como executar

### Pré-requisitos

- Docker
- Docker Compose

### Passo 1: copiar o arquivo de ambiente

```bash
cp .env.example .env
```

### Passo 2: subir a aplicação

```bash
docker compose up --build -d
```

### Passo 3: aplicar migrations

```bash
docker compose exec api alembic upgrade head
```

### Passo 4: criar usuários seed

```bash
docker compose exec api python -m app.scripts.seed_users
```

### Passo 5: abrir a documentação

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Docker

### Ver logs

```bash
docker compose logs -f api
```

### Derrubar os serviços

```bash
docker compose down
```

## Migrations

### Ver estado atual

```bash
docker compose exec api alembic current
```

### Criar nova migration

```bash
docker compose exec api alembic revision --autogenerate -m "descrever alteracao"
```

### Credenciais de exemplo

Admin:

- username: `admin`
- password: `Admin123!`

User:

- username: `user`
- password: `User123!`

Essas credenciais vêm do `.env` e podem ser alteradas.

## Como autenticar

### Endpoint de login

```http
POST /api/v1/auth/login
```

### Exemplo com curl

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"
```

### Resposta esperada

```json
{
  "access_token": "TOKEN",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Endpoint para identificar o usuário autenticado

```http
GET /api/v1/auth/me
```

```bash
curl "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer TOKEN"
```

## Perfis de acesso

### USER

Pode acessar apenas endpoints de leitura:

- `GET /api/v1/veiculos`
- `GET /api/v1/veiculos/{id}`
- `GET /api/v1/veiculos/relatorios/por-marca`
- endpoints de auth e health compatíveis

### ADMIN

Pode acessar tudo:

- leitura
- criação
- atualização completa
- atualização parcial
- delete lógico

## Endpoints principais

### Health

- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

### Auth

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Vehicles

- `GET /api/v1/veiculos`
- `GET /api/v1/veiculos/{id}`
- `POST /api/v1/veiculos`
- `PUT /api/v1/veiculos/{id}`
- `PATCH /api/v1/veiculos/{id}`
- `DELETE /api/v1/veiculos/{id}`

### Reports

- `GET /api/v1/veiculos/relatorios/por-marca`

## Regra de preço: `price_brl` -> persistência em `price_usd`

### Escrita

Nos endpoints de criação e atualização, o cliente envia:

- `price_brl`

Exemplo:

```json
{
  "brand": "Toyota",
  "model": "Corolla",
  "year": 2022,
  "color": "Prata",
  "plate": "ABC-1D23",
  "price_brl": "125000.00"
}
```

### Persistência

Internamente, a API:

1. obtém a cotação USD/BRL
2. converte BRL para USD
3. persiste apenas `price_usd`

### Leitura

A resposta da API expõe:

- `price_usd`

Exemplo:

```json
{
  "id": 1,
  "brand": "Toyota",
  "model": "Corolla",
  "year": 2022,
  "color": "Prata",
  "plate": "ABC1D23",
  "price_usd": "25000.00",
  "is_active": true,
  "created_at": "2026-03-15T03:00:00+00:00",
  "updated_at": "2026-03-15T03:00:00+00:00"
}
```

### Filtros de preço

Os filtros:

- `minPreco`
- `maxPreco`

são aplicados sobre o valor persistido em **USD**.

## Cotação USD/BRL com cache Redis e fallback

### Ordem de busca

1. Redis
2. AwesomeAPI
3. Frankfurter

### Comportamento

- se houver cache válido, a taxa é reutilizada
- se não houver cache, a API principal é consultada
- se a principal falhar, o fallback é acionado
- a taxa válida é salva no Redis com TTL

### TTL

- `REDIS_TTL_USD_BRL=300`
- 5 minutos

### Vantagens

- reduz chamadas externas
- melhora desempenho
- adiciona resiliência
- mantém o domínio desacoplado de HTTP/Redis

## Soft delete

O delete é lógico.

### O que acontece no `DELETE`

- `is_active = false`
- `deleted_at` recebe timestamp UTC

### Consequências

- o veículo deixa de aparecer na listagem
- o veículo não entra no relatório
- `GET /veiculos/{id}` retorna `404`
- updates posteriores retornam `404`

## Relatório por marca

### Endpoint

```http
GET /api/v1/veiculos/relatorios/por-marca
```

### Regra

O relatório considera somente veículos ativos.

### Resposta

```json
{
  "items": [
    {
      "brand": "Toyota",
      "total_active_vehicles": 2
    },
    {
      "brand": "Honda",
      "total_active_vehicles": 1
    }
  ],
  "total_brands": 2,
  "total_active_vehicles": 3,
  "generated_at": "2026-03-15T03:20:00+00:00"
}
```

### Ordenação

- `total_active_vehicles DESC`
- `brand ASC`

## Exemplos de uso

### Criar veículo como ADMIN

```bash
curl -X POST "http://localhost:8000/api/v1/veiculos" \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{
    "brand": "Chevrolet",
    "model": "Prisma",
    "year": 2016,
    "color": "Branco",
    "plate": "ABC-1D23",
    "price_brl": "56900.00"
  }'
```

### Listar veículos com filtros, paginação e ordenação

```bash
curl "http://localhost:8000/api/v1/veiculos?brand=Chevrolet&page=1&page_size=10&sort_by=price_usd&sort_order=asc" \
  -H "Authorization: Bearer TOKEN_USER"
```

### Detalhar veículo

```bash
curl "http://localhost:8000/api/v1/veiculos/1" \
  -H "Authorization: Bearer TOKEN_USER"
```

### Atualizar parcialmente

```bash
curl -X PATCH "http://localhost:8000/api/v1/veiculos/1" \
  -H "Authorization: Bearer TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{
    "color": "Preto",
    "price_brl": "60000.00"
  }'
```

### Delete lógico

```bash
curl -X DELETE "http://localhost:8000/api/v1/veiculos/1" \
  -H "Authorization: Bearer TOKEN_ADMIN"
```

### Gerar relatório por marca

```bash
curl "http://localhost:8000/api/v1/veiculos/relatorios/por-marca" \
  -H "Authorization: Bearer TOKEN_USER"
```

## Tratamento de erros

A API utiliza um payload padrão para todos os erros relevantes.

### Exemplo real

```json
{
  "error": {
    "code": "VEHICLE_ALREADY_EXISTS",
    "message": "Já existe um veículo cadastrado com esta placa.",
    "details": null,
    "path": "/api/v1/veiculos",
    "method": "POST",
    "timestamp": "2026-03-15T04:10:00+00:00",
    "request_id": "8d5f4cb6-df9f-4a84-a4ad-9b4a78e6f52f"
  }
}
```

### Códigos principais

- `UNAUTHORIZED`
- `FORBIDDEN`
- `VEHICLE_NOT_FOUND`
- `VEHICLE_ALREADY_EXISTS`
- `VALIDATION_ERROR`
- `EXCHANGE_RATE_UNAVAILABLE`
- `INTERNAL_SERVER_ERROR`

## Testes

A suíte está organizada em:

- `unit`
- `integration`
- `e2e`

### Rodar todos os testes

```bash
docker compose exec api pytest
```

### Rodar com cobertura

```bash
docker compose exec api pytest --cov=app --cov-report=term-missing --cov-fail-under=80
```

### Rodar testes específicos

Somente unit:

```bash
docker compose exec api pytest -m unit
```

Somente integration:

```bash
docker compose exec api pytest -m integration
```

Somente e2e:

```bash
docker compose exec api pytest -m e2e
```

## Qualidade de código

### Formatação

```bash
docker compose exec api black .
```

### Lint

```bash
docker compose exec api ruff check .
```

### Ordenar imports

```bash
docker compose exec api isort app tests alembic
```

### Validar imports

```bash
docker compose exec api isort --check-only app tests alembic
```

### Tipagem

```bash
docker compose exec api mypy app
```

## Arquitetura e decisões técnicas

### Por que arquitetura em camadas

Porque entrega:

- clareza
- testabilidade
- separação de responsabilidades
- manutenção mais simples

### Por que Redis apenas como cache

Para manter:

- baixo acoplamento
- falha de cache não bloqueando a operação
- comportamento resiliente

### Por que `VehicleService` não conhece HTTP nem Redis

Porque o domínio de veículos deve depender apenas do contrato de cotação, não de detalhes de infraestrutura.

### Por que `PUT` e `PATCH` são diferentes

- `PUT`: atualização completa
- `PATCH`: atualização parcial

Isso evita semântica ambígua e atende ao que normalmente é esperado de uma API.

## Observações finais

Esta API foi construída para ser:

- fácil de executar
- fácil de testar
- forte em arquitetura, segurança e qualidade

O foco foi entregar uma solução de backend profissional sem excesso de abstração, mantendo o projeto robusto e legível.
