"""Configuration loading for Bike Alert.

The application keeps search settings outside the Python code in
`config/search_criteria.toml`. This lets a non-programmer change brands,
locations, or price limits without editing the app itself.
"""

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class SearchConfig:
    """Search settings used by future scraper classes.

    `frozen=True` makes the object read-only after creation. That prevents
    accidental changes while the app is running.
    """

    brands: list[str]
    max_price: int
    frame_size: str
    target_frame_sizes: list[str]
    locations: list[str]
    posted_after: str
    velomarkt_search_url: str
    max_pages: int
    alerts_enabled: bool


def load_search_config(config_path: Path) -> SearchConfig:
    """Load search criteria from a TOML file.

    Args:
        config_path: Path to `search_criteria.toml`.

    Returns:
        A `SearchConfig` object with typed attributes.
    """

    with config_path.open("rb") as file:
        raw_config = tomllib.load(file)

    search_section = raw_config["search"]
    alerts_section = raw_config["alerts"]
    frame_size = search_section["frame_size"]
    target_frame_sizes = search_section.get("target_frame_sizes") or (
        [frame_size] if frame_size else []
    )

    return SearchConfig(
        brands=search_section["brands"],
        max_price=search_section["max_price"],
        frame_size=frame_size,
        target_frame_sizes=target_frame_sizes,
        locations=search_section["locations"],
        posted_after=search_section["posted_after"],
        velomarkt_search_url=search_section["velomarkt_search_url"],
        max_pages=search_section.get("max_pages", 3),
        alerts_enabled=alerts_section["enabled"],
    )
