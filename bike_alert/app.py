"""Application orchestration for Bike Alert.

This module answers the question: "What should happen when the app starts?"
It deliberately avoids detailed database, scraping, and Excel logic. Those
details live in their own modules so each file has one clear responsibility.
"""

from pathlib import Path

from bike_alert.config import load_search_config
from bike_alert.database import Database
from bike_alert.exporters.excel_exporter import export_listings_to_excel
from bike_alert.scrapers.example_scraper import ExampleScraper


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "search_criteria.toml"
DATABASE_PATH = PROJECT_ROOT / "data" / "bike_alert.sqlite3"
EXPORT_PATH = PROJECT_ROOT / "exports" / "bike_listings.xlsx"


def run() -> None:
    """Run the Bike Alert workflow.

    The workflow is intentionally simple at this stage:

    1. Load search settings from the configuration file.
    2. Create the SQLite database and required tables if needed.
    3. Run placeholder scraper classes.
    4. Save the empty result set to the database.
    5. Export the result set to Excel.

    Real scraping can be added later without changing this high-level shape.
    """

    print("Starting Bike Alert...")

    search_config = load_search_config(CONFIG_PATH)
    database = Database(DATABASE_PATH)
    database.initialize()

    # This scraper is only a teaching example. It returns an empty list and
    # performs no web requests.
    scrapers = [
        ExampleScraper(search_config=search_config),
    ]

    all_listings = []
    for scraper in scrapers:
        print(f"Running scraper: {scraper.name}")
        all_listings.extend(scraper.fetch_listings())

    database.save_listings(all_listings)
    export_listings_to_excel(all_listings, EXPORT_PATH)

    print(f"Saved {len(all_listings)} listings to {DATABASE_PATH}")
    print(f"Exported Excel file to {EXPORT_PATH}")
