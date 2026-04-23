import logging
from decimal import Decimal
from typing import Any
from urllib.parse import quote_plus

from playwright.async_api import async_playwright

from scrapers.base_scraper import BaseScraper


logger = logging.getLogger(__name__)


class MartiScraper(BaseScraper):
    """
    Scraper (Playwright) best-effort para marti.com.mx.
    """

    SEARCH_URL = "https://www.marti.com.mx/search?q={query}"

    async def scrape(self, product_name: str) -> list[dict[str, Any]]:
        await self._delay_between_requests()
        search_url = self.SEARCH_URL.format(query=quote_plus(product_name))

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(user_agent=self._pick_user_agent())
                page = await context.new_page()

                await page.goto(search_url, wait_until="domcontentloaded")
                await page.wait_for_load_state("networkidle")

                product_url = None
                price = None

                try:
                    a = await page.query_selector("a[href*='/p/'], a[href*='/producto/']")
                    if a:
                        href = await a.get_attribute("href")
                        if href:
                            product_url = href if href.startswith("http") else f"https://www.marti.com.mx{href}"
                except Exception:
                    pass

                try:
                    el = await page.query_selector("[class*='price'], [data-testid*='price']")
                    if el:
                        txt = (await el.inner_text()).strip()
                        cleaned = "".join(ch for ch in txt if ch.isdigit() or ch in ",.")
                        cleaned = cleaned.replace(",", "")
                        if cleaned:
                            price = Decimal(cleaned)
                except Exception:
                    pass

                await browser.close()

                if price is None and product_url is None:
                    return []

                return [
                    {
                        "price": price or Decimal("0"),
                        "currency": "MXN",
                        "url": product_url,
                        "in_stock": True,
                        "size_available": [],
                        "thumbnail": None,
                    }
                ]
        except Exception:
            logger.exception("Marti scrape falló para query=%s", product_name)
            return []

