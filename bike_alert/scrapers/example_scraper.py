"""Placeholder scraper used to demonstrate the architecture.

This file intentionally performs no scraping. It exists so beginners can see
what a future scraper class will look like.
"""

from bike_alert.models import BikeListing
from bike_alert.scrapers.base import BaseScraper


class ExampleScraper(BaseScraper):
    """Example scraper that returns no listings yet."""

    @property
    def name(self) -> str:
        """Return the display name for this scraper."""

        return "ExampleScraper"

    def fetch_listings(self) -> list[BikeListing]:
        """Return an empty list until real scraping is implemented."""

        # No network request, HTML parsing, browser automation, or real scraping
        # belongs here yet. Later, this method is the place to add it.
        return []
