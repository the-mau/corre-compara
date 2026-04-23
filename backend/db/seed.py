import asyncio
import os
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from .connection import engine as async_engine


STORES = [
    {"name": "Nike Oficial", "domain": "nike.com.mx", "affiliate_tag": "nike-mx", "country": "MX"},
    {"name": "Adidas Oficial", "domain": "adidas.com.mx", "affiliate_tag": "adidas-mx", "country": "MX"},
    {"name": "Liverpool", "domain": "liverpool.com.mx", "affiliate_tag": "liverpool-mx", "country": "MX"},
    {"name": "Martí", "domain": "marti.com.mx", "affiliate_tag": "marti-mx", "country": "MX"},
    {"name": "Mercado Libre", "domain": "mercadolibre.com.mx", "affiliate_tag": "meli-mx", "country": "MX"},
]

PRODUCTS = [
    ("Nike Pegasus 41", "Nike", "road"),
    ("Nike Vomero 18", "Nike", "road"),
    ("Adidas Supernova Rise", "Adidas", "road"),
    ("Adidas Ultraboost 5", "Adidas", "road"),
    ("ASICS Gel-Kayano 31", "ASICS", "road"),
    ("ASICS Gel-Nimbus 26", "ASICS", "road"),
    ("New Balance Fresh Foam X 1080v14", "New Balance", "road"),
    ("New Balance FuelCell SuperComp Elite v4", "New Balance", "road"),
]


async def _upsert_store(db: AsyncSession, store: dict[str, Any]) -> None:
    exists_sql = text("SELECT id FROM stores WHERE name = :name")
    row = (await db.execute(exists_sql, {"name": store["name"]})).mappings().first()
    if row:
        update_sql = text(
            """
            UPDATE stores
            SET domain = :domain,
                affiliate_tag = :affiliate_tag,
                country = :country,
                active = true
            WHERE id = :id
            """
        )
        await db.execute(
            update_sql,
            {
                "id": row["id"],
                "domain": store["domain"],
                "affiliate_tag": store["affiliate_tag"],
                "country": store["country"],
            },
        )
    else:
        insert_sql = text(
            """
            INSERT INTO stores (name, domain, affiliate_tag, country, active)
            VALUES (:name, :domain, :affiliate_tag, :country, true)
            """
        )
        await db.execute(insert_sql, store)


async def _upsert_product(db: AsyncSession, name: str, brand: str, category: str) -> None:
    exists_sql = text("SELECT id FROM products WHERE name = :name")
    row = (await db.execute(exists_sql, {"name": name})).mappings().first()
    model_code = name.lower().replace(" ", "-")

    if row:
        update_sql = text(
            """
            UPDATE products
            SET brand = :brand,
                category = :category,
                model_code = :model_code
            WHERE id = :id
            """
        )
        await db.execute(
            update_sql,
            {
                "id": row["id"],
                "brand": brand,
                "category": category,
                "model_code": model_code,
            },
        )
    else:
        insert_sql = text(
            """
            INSERT INTO products (name, brand, category, model_code)
            VALUES (:name, :brand, :category, :model_code)
            """
        )
        await db.execute(
            insert_sql,
            {
                "name": name,
                "brand": brand,
                "category": category,
                "model_code": model_code,
            },
        )


async def main() -> None:
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL no está configurado (revisa tu .env)")

    async with AsyncSession(async_engine) as db:
        for store in STORES:
            await _upsert_store(db, store)

        for name, brand, category in PRODUCTS:
            await _upsert_product(db, name, brand, category)

        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())

