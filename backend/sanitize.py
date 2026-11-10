"""Server-side port of frontend/src/lib/sanitize.js. Never trust client-side sanitising alone."""

import math
import re
from typing import Any

_TAGS = re.compile(r"<[^>]*>")
_CONTROL = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")
_DATA_IMAGE = re.compile(r"^data:image/(jpeg|png|webp);base64,")


def clean(value: Any, max_len: int = 2000) -> str:
    text = "" if value is None else str(value)
    text = _TAGS.sub("", text)
    text = _CONTROL.sub("", text)
    return text.strip()[:max_len]


def safe_image(src: Any) -> str:
    """Only allow data URLs we produced ourselves; blocks javascript: and remote tracking URLs."""
    return src if isinstance(src, str) and _DATA_IMAGE.match(src) else ""


def _is_finite_number(v: Any) -> bool:
    # Mirrors JS Number.isFinite: real numbers only (no strings, no booleans).
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def valid_coords(lat: Any, lng: Any) -> bool:
    return _is_finite_number(lat) and _is_finite_number(lng) and abs(lat) <= 90 and abs(lng) <= 180
