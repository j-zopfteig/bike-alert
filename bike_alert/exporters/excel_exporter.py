"""Excel export for Bike Alert listings.

The exporter receives plain `BikeListing` objects and writes them to an Excel
workbook. It does not know how scraping works and it does not know how the
database works.
"""

from pathlib import Path

from openpyxl import Workbook

from bike_alert.models import BikeListing


def export_listings_to_excel(listings: list[BikeListing], export_path: Path) -> None:
    """Export bike listings to an `.xlsx` file.

    Args:
        listings: Bike listings to export.
        export_path: Destination path for the Excel file.
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

    workbook.save(export_path)
