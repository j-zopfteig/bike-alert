"""Application orchestration for Bike Alert.

This module answers the question: "What should happen when the app starts?"
It deliberately avoids detailed database, scraping, and Excel logic. Those
details live in their own modules so each file has one clear responsibility.
"""

import logging
from pathlib import Path

from bike_alert.config import load_search_config
from bike_alert.database import Database
from bike_alert.exporters.excel_exporter import export_listings_to_excel
from bike_alert.scrapers.bike_discount_scraper import BikeDiscountScraper
from bike_alert.scrapers.fake_scraper import FakeScraper


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "search_criteria.toml"
DATABASE_PATH = PROJECT_ROOT / "data" / "bike_alert.sqlite3"
EXPORT_PATH = PROJECT_ROOT / "exports" / "bike_listings.xlsx"


def configure_logging() -> None:
    """Configure readable console logging for the whole application."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def run() -> None:
    """Run the Bike Alert workflow.

    The workflow is intentionally simple:

    1. Load search settings from the configuration file.
    2. Create the SQLite database and required tables if needed.
    3. Run scraper classes.
    4. Save found listings to the database.
    5. Read all stored listings back from SQLite.
    6. Export the stored listings to Excel.

    Real scraping can be added later without changing this high-level shape.
    """

    configure_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Bike Alert")
    logger.info("Loading search criteria from %s", CONFIG_PATH)

    search_config = load_search_config(CONFIG_PATH)
    database = Database(DATABASE_PATH)

    logger.info("Preparing SQLite database at %s", DATABASE_PATH)
    database.initialize()

    # FakeScraper stays useful for predictable local learning data.
    # BikeDiscountScraper is the first real requests + BeautifulSoup scraper.
    scrapers = [
        FakeScraper(search_config=search_config),
        BikeDiscountScraper(search_config=search_config),
    ]

    all_listings = []
    for scraper in scrapers:
        logger.info("Running scraper: %s", scraper.name)
        scraper_listings = scraper.fetch_listings()
        logger.info("%s returned %s listings", scraper.name, len(scraper_listings))
        all_listings.extend(scraper_listings)

    inserted_count = database.save_listings(all_listings)
    stored_listings = database.list_all_listings()

    logger.info("Scraper found %s listings", len(all_listings))
    logger.info("Inserted %s new listings", inserted_count)
    logger.info("Database now contains %s unique listings", len(stored_listings))

    written_export_path = export_listings_to_excel(stored_listings, EXPORT_PATH)

    logger.info("Exported %s listings to %s", len(stored_listings), written_export_path)
    logger.info("Bike Alert finished")
