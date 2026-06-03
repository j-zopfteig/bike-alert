# Bike Alert

Beginner-friendly Python 3.14 project structure for a Swiss used-bike listing
alert application.

The project is set up for:

- SQLite storage
- TOML configuration for search criteria
- A scraper architecture with a reusable base class
- A real Velomarkt.ch scraper using `requests` and BeautifulSoup
- Frame-size parsing and relevance flags
- Excel export
- Clear separation between app startup, configuration, database access,
  scraping, and exporting

The project includes a fake scraper with five hardcoded listings for tests and
one real scraper for Velomarkt.ch. Normal application runs use Velomarkt only.
Other Swiss marketplaces are intentionally not added yet.

## Project Structure

```text
bike-alert/
|-- main.py
|-- pyproject.toml
|-- requirements.txt
|-- README.md
|-- config/
|   `-- search_criteria.toml
|-- data/
|   `-- .gitkeep
|-- exports/
|   `-- .gitkeep
`-- bike_alert/
    |-- __init__.py
    |-- app.py
    |-- config.py
    |-- database.py
    |-- models.py
    |-- frame_size.py
    |-- exporters/
    |   |-- __init__.py
    |   `-- excel_exporter.py
    `-- scrapers/
        |-- __init__.py
        |-- base.py
        |-- bike_discount_scraper.py
        |-- example_scraper.py
        |-- fake_scraper.py
        `-- velomarkt_scraper.py
```

## Files Explained

`main.py`
: Starts the application. It imports `run()` from `bike_alert.app` and keeps
the top-level script easy to read.

`pyproject.toml`
: Declares project metadata, Python version, and dependencies. This project
uses Python 3.14 and `openpyxl` for Excel export.

`requirements.txt`
: A simple dependency list for beginners who prefer `pip install -r
requirements.txt`.

`config/search_criteria.toml`
: Human-editable search settings such as bike brands, maximum price, frame
size, target frame sizes, listing locations, and the Velomarkt URL to scrape.

`data/`
: Intended location for the SQLite database file. The `.gitkeep` file keeps
the otherwise-empty folder in Git.

`exports/`
: Intended location for generated Excel files.

`bike_alert/app.py`
: Coordinates the application flow: load config, prepare the database, run
the fake scraper, store unique listings, and export results.

`bike_alert/config.py`
: Reads the TOML configuration file and converts it into Python dataclasses.

`bike_alert/database.py`
: Owns the SQLite connection, table creation logic, duplicate prevention, and
loading stored listings.

`bike_alert/models.py`
: Defines the `BikeListing` dataclass used to pass listing data between the
scraper, database, and exporter layers.

`bike_alert/frame_size.py`
: Extracts frame sizes from listing titles and raw text, then decides whether
the listing matches your configured target frame sizes.

`bike_alert/scrapers/base.py`
: Defines the abstract base scraper class. Future real scrapers should inherit
from this class.

`bike_alert/scrapers/example_scraper.py`
: A placeholder scraper that demonstrates the shape of a scraper without doing
any network requests or parsing.

`bike_alert/scrapers/fake_scraper.py`
: Returns five hardcoded `BikeListing` objects. It behaves like a scraper from
the app's point of view, but it does not scrape websites.

`bike_alert/scrapers/velomarkt_scraper.py`
: Uses `requests` to download one configured Velomarkt.ch page, parses listing
cards with BeautifulSoup, converts them into `BikeListing` objects, and logs
each extracted listing.

`bike_alert/scrapers/bike_discount_scraper.py`
: Legacy retail scraper from an earlier experiment. It is not imported by the
application and is disabled for the Swiss used-bike marketplace workflow.

`bike_alert/exporters/excel_exporter.py`
: Exports bike listings to an `.xlsx` file using `openpyxl`.

## What Happens When You Run It

1. `main.py` calls `bike_alert.app.run()`.
2. `app.py` configures logging so each step is visible in the terminal.
3. `config.py` loads `config/search_criteria.toml`.
4. `database.py` creates `data/bike_alert.sqlite3` and the `bike_listings`
   table if they do not exist yet.
5. `VelomarktScraper` requests one configured Velomarkt.ch search/category URL
   and parses its listing cards with BeautifulSoup.
6. Listings are filtered by configured brands, maximum price, frame size, and
   Velomarkt category before they are stored.
7. `Database.save_listings()` uses a unique `url` column plus SQLite upsert
   logic, so running the app repeatedly does not create duplicate rows and
   existing listings can still receive updated prices.
8. `Database.list_all_listings()` reads the unique stored listings back.
9. `excel_exporter.py` writes those listings to `exports/bike_listings.xlsx`.

## Configure Velomarkt

Edit `config/search_criteria.toml`:

```toml
brands = ["ARC8", "Scott"]
max_price = 1500
frame_size = "L"
target_frame_sizes = ["L"]
locations = []
posted_after = ""
velomarkt_search_url = "https://velomarkt.ch/en/veloboerse/all-switzerland"
max_pages = 10
```

The Velomarkt scraper applies these filters before storing listings:

- `brands`: case-insensitive match against title, visible brand, model, and raw
  text. Listings with no matching brand are skipped.
- `max_price`: listings above this price are skipped. Missing prices are kept
  for manual review.
- `target_frame_sizes`: matching sizes are kept as relevant, clear mismatches
  are skipped, and unknown sizes are kept for manual review.
- `max_pages`: controls Velomarkt pagination. The scraper stops early if a page
  has no listing cards.
- `locations` and `posted_after`: loaded from config but intentionally ignored
  for now.

The scraper also keeps only actual bicycles and frames. Accessories, parts,
clothing, shoes, helmets, components, and spare parts are skipped. Listings
with unclear category information are kept for manual review.

The frame-size parser recognizes examples such as `Size L`, `Grösse L`,
`Rahmen L`, `Rahmengrösse L`, `RH 56`, `Rahmenhöhe 56`, `56 cm`, and `56cm`.

## Install

```powershell
py -3.14 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
python main.py
```

## Tests

```powershell
python -m unittest
```
