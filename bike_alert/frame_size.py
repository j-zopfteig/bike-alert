"""Frame-size parsing and relevance decisions.

Marketplace listings are written by humans, so frame sizes can appear in many
forms: "Size L", "Grösse L", "RH 56", "56 cm", and so on. This module keeps
that parsing logic in one place so every scraper can use the same rules.
"""

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class FrameSizeResult:
    """Result of parsing frame size text."""

    frame_size: str | None
    confidence: str
    is_relevant: bool
    needs_manual_review: bool


def evaluate_frame_size(
    title: str,
    raw_text: str,
    target_frame_sizes: list[str],
) -> FrameSizeResult:
    """Parse a frame size and compare it with configured target sizes."""

    parsed_size, confidence = parse_frame_size(f"{title}\n{raw_text}")
    normalized_targets = {normalize_frame_size(size) for size in target_frame_sizes}

    if parsed_size is None:
        return FrameSizeResult(
            frame_size=None,
            confidence="unknown",
            is_relevant=False,
            needs_manual_review=True,
        )

    is_relevant = parsed_size in normalized_targets
    return FrameSizeResult(
        frame_size=parsed_size,
        confidence=confidence,
        is_relevant=is_relevant,
        needs_manual_review=False,
    )


def parse_frame_size(text: str) -> tuple[str | None, str]:
    """Extract a likely frame size from free text.

    Returns:
        A tuple of `(frame_size, confidence)`. The size is normalized to values
        such as `"L"` or `"56"`.
    """

    normalized_text = _normalize_text(text)

    # Strong patterns: the text explicitly says the nearby value is a frame
    # size. These are the clearest matches and should win over generic tokens.
    labeled_patterns = [
        r"\b(?:size|grösse|groesse|rahmen|rahmengrösse|rahmengroesse)\s*[:\-]?\s*(XS|S|M|L|XL)\b",
        r"\b(?:rh|rahmenhöhe|rahmenhoehe)\s*[:\-]?\s*(\d{2})\b",
        r"\b(?:size|grösse|groesse|rahmen|rahmengrösse|rahmengroesse)\s*[:\-]?\s*(\d{2})\b",
    ]

    for pattern in labeled_patterns:
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if match:
            size = normalize_frame_size(match.group(1))
            if _is_supported_size(size):
                return size, "high"

    # Numeric road-bike sizes are commonly written as "56 cm" or "56cm".
    cm_match = re.search(r"\b(\d{2})\s*cm\b", normalized_text, flags=re.IGNORECASE)
    if cm_match:
        size = normalize_frame_size(cm_match.group(1))
        if _is_supported_size(size):
            return size, "high"

    # Bare letter sizes are useful in titles like "Wilier ... M" or
    # "Cube ... L". This is less explicit than "Grösse L", but still practical
    # for listing titles.
    bare_letter_match = re.search(r"\b(XS|S|M|L|XL)\b", normalized_text)
    if bare_letter_match:
        return normalize_frame_size(bare_letter_match.group(1)), "medium"

    return None, "unknown"


def normalize_frame_size(frame_size: str) -> str:
    """Normalize size text before comparing values."""

    return frame_size.strip().upper().replace("CM", "")


def _normalize_text(text: str) -> str:
    """Collapse whitespace so regex patterns can work across line breaks."""

    return " ".join(text.split())


def _is_supported_size(frame_size: str) -> bool:
    """Return whether a parsed size is in the range this project understands."""

    if frame_size in {"XS", "S", "M", "L", "XL"}:
        return True

    if not frame_size.isdigit():
        return False

    # Road bike frame sizes usually sit roughly in this range. The guard avoids
    # confusing rider height values like "180 cm" with frame sizes.
    return 44 <= int(frame_size) <= 64
