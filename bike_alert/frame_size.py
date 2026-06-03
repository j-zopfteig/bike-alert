"""Frame-size parsing and relevance decisions.

Marketplace listings are written by humans, so frame sizes can appear in many
forms: "Size L", "Groesse L", "RH 56", "56 cm", and so on. This module keeps
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
    """Extract a likely frame size from free text."""

    normalized_text = _normalize_text(text)

    labeled_patterns = [
        r"\b(?:size|gr\u00f6sse|groesse|rahmen|rahmengr\u00f6sse|rahmengroesse)\s*[:\-]?\s*(XS|S|M|L|XL|SMALL|MEDIUM|LARGE|EXTRA\s+LARGE)\b",
        r"\b(?:rh|rahmenh\u00f6he|rahmenhoehe)\s*[:\-]?\s*(\d{2})\b",
        r"\b(?:size|gr\u00f6sse|groesse|rahmen|rahmengr\u00f6sse|rahmengroesse)\s*[:\-]?\s*(\d{2})\b",
    ]

    for pattern in labeled_patterns:
        match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if match:
            size = normalize_frame_size(match.group(1))
            if _is_supported_size(size):
                return size, "high"

    cm_match = re.search(r"\b(\d{2})\s*cm\b", normalized_text, flags=re.IGNORECASE)
    if cm_match:
        size = normalize_frame_size(cm_match.group(1))
        if _is_supported_size(size):
            return size, "high"

    bare_letter_match = re.search(r"\b(XS|S|M|L|XL)\b", normalized_text)
    if bare_letter_match:
        return normalize_frame_size(bare_letter_match.group(1)), "medium"

    return None, "unknown"


def normalize_frame_size(frame_size: str) -> str:
    """Normalize size text before comparing values."""

    normalized = " ".join(frame_size.strip().upper().replace("CM", "").split())
    long_sizes = {
        "SMALL": "S",
        "MEDIUM": "M",
        "LARGE": "L",
        "EXTRA LARGE": "XL",
    }
    return long_sizes.get(normalized, normalized)


def _normalize_text(text: str) -> str:
    """Collapse whitespace so regex patterns can work across line breaks."""

    return " ".join(text.split())


def _is_supported_size(frame_size: str) -> bool:
    """Return whether a parsed size is in the range this project understands."""

    if frame_size in {"XS", "S", "M", "L", "XL"}:
        return True

    if not frame_size.isdigit():
        return False

    return 44 <= int(frame_size) <= 64
