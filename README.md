# Bike Alert

Beginner-friendly Python 3.14 project structure for a future bike listing alert
application.

The project is set up for:

- SQLite storage
- TOML configuration for search criteria
- A scraper architecture with a reusable base class
- Excel export
- Clear separation between app startup, configuration, database access,
  scraping, and exporting

Actual web scraping is intentionally not implemented yet.

## Project Structure

```text
bike-alert/
├── main.py
├── pyproject.toml
├── requirements.txt
├── README.md
├── config/
│   └── search_criteria.toml
├── data/
│   └── .gitkeep
├── exports/
│   └── .gitkeep
└── bike_alert/
    ├── __init__.py
    ├── app.py
    ├── config.py
    ├── database.py
    ├── models.py
    ├── exporters/
    │   ├── __init__.py
    │   └── excel_exporter.py
    └── scrapers/
        ├── __init__.py
        ├── base.py
        └── example_scraper.py
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
placeholder scrapers, and export results.

`bike_alert/config.py`
: Reads the TOML configuration file and converts it into Python dataclasses.

`bike_alert/database.py`
: Owns the SQLite connection and table creation logic.

`bike_alert/models.py`
: Defines the `BikeListing` dataclass used to pass listing data between the
scraper, database, and exporter layers.

`bike_alert/scrapers/base.py`
: Defines the abstract base scraper class. Future real scrapers should inherit
from this class.

`bike_alert/scrapers/example_scraper.py`
: A placeholder scraper that demonstrates the shape of a scraper without doing
any network requests or parsing.

`bike_alert/exporters/excel_exporter.py`
: Exports bike listings to an `.xlsx` file using `openpyxl`.

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
