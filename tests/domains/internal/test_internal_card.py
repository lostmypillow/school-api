import sys
from unittest.mock import MagicMock

import pytest

# Mock pymupdf if not installed
if "pymupdf" not in sys.modules:
    sys.modules["pymupdf"] = MagicMock()

from app.domains.card.router import mm_to_points, generate_a4


def test_mm_to_points():
    """Test _mm_to_points conversion formula."""
    # 25.4 mm == 1 inch == 72 points
    assert pytest.approx(mm_to_points(25.4), 0.001) == 72.0
    assert pytest.approx(mm_to_points(0), 0.001) == 0.0
    assert pytest.approx(mm_to_points(12.7), 0.001) == 36.0


def test_generate_a4_too_many_cards_error():
    """Test generate_a4 raises ValueError when more than 10 cards are passed."""
    with pytest.raises(ValueError) as exc_info:
        generate_a4([b"mock_card_bytes"] * 11)

    assert "This template only supports up to 10 cards per A4 sheet." in str(
        exc_info.value
    )
