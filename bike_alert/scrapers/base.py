"""Base scraper architecture for Bike Alert.

Future scraper classes should inherit from `BaseScraper`. This gives every
scraper the same public interface, which makes it easy for the app to run
multiple scrapers in a loop.
"""

from abc import ABC, abstractmethod

from bike_alert.config import SearchConfig
from bike_alert.models import BikeListing


class BaseScraper(ABC):
    """Abstract parent class for all bike listing scrapers.

    An abstract class describes behavior that child classes must provide.
    Here, every scraper must have a `name` and must implement
    `fetch_listings()`.
    """

    def __init__(self, search_config: SearchConfig) -> None:
        self.search_config = search_config

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable scraper name used in logs."""

    @abstractmethod
    def fetch_listings(self) -> list[BikeListing]:
        """Fetch listings from a source.

        Real implementations will eventually:

        1. Read criteria from `self.search_config`.
        2. Request or open marketplace pages.
        3. Parse listing data.
        4. Return a list of `BikeListing` objects.

        This project does not implement those steps yet.
        """
