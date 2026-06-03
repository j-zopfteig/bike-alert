"""SQLite database access for Bike Alert.

SQLite is a good beginner database because it stores everything in one local
file and Python includes SQLite support in the standard library.
"""

from pathlib import Path
import logging
import sqlite3

from bike_alert.models import BikeListing


logger = logging.getLogger(__name__)


class Database:
    """Small wrapper around an SQLite database file.

    Wrapping database behavior in a class keeps SQL details out of the rest of
    the application. Other modules can call clear methods such as
    `initialize()` and `save_listings()` without knowing the SQL statements.
    """

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def connect(self) -> sqlite3.Connection:
        """Create and return a database connection."""

        # Ensure the `data/` folder exists before SQLite tries to create the
        # database file inside it.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)

        # Row objects let us access columns by name, for example row["title"].
        # This is easier to read than remembering numeric positions.
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create required database tables if they do not already exist."""

        with self.connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS bike_listings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    price INTEGER,
                    location TEXT,
                    url TEXT UNIQUE,
                    source TEXT NOT NULL,
                    posted_date TEXT
                )
                """
            )
        logger.info("Database table is ready")

    def save_listings(self, listings: list[BikeListing]) -> int:
        """Save bike listings to SQLite.

        `INSERT OR IGNORE` prevents duplicate rows when a listing has the same
        URL as one already stored in the database.

        Returns:
            The number of new rows inserted.
        """

        if not listings:
            logger.info("No listings to save")
            return 0

        rows = [
            (
                listing.title,
                listing.price,
                listing.location,
                listing.url,
                listing.source,
                listing.posted_date,
            )
            for listing in listings
        ]

        with self.connect() as connection:
            before_count = connection.total_changes
            connection.executemany(
                """
                INSERT OR IGNORE INTO bike_listings (
                    title,
                    price,
                    location,
                    url,
                    source,
                    posted_date
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            inserted_count = connection.total_changes - before_count

        logger.info(
            "Saved listings to SQLite: %s new, %s ignored as duplicates",
            inserted_count,
            len(listings) - inserted_count,
        )
        return inserted_count

    def list_all_listings(self) -> list[BikeListing]:
        """Load all unique bike listings currently stored in SQLite."""

        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT title, price, location, url, source, posted_date
                FROM bike_listings
                ORDER BY id
                """
            ).fetchall()

        return [
            BikeListing(
                title=row["title"],
                price=row["price"],
                location=row["location"],
                url=row["url"],
                source=row["source"],
                posted_date=row["posted_date"],
            )
            for row in rows
        ]
