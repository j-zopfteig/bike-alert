"""Velomarkt.ch scraper for Swiss used-bike listings.

Velomarkt is the first real marketplace source for this project. The scraper
starts with one configurable search/category URL, downloads the page with
`requests`, parses listing cards with BeautifulSoup, and returns `BikeListing`
objects for the rest of the app.
"""

import logging
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4.element import Tag
import requests

from bike_alert.frame_size import evaluate_frame_size
from bike_alert.models import BikeListing
from bike_alert.scrapers.base import BaseScraper


logger = logging.getLogger(__name__)


class VelomarktScraper(BaseScraper):
    """Scrape one configured Velomarkt.ch listing page."""

    SOURCE_NAME = "Velomarkt.ch"
    BASE_URL = "https://velomarkt.ch"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9,de-CH;q=0.8,de;q=0.7",
    }

    @property
    def name(self) -> str:
        """Return the display name used in logs and stored rows."""

        return self.SOURCE_NAME

    def fetch_listings(self) -> list[BikeListing]:
        """Fetch and parse listings from the configured Velomarkt URL."""

        url = self.search_config.velomarkt_search_url
        logger.info("Requesting Velomarkt page: %s", url)

        try:
            response = requests.get(url, headers=self.HEADERS, timeout=20)
            response.raise_for_status()
        except requests.RequestException as error:
            logger.warning("Could not fetch Velomarkt page %s: %s", url, error)
            return []

        logger.info("Downloaded %s bytes from Velomarkt", len(response.text))

        soup = BeautifulSoup(response.text, "html.parser")
        cards = [card for card in soup.select(".bike-item") if isinstance(card, Tag)]
        logger.info("Found %s Velomarkt listing cards", len(cards))

        listings: list[BikeListing] = []
        for card in cards:
            listing = self._parse_card(card)
            if listing is None:
                continue

            listings.append(listing)
            logger.info(
                "Extracted Velomarkt listing: title=%r brand=%r price=%r "
                "location=%r frame_size=%r confidence=%s relevant=%s review=%s url=%s",
                listing.title,
                listing.brand,
                listing.price,
                listing.location,
                listing.frame_size,
                listing.frame_size_confidence,
                listing.is_relevant,
                listing.needs_manual_review,
                listing.url,
            )

        logger.info("Extracted %s Velomarkt listings", len(listings))
        return listings

    def _parse_card(self, card: Tag) -> BikeListing | None:
        """Convert one Velomarkt `.bike-item` card into a `BikeListing`."""

        title = self._extract_title(card)
        url = self._extract_url(card)
        raw_text = self._clean_text(card.get_text("\n", strip=True))

        if title is None or url is None:
            logger.debug("Skipping Velomarkt card without title or URL")
            return None

        brand = self._extract_labeled_value(card, "Brand")
        visible_frame_size = self._extract_labeled_value(card, "Frame size")
        frame_result = evaluate_frame_size(
            title=title,
            raw_text=raw_text,
            target_frame_sizes=self.search_config.target_frame_sizes,
        )

        return BikeListing(
            title=title,
            price=self._extract_price(raw_text),
            location=self._extract_location(raw_text),
            url=url,
            source=self.name,
            posted_date=None,
            brand=brand,
            model=self._derive_model(title=title, brand=brand),
            condition=self._extract_labeled_value(card, "Condition"),
            frame_size=frame_result.frame_size or visible_frame_size,
            frame_size_confidence=frame_result.confidence,
            raw_text=raw_text,
            is_relevant=frame_result.is_relevant,
            needs_manual_review=frame_result.needs_manual_review,
        )

    def _extract_title(self, card: Tag) -> str | None:
        """Read the listing title from the card heading."""

        heading = card.select_one("h3")
        if heading is None:
            return None

        title = heading.get_text(" ", strip=True)
        return title or None

    def _extract_url(self, card: Tag) -> str | None:
        """Read the listing detail URL and convert it to an absolute URL."""

        title_link = card.select_one(".item-title a[href], .item-name a[href]")
        link = title_link or card.select_one("a[href]")
        if link is None:
            return None

        href = link.get("href")
        if not isinstance(href, str) or not href.strip():
            return None

        return urljoin(self.BASE_URL, href)

    def _extract_labeled_value(self, card: Tag, label: str) -> str | None:
        """Extract values from Velomarkt label/value lines.

        Velomarkt cards render details like:

        `Brand:`
        `TREK`

        Using line positions is easier for beginners to follow than a dense CSS
        selector that depends on every nested element.
        """

        lines = self._card_lines(card)
        label_text = f"{label}:"

        for index, line in enumerate(lines[:-1]):
            if line.casefold() == label_text.casefold():
                value = lines[index + 1].strip()
                return value or None

        return None

    def _extract_price(self, raw_text: str) -> int | None:
        """Extract a CHF price from the card text."""

        match = re.search(r"CHF\s+([\d']+)", raw_text)
        if match is None:
            return None

        return int(match.group(1).replace("'", ""))

    def _extract_location(self, raw_text: str) -> str | None:
        """Extract Swiss postcode and canton/city text from the card."""

        for line in raw_text.splitlines():
            if re.match(r"^\d{4}\s+.+", line):
                return line

        return None

    def _derive_model(self, title: str, brand: str | None) -> str | None:
        """Derive a simple model guess from the title and visible brand."""

        if brand is None:
            return None

        pattern = re.compile(rf"^{re.escape(brand)}\s+", flags=re.IGNORECASE)
        model = pattern.sub("", title).strip()
        return model or None

    def _card_lines(self, card: Tag) -> list[str]:
        """Return cleaned non-empty text lines from one listing card."""

        return [
            line.strip()
            for line in card.get_text("\n", strip=True).splitlines()
            if line.strip()
        ]

    def _clean_text(self, text: str) -> str:
        """Normalize whitespace while preserving useful line breaks."""

        lines = [" ".join(line.split()) for line in text.splitlines()]
        return "\n".join(line for line in lines if line)
