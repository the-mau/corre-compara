import logging
import os
from decimal import Decimal
from typing import Any
from urllib.parse import quote_plus

import httpx

from scrapers.base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class MercadoLibreScraper(BaseScraper):
    """
    Usa la API pública de Mercado Libre (no scraping).
    Endpoint:
      https://api.mercadolibre.com/sites/MLM/search?q={query}&limit=5
    """

    API_URL = "https://api.mercadolibre.com/sites/MLM/search"
    TOKEN_URL = "https://api.mercadolibre.com/oauth/token"

    async def _get_access_token(self) -> str | None:
        client_id = os.getenv("MELI_CLIENT_ID")
        client_secret = os.getenv("MELI_CLIENT_SECRET")
        if not client_id or not client_secret:
            logger.error("MELI_CLIENT_ID o MELI_CLIENT_SECRET no configurados")
            return None

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(self.TOKEN_URL, data=payload)
                res.raise_for_status()
                data = res.json()
                token = data.get("access_token")
                if not token:
                    logger.error("No se recibió access_token de Mercado Libre")
                    return None
                return token
        except Exception:
            logger.exception("Error obteniendo OAuth token de Mercado Libre")
            return None

    async def scrape(self, product_name: str) -> list[dict[str, Any]]:
        await self._delay_between_requests()

        access_token = await self._get_access_token()
        if not access_token:
            return []

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Referer": "https://www.mercadolibre.com.mx/",
            "Origin": "https://www.mercadolibre.com.mx",
            "Authorization": f"Bearer {access_token}",
        }
        url = f"{self.API_URL}?q={quote_plus(product_name)}&limit=10"

        try:
            async with httpx.AsyncClient(headers=headers, timeout=15.0) as client:
                res = await client.get(url)
                res.raise_for_status()
                data = res.json()
        except Exception:
            logger.exception("MercadoLibre scrape falló para query=%s", product_name)
            return []

        results = data.get("results") or []
        logger.info("MercadoLibre API returned %s results (pre-filter) for query=%s", len(results), product_name)
        prices: list[dict[str, Any]] = []

        def is_preferred(item: dict[str, Any]) -> bool:
            listing_type = item.get("listing_type_id")
            official_store_id = item.get("official_store_id")
            return listing_type in ("gold_special", "gold_pro") or official_store_id is not None

        preferred = [item for item in results if is_preferred(item)]
        # Si el filtro no da resultados, tomamos fallback de los primeros 3 de cualquier vendedor.
        chosen = preferred if preferred else results[:3]

        for item in chosen:
            listing_type = item.get("listing_type_id")
            official_store_id = item.get("official_store_id")

            currency = item.get("currency_id") or "MXN"
            amount = item.get("price")
            if amount is None:
                continue

            thumb = item.get("thumbnail")
            permalink = item.get("permalink")
            if not permalink:
                continue

            # URL de afiliado sencilla para Corre Compara.
            affiliate_url = f"{permalink}?ref=correcompara"

            available_quantity = item.get("available_quantity")
            in_stock = bool(available_quantity is None or available_quantity > 0)

            prices.append(
                {
                    "title": item.get("title"),
                    "price": Decimal(str(amount)),
                    "currency": currency,
                    "url": affiliate_url,
                    "in_stock": in_stock,
                    "size_available": [],
                    "thumbnail": thumb,
                    "listing_type_id": listing_type,
                    "official_store_id": official_store_id,
                }
            )

        return prices

