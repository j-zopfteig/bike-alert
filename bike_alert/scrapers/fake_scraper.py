"""Fake scraper that returns hardcoded bike listings.

This scraper is useful while learning because it behaves like a real scraper
from the rest of the app's point of view, but it does not visit any websites.
That means the database and Excel export can be developed safely before adding
network requests, HTML parsing, or browser automation.
"""

import logging

from bike_alert.models import BikeListing
from bike_alert.scrapers.base import BaseScraper


logger = logging.getLogger(__name__)


class FakeScraper(BaseScraper):
    """Scraper implementation that returns five fixed listings."""

    @property
    def name(self) -> str:
        """Return the display name for logs."""

        return "FakeScraper"

    def fetch_listings(self) -> list[BikeListing]:
        """Return fake listings without doing any real scraping."""

        logger.info(
            "Creating fake listings using configured brands: %s",
            ", ".join(self.search_config.brands),
        )

        # The URL is the duplicate key in the SQLite table. If the same fake
        # listing is saved twice, SQLite ignores the second copy because the URL
        # already exists.
        return [
            BikeListing(
                title="Cube Nuroad Pro Gravel Bike",
                price=1200,
                location="Zurich",
                url="https://example.com/bikes/cube-nuroad-pro",
                source=self.name,
                posted_date="2026-05-28",
            ),
            BikeListing(
                title="Trek Domane AL 3 Road Bike",
                price=1450,
                location="Winterthur",
                url="https://example.com/bikes/trek-domane-al-3",
                source=self.name,
                posted_date="2026-05-29",
            ),
            BikeListing(
                title="Specialized Sirrus X 4.0",
                price=980,
                location="Zurich",
                url="https://example.com/bikes/specialized-sirrus-x-4",
                source=self.name,
                posted_date="2026-05-30",
            ),
            BikeListing(
                title="Cannondale Topstone Alloy",
                price=1350,
                location="Uster",
                url="https://example.com/bikes/cannondale-topstone-alloy",
                source=self.name,
                posted_date="2026-05-31",
            ),
            BikeListing(
                title="Scott Speedster 20 Disc",
                price=1100,
                location="Zurich",
                url="https://example.com/bikes/scott-speedster-20-disc",
                source=self.name,
                posted_date="2026-06-01",
            ),
        ]
