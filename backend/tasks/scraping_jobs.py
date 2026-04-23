import asyncio
import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from db.connection import engine as async_engine

from scrapers.adidas import AdidasScraper
from scrapers.liverpool import LiverpoolScraper
from scrapers.marti import MartiScraper
from scrapers.mercadolibre import MercadoLibreScraper
from scrapers.nike import NikeScraper

from tasks.celery_app import celery_app


logger = logging.getLogger(__name__)


async def _get_rows(db: AsyncSession, sql: text, params: dict[str, Any]) -> list[dict[str, Any]]:
    rows = (await db.execute(sql, params)).mappings().all()
    return [dict(r) for r in rows]


def _scraper_for_store(domain: str | None, name: str | None):
    key = f"{name or ''} {domain or ''}".lower()
    if "nike" in key:
        return NikeScraper
    if "adidas" in key:
        return AdidasScraper
    if "liverpool" in key:
        return LiverpoolScraper
    if "marti" in key:
        return MartiScraper
    if "mercadolibre" in key:
        return MercadoLibreScraper
    # Default: Mercado Libre como alternativa si el store no mapea.
    return None


async def _check_alerts_for_product(db: AsyncSession, product_id: UUID) -> None:
    """
    Placeholder:
    - Calcula el mejor precio en las últimas 24 horas.
    - Dispara alertas cuyo `target_price` sea >= ese mejor precio.
    """
    current_min_sql = text(
        """
        SELECT MIN(price) AS min_price
        FROM price_history
        WHERE product_id = :product_id
          AND scraped_at >= now() - interval '24 hours'
        """
    )
    current_row = (await db.execute(current_min_sql, {"product_id": str(product_id)})).mappings().first()
    min_price = current_row["min_price"] if current_row else None
    if min_price is None:
        return

    alerts_sql = text(
        """
        SELECT id, user_id, product_id, target_price
        FROM alerts
        WHERE product_id = :product_id
          AND active = true
          AND target_price >= :min_price
        """
    )
    alerts = await _get_rows(db, alerts_sql, {"product_id": str(product_id), "min_price": min_price})
    if not alerts:
        return

    # Marcamos como disparadas.
    trigger_sql = text(
        """
        UPDATE alerts
        SET active = false, triggered_at = now()
        WHERE id = :id
        """
    )
    for alert in alerts:
        await db.execute(trigger_sql, {"id": str(alert["id"])})
        # Email placeholder (tarea en background).
        send_alert_email.delay(alert_id=str(alert["id"]))

    await db.commit()


async def _scrape_product_for_store(db: AsyncSession, product: dict[str, Any], store: dict[str, Any]) -> None:
    scraper_cls = _scraper_for_store(store.get("domain"), store.get("name"))
    if scraper_cls is None:
        logger.warning("No scraper map para store=%s domain=%s", store.get("name"), store.get("domain"))
        return

    scraper = scraper_cls(db)
    scraped = await scraper.scrape(product["name"])

    await scraper.save_prices(product_id=product["id"], store_id=store["id"], prices=scraped)
    await _check_alerts_for_product(db, product["id"])


@celery_app.task
def scrape_all_products() -> str:
    """
    Itera todos los productos y ejecuta scraping solo para Mercado Libre y Liverpool.
    """

    async def _run() -> str:
        async with AsyncSession(async_engine) as db:
            # Productos (skeleton: sin campo activo, tomamos todos).
            products_sql = text("SELECT id, name FROM products")
            products = await _get_rows(db, products_sql, {})
            if not products:
                logger.info("No products found to scrape.")
                return "no-products"

            # Mercado Libre + Liverpool (scrapers activos en este flujo).
            stores_sql = text(
                """
                SELECT id, name, domain, affiliate_tag, active
                FROM stores
                WHERE active = true
                  AND (
                    domain ILIKE '%mercadolibre%'
                    OR name ILIKE '%mercado libre%'
                    OR domain ILIKE '%liverpool%'
                    OR name ILIKE '%liverpool%'
                  )
                """
            )
            stores = await _get_rows(db, stores_sql, {})
            if not stores:
                logger.info("No Mercado Libre / Liverpool stores found to scrape.")
                return "no-stores"

            for product in products:
                # Convertimos id a UUID (asegura tipo para save_prices).
                product["id"] = UUID(str(product["id"]))
                for store in stores:
                    store["id"] = UUID(str(store["id"]))
                    await _scrape_product_for_store(db, product, store)

        return "ok"

    return asyncio.run(_run())


@celery_app.task
def check_alerts(product_id: str) -> str:
    """
    Tarea separada (útil si luego queremos llamarla desde otros flows).
    """

    async def _run() -> str:
        async with AsyncSession(async_engine) as db:
            await _check_alerts_for_product(db, UUID(product_id))
            return "ok"

    return asyncio.run(_run())


@celery_app.task
def send_alert_email(alert_id: str) -> str:
    """
    Placeholder: se reemplaza por integración real de email.
    """
    logger.info("send_alert_email placeholder alert_id=%s", alert_id)
    return "sent-placeholder"

