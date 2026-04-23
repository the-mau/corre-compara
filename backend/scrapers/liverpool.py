import logging
import os
import re
from decimal import Decimal
from typing import Any
from urllib.parse import quote_plus, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper


logger = logging.getLogger(__name__)

SCRAPER_API_BASE = "http://api.scraperapi.com"
SEARCH_URL_TEMPLATE = "https://www.liverpool.com.mx/tienda/search?query={query}"

# Enlaces a PDP (Liverpool puede usar /p/ o rutas bajo /tienda/)
PRODUCT_HREF_PATTERN = re.compile(r"/p/|/tienda/", re.I)
PRICE_TEXT_PATTERN = re.compile(r"\$[\d,]+(?:\.\d{2})?")


def _affiliate_url(url: str) -> str:
    """Añade utm_source=correcompara (query o & si ya hay query)."""
    if not url:
        return url
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://www.liverpool.com.mx{url if url.startswith('/') else '/' + url}"
        parsed = urlparse(url)
    q = parsed.query
    if q:
        return urlunparse(parsed._replace(query=f"{q}&utm_source=correcompara"))
    return urlunparse(parsed._replace(query="utm_source=correcompara"))


def _parse_price_text(text: str) -> Decimal | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.,]", "", text.strip())
    if not cleaned:
        return None
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        parts = cleaned.split(",")
        if len(parts[-1]) == 2:
            cleaned = cleaned.replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned)
    except Exception:
        return None


def _normalize_href(href: str | None) -> str | None:
    if not href or href.startswith("#") or href.startswith("javascript:"):
        return None
    if not PRODUCT_HREF_PATTERN.search(href):
        return None
    if href.startswith("http"):
        return href
    return f"https://www.liverpool.com.mx{href if href.startswith('/') else '/' + href}"


def _extract_from_anchor(a: Any) -> dict[str, Any] | None:
    href = _normalize_href(a.get("href"))
    if not href:
        return None

    name = (a.get_text(strip=True) or a.get("title") or "").strip()
    if not name:
        name = "Producto Liverpool"

    price_val: Decimal | None = None
    thumb: str | None = None
    in_stock = True

    parent = a.parent
    for _ in range(8):
        if parent is None:
            break
        if price_val is None:
            for sel in ('[class*="price"]', '[class*="Price"]', "[data-testid*='price']"):
                pel = parent.select_one(sel)
                if pel:
                    price_val = _parse_price_text(pel.get_text())
                    if price_val is not None:
                        break
            if price_val is None:
                blob = parent.get_text(" ", strip=True)
                m = PRICE_TEXT_PATTERN.search(blob)
                if m:
                    price_val = _parse_price_text(m.group(0))
        if thumb is None:
            im = parent.select_one("img[src]")
            if im:
                src = im.get("src") or ""
                if src and not src.startswith("data:"):
                    thumb = src if src.startswith("http") else f"https:{src}" if src.startswith("//") else f"https://www.liverpool.com.mx{src}"
        parent = parent.parent

    return {
        "title": name,
        "price": price_val if price_val is not None else Decimal("0"),
        "currency": "MXN",
        "url": _affiliate_url(href),
        "in_stock": in_stock,
        "size_available": [],
        "thumbnail": thumb,
    }


class LiverpoolScraper(BaseScraper):
    """
    Liverpool.com.mx vía ScraperAPI (render JS) + BeautifulSoup.
    """

    async def scrape(self, product_name: str) -> list[dict[str, Any]]:
        await self._delay_between_requests()

        try:
            api_key = os.environ["SCRAPER_API_KEY"]
        except KeyError:
            logger.error("SCRAPER_API_KEY no está definida en el entorno")
            return []

        target_url = SEARCH_URL_TEMPLATE.format(query=quote_plus(product_name))
        params = {
            "api_key": api_key,
            "url": target_url,
            "render": "true",
            "country_code": "mx",
        }

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.get(SCRAPER_API_BASE, params=params)
                res.raise_for_status()
                html = res.text
        except httpx.HTTPStatusError as e:
            logger.exception("Liverpool ScraperAPI HTTP error: %s", e.response.status_code)
            return []
        except httpx.RequestError:
            logger.exception("Liverpool ScraperAPI request failed para query=%s", product_name)
            return []

        snippet = (html or "")[:500]
        logger.info("Liverpool ScraperAPI HTML (primeros 500 chars) query=%s: %r", product_name, snippet)

        soup = BeautifulSoup(html or "", "html.parser")
        anchors = soup.select('a[href*="/p/"], a[href*="/tienda/"]')

        results: list[dict[str, Any]] = []
        seen: set[str] = set()

        for a in anchors:
            if len(results) >= 5:
                break
            href = _normalize_href(a.get("href"))
            if not href or href in seen:
                continue
            seen.add(href)
            row = _extract_from_anchor(a)
            if row:
                results.append(row)

        logger.info("Liverpool: productos parseados=%s (máx 5) query=%s", len(results), product_name)
        return results
