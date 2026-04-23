import asyncio
import logging
import random
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


USER_AGENTS: list[str] = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
]


class BaseScraper(ABC):
    """
    Clase base para scrapers.

    - Define rotación de user-agent.
    - Aplica delay aleatorio entre requests.
    - Provee save_prices() para persistir en DB.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _pick_user_agent(self) -> str:
        return random.choice(USER_AGENTS)

    async def _delay_between_requests(self) -> None:
        await asyncio.sleep(random.uniform(1, 3))

    @abstractmethod
    async def scrape(self, product_name: str) -> list[dict[str, Any]]:
        """
        Devuelve una lista de precios encontrados.

        Cada dict debería incluir como mínimo:
        - price: Decimal | float | str
        - url: str | None
        - in_stock: bool
        - size_available: list[str]
        - currency: str
        """

    async def save_prices(
        self,
        product_id: UUID,
        store_id: UUID,
        prices: list[dict[str, Any]],
    ) -> None:
        if not prices:
            return

        insert_sql = text(
            """
            INSERT INTO price_history (
              product_id, store_id, price, currency, url, in_stock, size_available, scraped_at
            )
            VALUES (
              :product_id, :store_id, :price, :currency, :url, :in_stock, :size_available, now()
            )
            """
        )

        try:
            for item in prices:
                price_val = item.get("price")
                currency = item.get("currency") or "MXN"
                url = item.get("url")
                in_stock = bool(item.get("in_stock", False))
                size_available = item.get("size_available") or []

                # Aseguramos Decimal para SQL DECIMAL.
                if not isinstance(price_val, Decimal):
                    price_val = Decimal(str(price_val))

                await self.db.execute(
                    insert_sql,
                    {
                        "product_id": str(product_id),
                        "store_id": str(store_id),
                        "price": price_val,
                        "currency": currency,
                        "url": url,
                        "in_stock": in_stock,
                        "size_available": size_available,
                    },
                )

            await self.db.commit()
        except Exception:
            logger.exception("Error guardando precios para product_id=%s store_id=%s", product_id, store_id)
            await self.db.rollback()

