import re

PLATE_OLD_PATTERN = re.compile(r"^[A-Z]{3}[0-9]{4}$")
PLATE_MERCOSUL_PATTERN = re.compile(r"^[A-Z]{3}[0-9][A-Z][0-9]{2}$")


def normalize_plate(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9]", "", value.strip()).upper()
    return normalized


def is_valid_plate(value: str) -> bool:
    normalized = normalize_plate(value)
    return bool(
        PLATE_OLD_PATTERN.fullmatch(normalized) or PLATE_MERCOSUL_PATTERN.fullmatch(normalized)
    )


def validate_and_normalize_plate(value: str) -> str:
    normalized = normalize_plate(value)

    if not is_valid_plate(normalized):
        raise ValueError("Placa inválida. Utilize o padrão antigo (AAA1234) ou Mercosul (AAA1A23).")

    return normalized
