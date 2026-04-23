from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from db.connection import get_db


router = APIRouter(tags=["products"])


@router.get("/products")
async def list_products(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT id, name, brand, model_code, category, image_url, created_at
        FROM products
        ORDER BY brand, name
        """
    )
    rows = (await db.execute(sql)).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/search")
async def search_products(
    q: str = Query(..., min_length=1),
    brand: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    pattern = f"%{q}%"

    sql = text(
        """
        SELECT
          id, name, brand, model_code, category, image_url, created_at
        FROM products
        WHERE (name ILIKE :pattern OR model_code ILIKE :pattern)
          AND (:brand IS NULL OR brand = :brand)
        ORDER BY created_at DESC
        LIMIT 20
        """
    )

    rows = (await db.execute(sql, {"pattern": pattern, "brand": brand})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/{id}")
async def get_product(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    sql = text(
        """
        SELECT id, name, brand, model_code, category, image_url, created_at
        FROM products
        WHERE id = :id
        """
    )
    row = (await db.execute(sql, {"id": str(id)})).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return dict(row)


@router.get("/products/{id}/prices")
async def get_product_prices(
    id: UUID,
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Devuelve el último precio por tienda para el producto.
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

    rows = (await db.execute(sql, {"id": str(id)})).mappings().all()
    return [dict(r) for r in rows]


@router.get("/products/{id}/history")
async def get_product_history(
    id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """
    Historial agregado (mejor precio por día) para graficar.
    """
    sql = text(
        """
        WITH daily AS (
          SELECT
            date_trunc('day', scraped_at) AS day,
            product_id,
            MIN(price) AS best_price
          FROM price_history
          WHERE product_id = :id
            AND scraped_at >= now() - (:days || ' days')::interval
          GROUP BY day, product_id
        )
        SELECT
          gen_random_uuid() AS id,
          d.product_id,
          NULL::uuid AS store_id,
          NULL::text AS store_name,
          d.best_price AS price,
          'MXN' AS currency,
          NULL::text AS url,
          false AS in_stock,
          NULL::text[] AS size_available,
          d.day AS scraped_at
        FROM daily d
        ORDER BY d.day ASC
        """
    )

    rows = (await db.execute(sql, {"id": str(id), "days": days})).mappings().all()
    return [dict(r) for r in rows]

