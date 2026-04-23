 # Corre Compara

Monitor y comparador de precios de tenis de running para corredores en México (mezcla de Keepa + Trivago).

## Objetivo

- Búsqueda por modelo/marca (Nike, Adidas, ASICS, New Balance).
- Rastreo de precios en 5 tiendas: `Nike.com.mx`, `Adidas.com.mx`, `Liverpool.com.mx`, `Marti.com.mx` y `Mercado Libre MX`.
- Freemium:
  - Búsqueda gratis.
  - Alertas de precio sólo para usuarios premium.
- Ingreso principal vía afiliados (links con tracking a las tiendas).

## Stack

- Backend: Python 3.11 + FastAPI
- Scrapers: Python + Playwright (y Mercado Libre por API pública)
- DB: PostgreSQL (SQL estándar; compatible con Supabase)
- Task queue: Celery + Redis
- Frontend: Next.js 14 + TypeScript + Tailwind CSS
- Auth: Supabase Auth (JWT)

## Requisitos

- Docker / Docker Compose

## Variables de entorno

Duplica `.env.example` a `.env` y completa los valores necesarios.

## Levantar en local con Docker

1. Crear `.env` desde `.env.example`
2. Ejecutar:

```bash
docker compose up --build
```

Accesos:

- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## Estructura

- `backend/`: API, scrapers, modelo de datos, Celery tasks y esquema SQL.
- `frontend/`: App web con App Router y componentes de UI.

