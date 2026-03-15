from decimal import Decimal

import pytest

from app.utils.money import quantize_exchange_rate, quantize_money

pytestmark = pytest.mark.unit


def test_quantize_money_uses_two_decimal_places() -> None:
    assert quantize_money(Decimal("10.005")) == Decimal("10.01")


def test_quantize_exchange_rate_uses_four_decimal_places() -> None:
    assert quantize_exchange_rate(Decimal("5.73465")) == Decimal("5.7347")
