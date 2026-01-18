## RESTful API (Organizations/Buildings/Activities)

API для справочника организаций, зданий и видов деятельности. Реализовано на FastAPI
с асинхронным SQLAlchemy и миграциями Alembic.

## Стек

- FastAPI
- Pydantic v2
- SQLAlchemy (async) + asyncpg
- Alembic
- PostgreSQL
- Docker / Docker Compose

## Быстрый старт (Docker)

```bash
docker compose up --build
```

Применить миграции:

```bash
docker compose exec api alembic upgrade head
```

Заполнить тестовыми данными:

```bash
docker compose exec -T db psql -U app -d app < seed.sql
```

После старта приложение доступно на `http://localhost:8000`.

Swagger UI: `http://localhost:8000/docs`  
Redoc: `http://localhost:8000/redoc`

## Локальный запуск (без Docker)

```bash
poetry install
poetry run alembic upgrade head
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## Переменные окружения

Смотри `.env`:

- `DATABASE_URL` — строка подключения к БД
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- `API_KEY` — зарезервировано для статического ключа (аутентификация не подключена)

## Основные эндпоинты

### Organizations

- `GET /organizations/{org_id}` — получить организацию по id
- `POST /organizations` — создать организацию
- `GET /organizations` — список организаций с фильтрами:
  - `building_id`
  - `name` (поиск по названию)
  - `activity_id`
  - `include_children` (учитывать дочерние виды деятельности)
- `GET /organizations/geo/radius` — поиск в радиусе:
  - `lat`, `lon`, `radius_m`
- `GET /organizations/geo/bbox` — поиск в прямоугольнике:
  - `min_lat`, `min_lon`, `max_lat`, `max_lon`

### Buildings

- `GET /buildings` — список зданий

### Activities

- `GET /activities` — список видов деятельности
- `POST /activities` — создать вид деятельности

## Примеры запросов

```bash
curl "http://localhost:8000/organizations?building_id=1"
curl "http://localhost:8000/organizations?activity_id=1&include_children=true"
curl "http://localhost:8000/organizations/geo/radius?lat=55.75&lon=37.61&radius_m=1000"
```

## Структура проекта

- `src/main.py` — точка входа FastAPI
- `src/restfulapi/` — роутеры
- `src/db/` — модели, схемы, сессия
- `alembic/` — миграции
- `seed.sql` — тестовые данные
