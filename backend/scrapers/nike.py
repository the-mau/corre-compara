import logging
import re
from decimal import Decimal
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from scrapers.base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class NikeScraper(BaseScraper):
    """
    Scraper con Playwright para nike.com.mx.
    Buscar por nombre de modelo y extraer precio/URL/disponibilidad de tallas.

    Nota: Nike es altamente dinámica; este scraper intenta varias estrategias.
    """

    SEARCH_URL = "https://www.nike.com/mx/es/search?q={query}"

    async def scrape(self, product_name: str) -> list[dict[str, Any]]:
        await self._delay_between_requests()

        search_url = self.SEARCH_URL.format(query=quote_plus(product_name))
        user_agent = self._pick_user_agent()

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=user_agent, viewport={"width": 1280, "height": 720})
                page = await context.new_page()

                await page.goto(search_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                # Intento 1: capturar precio desde primer card.
                # Selectores son best-effort; si fallan, regresamos [].
                price_text = None
                possible_price_selectors = [
                    "[data-testid*='price']",
                    "span[class*='price']",
                    "span[class*='Price']",
                ]
                for sel in possible_price_selectors:
                    try:
                        el = await page.query_selector(sel)
                        if el:
                            txt = (await el.inner_text()).strip()
                            if txt:
                                price_text = txt
                                break
                    except Exception:
                        continue

                product_url = None
                possible_link_selectors = ["a[href*='/p/']", "a[href*='/product/']", "a[href*='/es/']"]
                for sel in possible_link_selectors:
                    try:
                        a = await page.query_selector(sel)
                        if a:
                            href = await a.get_attribute("href")
                            if href:
                                product_url = href if href.startswith("http") else f"https://www.nike.com{href}"
                                break
                    except Exception:
                        continue

                if not price_text and not product_url:
                    await browser.close()
                    return []

                # Normalizamos el precio (ej. "$1,299.00" o "MX$ 1,299").
                cleaned = re.sub(r"[^\d.,]", "", price_text or "")
                cleaned = cleaned.replace(",", "")
                price = Decimal(cleaned) if cleaned else Decimal("0")

                # Tallas: intento best-effort.
                size_available: list[str] = []
                try:
                    for badge_sel in ["button[aria-label*='Talla']", "[data-testid*='size'] button", "button[role='option']"]:
                        btns = await page.query_selector_all(badge_sel)
                        for b in btns[:10]:
                            t = (await b.inner_text()).strip()
                            if t and t not in size_available:
                                size_available.append(t)
                        if size_available:
                            break
                except Exception:
                    size_available = []

                await browser.close()
                return [
                    {
                        "price": price,
                        "currency": "MXN",
                        "url": product_url,
                        "in_stock": True if size_available else True,
                        "size_available": size_available,
                        "thumbnail": None,
                    }
                ]
        except Exception:
            logger.exception("Nike scrape falló para query=%s", product_name)
            return []

