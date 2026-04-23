import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.alerts import router as alerts_router
from api.routes.products import router as products_router
from api.routes.prices import router as prices_router
from api.routes.users import router as users_router


def _parse_origins(value: str) -> list[str]:
    value = (value or "").strip()
    if not value:
        return ["http://localhost:3000"]
    return [v.strip() for v in value.split(",") if v.strip()]


app = FastAPI(title="Corre Compara API", version="0.1.0")

origins = _parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
production_domain = os.getenv("PRODUCTION_DOMAIN")
if production_domain:
    # Soporte simple: si el dominio es `https://...` lo agregamos como origin.
    origins = list({*origins, production_domain})

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router)
app.include_router(prices_router)
app.include_router(alerts_router)
app.include_router(users_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}

