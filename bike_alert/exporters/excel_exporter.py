"""Excel export for Bike Alert listings.

The exporter receives plain `BikeListing` objects and writes them to an Excel
workbook. It does not know how scraping works and it does not know how the
database works.
"""

from pathlib import Path
from datetime import datetime
import logging

from openpyxl import Workbook

from bike_alert.models import BikeListing


logger = logging.getLogger(__name__)


def export_listings_to_excel(listings: list[BikeListing], export_path: Path) -> Path:
    """Export bike listings to an `.xlsx` file.

    Args:
        listings: Bike listings to export.
        export_path: Destination path for the Excel file.

    Returns:
        The path that was actually written. This is usually `export_path`, but
        if Excel has that file open on Windows, the exporter writes a
        timestamped copy instead.
    """

    export_path.parent.mkdir(parents=True, exist_ok=True)

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Bike Listings"

    headers = ["Title", "Price", "Location", "URL", "Source", "Posted Date"]
    sheet.append(headers)

    for listing in listings:
        sheet.append(
            [
                listing.title,
                listing.price,
                listing.location,
                listing.url,
                listing.source,
                listing.posted_date,
            ]
        )

    # Make the first row stand out a little. This is optional, but it makes the
    # exported file easier to scan when opened in Excel.
    for cell in sheet[1]:
        cell.style = "Headline 4"

    try:
        workbook.save(export_path)
        logger.info("Excel export written to %s", export_path)
        return export_path
    except PermissionError:
        fallback_path = _build_fallback_export_path(export_path)
        workbook.save(fallback_path)
        logger.warning(
            "Could not overwrite %s, so Excel export was written to %s",
            export_path,
            fallback_path,
        )
        return fallback_path


def _build_fallback_export_path(export_path: Path) -> Path:
    """Create a unique export path for cases where the normal file is locked."""

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return export_path.with_name(f"{export_path.stem}_{timestamp}{export_path.suffix}")
