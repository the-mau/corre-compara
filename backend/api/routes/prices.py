import asyncio
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.connection import get_db
from scrapers.liverpool import LiverpoolScraper
from scrapers.mercadolibre import MercadoLibreScraper


router = APIRouter(tags=["prices"])


@router.get("/prices/health")
async def prices_health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/prices/scrape/{product_id}")
async def scrape_product_prices(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    product_sql = text("SELECT id, name FROM products WHERE id = :id")
    product_row = (await db.execute(product_sql, {"id": str(product_id)})).mappings().first()
    if not product_row:
        raise HTTPException(status_code=404, detail="Product not found")

    meli_sql = text(
        """
        SELECT id, name, domain, affiliate_tag
        FROM stores
        WHERE active = true
          AND (domain ILIKE '%mercadolibre%' OR name ILIKE '%mercado libre%')
        LIMIT 1
        """
    )
    liverpool_sql = text(
        """
        SELECT id, name, domain, affiliate_tag
        FROM stores
        WHERE active = true
          AND (domain ILIKE '%liverpool%' OR name ILIKE '%liverpool%')
        LIMIT 1
        """
    )
    meli_store = (await db.execute(meli_sql)).mappings().first()
    liverpool_store = (await db.execute(liverpool_sql)).mappings().first()

    name = product_row["name"]
    pid = product_row["id"]

    meli_scraper = MercadoLibreScraper(db)
    liverpool_scraper = LiverpoolScraper(db)

    async def scrape_meli() -> list[Any]:
        if not meli_store:
            return []
        return await meli_scraper.scrape(name)

    async def scrape_liverpool() -> list[Any]:
        if not liverpool_store:
            return []
        return await liverpool_scraper.scrape(name)

    meli_prices, liverpool_prices = await asyncio.gather(scrape_meli(), scrape_liverpool())

    if meli_store:
        await meli_scraper.save_prices(product_id=pid, store_id=meli_store["id"], prices=meli_prices)
    if liverpool_store:
        await liverpool_scraper.save_prices(
            product_id=pid, store_id=liverpool_store["id"], prices=liverpool_prices
        )

    x, y = len(meli_prices), len(liverpool_prices)
    return {
        "product_id": str(pid),
        "results": x + y,
        "by_store": {"mercadolibre": x, "liverpool": y},
    }


@router.get("/prices/latest/{product_id}")
async def get_latest_prices(
    product_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Último precio por tienda para un producto (similar a /products/{id}/prices).
    """
    sql = text(
        """
        SELECT DISTINCT ON (p.store_id)
          p.id,
          p.product_id,
          p.store_id,
          s.name AS store_name,
          s.domain,
          s.affiliate_tag,
          p.price,
          p.currency,
          p.url,
          p.in_stock,
          p.size_available,
          p.scraped_at
        FROM price_history p
        JOIN stores s ON s.id = p.store_id
        WHERE p.product_id = :id
        ORDER BY p.store_id, p.scraped_at DESC
        """
    )

    rows = (await db.execute(sql, {"id": str(product_id)})).mappings().all()
    return [dict(r) for r in rows]


