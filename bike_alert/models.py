"""Shared data models for Bike Alert.

Models describe the shape of the data that moves through the application.
Using one shared model helps the scraper, database, and exporter agree on what
a bike listing looks like.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class BikeListing:
    """A single bike listing found by a scraper.

    Real scraper implementations will create these objects after reading data
    from a website or marketplace.
    """

    title: str
    price: int | None
    location: str | None
    url: str
    source: str
    posted_date: str | None
    brand: str | None = None
    model: str | None = None
    condition: str | None = None
    frame_size: str | None = None
    frame_size_confidence: str = "unknown"
    raw_text: str = ""
    is_relevant: bool = False
    needs_manual_review: bool = True
