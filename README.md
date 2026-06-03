# Bike Alert

Beginner-friendly Python 3.14 project structure for a future bike listing alert
application.

The project is set up for:

- SQLite storage
- TOML configuration for search criteria
- A scraper architecture with a reusable base class
- A real scraper using `requests` and BeautifulSoup
- Excel export
- Clear separation between app startup, configuration, database access,
  scraping, and exporting

The app includes both a fake scraper with five hardcoded listings and a real
scraper for one public bike listing page.

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
    |-- exporters/
    |   |-- __init__.py
    |   `-- excel_exporter.py
    `-- scrapers/
        |-- __init__.py
        |-- base.py
        |-- bike_discount_scraper.py
        |-- example_scraper.py
        `-- fake_scraper.py
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
size, and listing locations.

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

`bike_alert/scrapers/base.py`
: Defines the abstract base scraper class. Future real scrapers should inherit
from this class.

`bike_alert/scrapers/example_scraper.py`
: A placeholder scraper that demonstrates the shape of a scraper without doing
any network requests or parsing.

`bike_alert/scrapers/fake_scraper.py`
: Returns five hardcoded `BikeListing` objects. It behaves like a scraper from
the app's point of view, but it does not scrape websites.

`bike_alert/scrapers/bike_discount_scraper.py`
: Uses `requests` to download Bike-Discount's public bike category page, parses
the HTML with BeautifulSoup, converts product cards into `BikeListing` objects,
and logs each extracted listing.

`bike_alert/exporters/excel_exporter.py`
: Exports bike listings to an `.xlsx` file using `openpyxl`.

## What Happens When You Run It

1. `main.py` calls `bike_alert.app.run()`.
2. `app.py` configures logging so each step is visible in the terminal.
3. `config.py` loads `config/search_criteria.toml`.
4. `database.py` creates `data/bike_alert.sqlite3` and the `bike_listings`
   table if they do not exist yet.
5. `FakeScraper` returns five hardcoded listings.
6. `BikeDiscountScraper` requests one public bike listing page and parses its
   product cards with BeautifulSoup.
7. `Database.save_listings()` uses a unique `url` column plus SQLite upsert
   logic, so running the app repeatedly does not create duplicate rows and
   existing listings can still receive updated prices.
8. `Database.list_all_listings()` reads the unique stored listings back.
9. `excel_exporter.py` writes those listings to `exports/bike_listings.xlsx`.

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
