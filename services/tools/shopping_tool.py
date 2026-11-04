"""Bounded storefront extraction; never manufactures prices or review claims."""

import asyncio
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from services.http import UpstreamError

POSITIVE = {"good", "great", "excellent", "durable", "comfortable", "superb", "worth"}
NEGATIVE = {"bad", "broken", "poor", "fake", "defective", "waste", "worst"}


def sentiment(reviews: list[str]) -> dict:
    words = re.findall(r"[a-z]+", " ".join(reviews).lower())
    positive = sum(word in POSITIVE for word in words)
    negative = sum(word in NEGATIVE for word in words)
    return {
        "label": "positive"
        if positive > negative
        else "negative"
        if negative > positive
        else "mixed_or_unknown",
        "sample_count": len(reviews),
        "method": "English keyword baseline; not fake-review detection",
    }


def number(text: str) -> float | None:
    match = re.search(r"[0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?", text)
    return float(match.group().replace(",", "")) if match else None


class ShoppingTool:
    def __init__(self, client) -> None:
        self.client = client

    async def _html(self, url: str, params: dict | None = None) -> str:
        async with self.client.stream(
            "GET",
            url,
            params=params,
            follow_redirects=False,
            headers={"User-Agent": "Thirdhand/1.0 product comparison"},
        ) as response:
            response.raise_for_status()
            if response.is_redirect:
                raise UpstreamError(
                    "Storefront redirected; automated search unavailable"
                )
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > 2097152:
                    raise UpstreamError("Storefront page exceeded size limit")
        text = body.decode("utf-8", errors="replace")
        if any(
            marker in text.lower()
            for marker in ("enter the characters you see", "captcha", "access denied")
        ):
            raise UpstreamError("Storefront blocks automated access")
        return text

    async def _store(self, store: str, query: str) -> list[dict]:
        amazon = store == "amazon"
        base = "https://www.amazon.in" if amazon else "https://www.flipkart.com"
        html = await self._html(
            base + ("/s" if amazon else "/search"), {"k" if amazon else "q": query}
        )
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(
            '[data-component-type="s-search-result"]' if amazon else "[data-id]"
        )
        products = []
        for card in cards[:20]:
            title = card.select_one(
                "h2" if amazon else ".KzDlHZ, .s1Q9rs, .WKTcLC, .wjcEIp"
            )
            link = card.select_one('a[href*="/dp/"]' if amazon else 'a[href*="/p/"]')
            price = card.select_one(
                ".a-price .a-offscreen" if amazon else ".Nx9bqj, ._30jeq3"
            )
            rating = card.select_one(".a-icon-alt" if amazon else ".XQDdHH, ._3LWZlK")
            if not title or not link or not price:
                continue
            price_value = number(price.get_text())
            url = urljoin(base, link.get("href", ""))
            if (
                price_value is None
                or price_value <= 0
                or urlsplit(url).hostname != urlsplit(base).hostname
            ):
                continue
            products.append(
                {
                    "store": store,
                    "title": title.get_text(" ", strip=True)[:300],
                    "price_inr": price_value,
                    "rating": number(rating.get_text()) if rating else None,
                    "url": url,
                }
            )
        if not products:
            raise UpstreamError(
                "No parseable products; storefront layout or availability changed"
            )
        return products[:5]

    async def _reviews(self, product: dict) -> dict:
        try:
            html = await self._html(product["url"])
            soup = BeautifulSoup(html, "html.parser")
            reviews = [
                node.get_text(" ", strip=True)[:1000]
                for node in soup.select('[data-hook="review-body"], .ZmyHeo, .t-ZTKy')[
                    :10
                ]
            ]
            return {**product, "review_sentiment": sentiment(reviews)}
        except Exception:
            return {
                **product,
                "review_sentiment": {"label": "unavailable", "sample_count": 0},
            }

    async def compare_ecommerce_products(
        self, query: str, max_budget: float | None = None
    ) -> dict:
        if (
            not query.strip()
            or len(query) > 200
            or (max_budget is not None and max_budget <= 0)
        ):
            raise ValueError("Invalid product query or budget")
        values = await asyncio.gather(
            self._store("amazon", query),
            self._store("flipkart", query),
            return_exceptions=True,
        )
        products, unavailable = [], []
        for store, value in zip(("amazon", "flipkart"), values):
            if isinstance(value, Exception):
                unavailable.append(store)
            else:
                products.extend(value)
        products = [
            p for p in products if max_budget is None or p["price_inr"] <= max_budget
        ]
        products.sort(key=lambda p: (p["price_inr"], -(p["rating"] or 0)))
        enriched = await asyncio.gather(*(self._reviews(p) for p in products[:3]))
        return {
            "products": enriched,
            "unavailable_stores": unavailable,
            "ranking": "Lowest observed price, then rating. Products may be different models; confirm specification, seller, shipping and current price before buying.",
        }
