"""Velomarkt.ch scraper for Swiss used-bike listings.

Velomarkt is the first real marketplace source for this project. The scraper
starts with one configurable search/category URL, downloads the page with
`requests`, parses listing cards with BeautifulSoup, and returns `BikeListing`
objects for the rest of the app.
"""

import logging
import re
import time
from dataclasses import replace
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

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
    PAGE_DELAY_SECONDS = 1
    EXCLUDED_CATEGORY_KEYWORDS = {
        "accessories",
        "accessory",
        "parts",
        "clothing",
        "shoes",
        "helmets",
        "helmet",
        "components",
        "component",
        "spare parts",
        "tool",
        "tools",
    }
    INCLUDED_CATEGORY_KEYWORDS = {
        "bike",
        "bikes",
        "bicycle",
        "bicycles",
        "velo",
        "velos",
        "frame",
        "frames",
        "rahmen",
        "racing",
        "mountain",
        "city",
        "tour",
        "e-bike",
        "ebike",
        "electric",
        "gravel",
        "cyclo-cross",
        "kids",
    }
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

        listings: list[BikeListing] = []

        for page_number in range(1, self.search_config.max_pages + 1):
            page_url = self._build_page_url(page_number)
            logger.info("Requesting Velomarkt page %s: %s", page_number, page_url)

            try:
                response = requests.get(page_url, headers=self.HEADERS, timeout=20)
                response.raise_for_status()
            except requests.RequestException as error:
                logger.warning("Could not fetch Velomarkt page %s: %s", page_url, error)
                break

            logger.info("Downloaded %s bytes from Velomarkt", len(response.text))

            soup = BeautifulSoup(response.text, "html.parser")
            cards = [
                card for card in soup.select(".bike-item") if isinstance(card, Tag)
            ]
            logger.info(
                "Velomarkt page %s has %s listing cards",
                page_number,
                len(cards),
            )

            if not cards:
                logger.info("Stopping pagination because page %s has no cards", page_number)
                break

            for card in cards:
                parsed = self._parse_card(card)
                if parsed is None:
                    continue

                listing, category, subcategory = parsed
                filtered_listing = self._apply_filters(
                    listing=listing,
                    category=category,
                    subcategory=subcategory,
                )
                if filtered_listing is None:
                    continue

                listings.append(filtered_listing)
                logger.info(
                    "Keeping Velomarkt listing: title=%r brand=%r price=%r "
                    "location=%r frame_size=%r confidence=%s relevant=%s review=%s url=%s",
                    filtered_listing.title,
                    filtered_listing.brand,
                    filtered_listing.price,
                    filtered_listing.location,
                    filtered_listing.frame_size,
                    filtered_listing.frame_size_confidence,
                    filtered_listing.is_relevant,
                    filtered_listing.needs_manual_review,
                    filtered_listing.url,
                )

            if page_number < self.search_config.max_pages:
                time.sleep(self.PAGE_DELAY_SECONDS)

        logger.info("Extracted %s Velomarkt listings", len(listings))
        return listings

    def _parse_card(self, card: Tag) -> tuple[BikeListing, str | None, str | None] | None:
        """Convert one Velomarkt `.bike-item` card into a `BikeListing`."""

        title = self._extract_title(card)
        url = self._extract_url(card)
        raw_text = self._clean_text(card.get_text("\n", strip=True))

        if title is None or url is None:
            logger.debug("Skipping Velomarkt card without title or URL")
            return None

        brand = self._extract_labeled_value(card, "Brand")
        category = self._extract_labeled_value(card, "Category")
        subcategory = self._extract_labeled_value(card, "Subcategory")
        visible_frame_size = self._extract_labeled_value(card, "Frame size")
        frame_result = evaluate_frame_size(
            title=title,
            raw_text=raw_text,
            target_frame_sizes=self.search_config.target_frame_sizes,
        )

        listing = BikeListing(
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
        return listing, category, subcategory

    def _apply_filters(
        self,
        listing: BikeListing,
        category: str | None,
        subcategory: str | None,
    ) -> BikeListing | None:
        """Apply configured search filters to one parsed listing.

        Returning `None` means the listing is skipped and never reaches SQLite.
        Returning a `BikeListing` means the listing should be stored. Some kept
        listings are marked for manual review when important data is unclear.
        """

        if not self._matches_configured_brand(listing):
            logger.info("Skipping %r because no configured brand matched", listing.title)
            return None

        listing = self._apply_price_filter(listing)
        if listing is None:
            return None

        listing = self._apply_frame_size_filter(listing)
        if listing is None:
            return None

        return self._apply_category_filter(listing, category, subcategory)

    def _matches_configured_brand(self, listing: BikeListing) -> bool:
        """Check configured brands against title, brand, model, and raw text."""

        haystack = " ".join(
            value
            for value in [
                listing.title,
                listing.brand,
                listing.model,
                listing.raw_text,
            ]
            if value
        ).casefold()

        return any(brand.casefold() in haystack for brand in self.search_config.brands)

    def _apply_price_filter(self, listing: BikeListing) -> BikeListing | None:
        """Skip expensive listings and keep missing prices for manual review."""

        max_price = self.search_config.max_price
        if max_price <= 0:
            return listing

        if listing.price is None:
            logger.info("Keeping %r for manual review because price is missing", listing.title)
            return replace(listing, needs_manual_review=True)

        if listing.price > max_price:
            logger.info(
                "Skipping %r because price %s is above max_price %s",
                listing.title,
                listing.price,
                max_price,
            )
            return None

        return listing

    def _apply_frame_size_filter(self, listing: BikeListing) -> BikeListing | None:
        """Keep matching sizes, skip clear mismatches, review unknown sizes."""

        if listing.frame_size is None or listing.frame_size_confidence == "unknown":
            logger.info(
                "Keeping %r for manual review because frame size is unclear",
                listing.title,
            )
            return replace(listing, needs_manual_review=True)

        if not listing.is_relevant:
            logger.info(
                "Skipping %r because frame size %r does not match targets %s",
                listing.title,
                listing.frame_size,
                self.search_config.target_frame_sizes,
            )
            return None

        return listing

    def _apply_category_filter(
        self,
        listing: BikeListing,
        category: str | None,
        subcategory: str | None,
    ) -> BikeListing | None:
        """Keep bicycles and frames, skip accessories and unclear non-bikes."""

        category_text = " ".join(
            value for value in [category, subcategory] if value
        ).casefold()

        if not category_text:
            logger.info(
                "Keeping %r for manual review because category is missing",
                listing.title,
            )
            return replace(listing, needs_manual_review=True)

        # Frames are relevant to the project even when a marketplace groups
        # them near accessories or parts.
        if any(keyword in category_text for keyword in {"frame", "frames", "rahmen"}):
            return listing

        if any(keyword in category_text for keyword in self.EXCLUDED_CATEGORY_KEYWORDS):
            logger.info(
                "Skipping %r because category/subcategory is not a bike: %r",
                listing.title,
                category_text,
            )
            return None

        if any(keyword in category_text for keyword in self.INCLUDED_CATEGORY_KEYWORDS):
            return listing

        logger.info(
            "Keeping %r for manual review because category is unclear: %r",
            listing.title,
            category_text,
        )
        return replace(listing, needs_manual_review=True)

    def _build_page_url(self, page_number: int) -> str:
        """Build a Velomarkt page URL from the configured first-page URL."""

        base_url = self.search_config.velomarkt_search_url
        if page_number == 1:
            return base_url

        parsed_url = urlparse(base_url)
        query = parse_qs(parsed_url.query)
        query["page"] = [str(page_number)]
        return urlunparse(
            parsed_url._replace(query=urlencode(query, doseq=True))
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
