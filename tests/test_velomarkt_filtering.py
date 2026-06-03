"""Tests for Velomarkt filtering rules."""

import unittest

from bike_alert.config import SearchConfig
from bike_alert.models import BikeListing
from bike_alert.scrapers.velomarkt_scraper import VelomarktScraper


class VelomarktFilteringTests(unittest.TestCase):
    """Focused tests for the scraper filtering decisions."""

    def setUp(self) -> None:
        self.scraper = VelomarktScraper(
            search_config=SearchConfig(
                brands=["ARC8", "Scott"],
                max_price=1500,
                frame_size="L",
                target_frame_sizes=["L"],
                locations=[],
                posted_after="",
                velomarkt_search_url="https://velomarkt.ch/en/veloboerse/all-switzerland",
                max_pages=3,
                alerts_enabled=False,
            )
        )

    def test_brand_filtering_skips_unmatched_brands(self) -> None:
        listing = self._listing(
            brand="Cube",
            model="Nuroad",
            title="Cube Nuroad L",
            raw_text="Cube Nuroad. Frame size: L.",
        )

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNone(result)

    def test_brand_filtering_matches_case_insensitively(self) -> None:
        listing = self._listing(brand="scott", title="SCOTT Addict Gravel L")

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNotNone(result)

    def test_max_price_filtering_skips_expensive_listings(self) -> None:
        listing = self._listing(price=2000)

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNone(result)

    def test_missing_price_keeps_listing_for_manual_review(self) -> None:
        listing = self._listing(price=None)

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNotNone(result)
        self.assertTrue(result.needs_manual_review)

    def test_frame_size_filtering_skips_clear_mismatches(self) -> None:
        listing = self._listing(
            frame_size="M",
            frame_size_confidence="high",
            is_relevant=False,
            needs_manual_review=False,
        )

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNone(result)

    def test_unknown_frame_size_keeps_listing_for_manual_review(self) -> None:
        listing = self._listing(
            frame_size=None,
            frame_size_confidence="unknown",
            is_relevant=False,
            needs_manual_review=True,
        )

        result = self.scraper._apply_filters(
            listing=listing,
            category="Racing bikes",
            subcategory="Cyclo-cross / Cross / Gravel",
        )

        self.assertIsNotNone(result)
        self.assertFalse(result.is_relevant)
        self.assertTrue(result.needs_manual_review)

    def test_excluded_categories_are_skipped(self) -> None:
        listing = self._listing(title="Scott Helmet Size L", raw_text="Scott helmet")

        result = self.scraper._apply_filters(
            listing=listing,
            category="Accessories-Parts",
            subcategory="Helmets",
        )

        self.assertIsNone(result)

    def _listing(
        self,
        title: str = "Scott Addict Gravel L",
        price: int | None = 1000,
        brand: str | None = "Scott",
        model: str | None = "Addict Gravel",
        frame_size: str | None = "L",
        frame_size_confidence: str = "high",
        raw_text: str = "Scott Addict Gravel. Frame size: L.",
        is_relevant: bool = True,
        needs_manual_review: bool = False,
    ) -> BikeListing:
        return BikeListing(
            title=title,
            price=price,
            location="8000 Zurich",
            url=f"https://example.com/{title.casefold().replace(' ', '-')}",
            source="Velomarkt.ch",
            posted_date=None,
            brand=brand,
            model=model,
            condition="Second hand",
            frame_size=frame_size,
            frame_size_confidence=frame_size_confidence,
            raw_text=raw_text,
            is_relevant=is_relevant,
            needs_manual_review=needs_manual_review,
        )


if __name__ == "__main__":
    unittest.main()
