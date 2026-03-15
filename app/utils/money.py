from decimal import ROUND_HALF_UP, Decimal

MONEY_QUANTIZER = Decimal("0.01")
EXCHANGE_RATE_QUANTIZER = Decimal("0.0001")


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTIZER, rounding=ROUND_HALF_UP)


def quantize_exchange_rate(value: Decimal) -> Decimal:
    return value.quantize(EXCHANGE_RATE_QUANTIZER, rounding=ROUND_HALF_UP)
