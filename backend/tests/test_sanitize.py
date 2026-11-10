import math

import pytest

from sanitize import clean, safe_image, valid_coords


def test_clean_strips_tags_control_chars_and_whitespace():
    # Like the JS version, only the tags go; text between them stays (React escapes it on render).
    assert clean("  <b>Здравей</b>\x00\x07 свят<script>alert(1)</script>  ") == "Здравей святalert(1)"


def test_clean_keeps_newlines_and_tabs():
    assert clean("ред 1\nред 2\tкрай") == "ред 1\nред 2\tкрай"


def test_clean_truncates_after_trimming():
    assert clean("   abcdef", 3) == "abc"


def test_clean_handles_none_and_non_strings():
    assert clean(None) == ""
    assert clean(42) == "42"


def test_clean_default_max_is_2000():
    assert len(clean("x" * 5000)) == 2000


@pytest.mark.parametrize(
    "src",
    ["data:image/jpeg;base64,AAA", "data:image/png;base64,AAA", "data:image/webp;base64,AAA"],
)
def test_safe_image_allows_own_data_urls(src):
    assert safe_image(src) == src


@pytest.mark.parametrize(
    "src",
    [
        "javascript:alert(1)",
        "https://tracker.example/pixel.png",
        "data:image/gif;base64,AAA",
        "data:image/svg+xml;base64,AAA",
        "data:text/html;base64,AAA",
        None,
        123,
    ],
)
def test_safe_image_rejects_everything_else(src):
    assert safe_image(src) == ""


@pytest.mark.parametrize(
    ("lat", "lng"),
    [(0, 0), (42.2, 23.3), (90, 180), (-90, -180)],
)
def test_valid_coords_accepts_numbers_in_range(lat, lng):
    assert valid_coords(lat, lng)


@pytest.mark.parametrize(
    ("lat", "lng"),
    [(91, 0), (0, 181), (-90.1, 0), ("42", 23), (42, None), (True, 1), (math.nan, 0), (math.inf, 0)],
)
def test_valid_coords_rejects_invalid(lat, lng):
    assert not valid_coords(lat, lng)
