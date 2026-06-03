"""Real scraper for one public bike listing page.

This scraper reads Bike-Discount's public bike category page with `requests`
and parses the returned HTML with BeautifulSoup. It is intentionally written in
a beginner-friendly style, with small helper methods and comments explaining
why each step exists.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from bike_alert.models import BikeListing
from bike_alert.scrapers.base import BaseScraper


logger = logging.getLogger(__name__)


class BikeDiscountScraper(BaseScraper):
    """Scrape bike products from one Bike-Discount listing page."""

    LISTING_URL = "https://www.bike-discount.de/en/bike/bike"
    SOURCE_NAME = "Bike-Discount"

    # A browser-like user agent helps polite public websites understand that
    # this is a normal HTTP request instead of an unknown script.
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }

    @property
    def name(self) -> str:
        """Return the display name for logs and stored rows."""

        return self.SOURCE_NAME

    def fetch_listings(self) -> list[BikeListing]:
        """Download the public listing page and return parsed bike listings."""

        logger.info("Requesting bike listing page: %s", self.LISTING_URL)

        try:
            response = requests.get(
                self.LISTING_URL,
                headers=self.HEADERS,
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as error:
            # Returning an empty list keeps the app running even if the website
            # is temporarily unavailable or the local network is offline.
            logger.warning("Could not fetch %s: %s", self.LISTING_URL, error)
            return []

        logger.info("Downloaded %s bytes of HTML", len(response.text))

        soup = BeautifulSoup(response.text, "html.parser")
        product_cards = self._find_product_cards(soup)
        logger.info("Found %s possible product cards", len(product_cards))

        listings: list[BikeListing] = []
        for product_card in product_cards:
            listing = self._parse_product_card(product_card)
            if listing is None:
                continue

            listings.append(listing)
            logger.info(
                "Extracted listing: title=%r price=%r location=%r url=%s",
                listing.title,
                listing.price,
                listing.location,
                listing.url,
            )

        logger.info("Extracted %s listings from %s", len(listings), self.name)
        return listings

    def _find_product_cards(self, soup: BeautifulSoup) -> list[Tag]:
        """Find product card elements in the listing page HTML.

        Websites often use CSS classes such as `product-box` or
        `cms-listing-col` for product cards. We try a few likely selectors so
        the scraper is easier to understand and a little more tolerant of small
        HTML changes.
        """

        selectors = [
            ".product-box",
            ".cms-listing-col",
            "[itemtype*='Product']",
        ]

        for selector in selectors:
            cards = [card for card in soup.select(selector) if isinstance(card, Tag)]
            if cards:
                logger.info("Using product card selector: %s", selector)
                return cards

        logger.warning("No product cards found in the downloaded HTML")
        return []

    def _parse_product_card(self, product_card: Tag) -> BikeListing | None:
        """Convert one product card element into a `BikeListing`.

        If a card does not contain both a title and URL, it is skipped because
        those fields are required for useful database storage and duplicate
        detection.
        """

        title = self._extract_title(product_card)
        url = self._extract_url(product_card)

        if title is None or url is None:
            logger.debug("Skipping product card without title or URL")
            return None

        return BikeListing(
            title=title,
            price=self._extract_price(product_card),
            location="Online shop",
            url=url,
            source=self.name,
            posted_date=None,
        )

    def _extract_title(self, product_card: Tag) -> str | None:
        """Extract and clean the product title from one product card."""

        selectors = [
            ".product-name",
            "[itemprop='name']",
            "a[title]",
        ]

        for selector in selectors:
            element = product_card.select_one(selector)
            if element is None:
                continue

            title = self._clean_text(element.get_text(" ", strip=True))
            if title:
                return title

            if isinstance(element, Tag):
                title_attribute = element.get("title")
                if isinstance(title_attribute, str) and title_attribute.strip():
                    return self._clean_text(title_attribute)

        return None

    def _extract_url(self, product_card: Tag) -> str | None:
        """Extract the product detail URL and turn it into an absolute URL."""

        link = product_card.select_one("a[href]")
        if link is None:
            return None

        href = link.get("href")
        if not isinstance(href, str) or not href.strip():
            return None

        return urljoin(self.LISTING_URL, href)

    def _extract_price(self, product_card: Tag) -> int | None:
        """Extract the current price as an integer number of euros.

        The `BikeListing` model stores `price` as an integer. For this beginner
        project we keep only whole euros, so a page price like `1.599,00 €`
        becomes `1599`.
        """

        selectors = [
            ".product-price",
            ".price",
            "[itemprop='price']",
        ]

        for selector in selectors:
            element = product_card.select_one(selector)
            if element is None:
                continue

            text = element.get("content") if isinstance(element, Tag) else None
            if not isinstance(text, str):
                text = element.get_text(" ", strip=True)

            price = self._parse_euro_price(text)
            if price is not None:
                return price

        return None

    def _parse_euro_price(self, text: str) -> int | None:
        """Parse visible European-formatted prices into whole euros.

        Some product cards show both a recommended retail price and a lower
        current price. For an alert app, the lower visible price is usually the
        useful one, so this method returns the smallest parsed euro amount.
        """

        matches = re.findall(r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{2})?)", text)
        if not matches:
            return None

        prices: list[int] = []
        for raw_price in matches:
            # Convert German-style prices such as "1.599,00" into "1599.00".
            normalized = raw_price.replace(".", "").replace(",", ".")

            try:
                prices.append(int(float(normalized)))
            except ValueError:
                logger.debug("Could not parse price text: %r", text)

        if not prices:
            return None

        return min(prices)

    def _clean_text(self, text: str) -> str:
        """Collapse repeated whitespace into single spaces."""

        return " ".join(text.split())
