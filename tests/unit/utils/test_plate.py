import pytest

from app.utils.plate import is_valid_plate, normalize_plate, validate_and_normalize_plate

pytestmark = pytest.mark.unit


def test_normalize_plate_removes_formatting_and_uppercases() -> None:
    assert normalize_plate(" abc-1d23 ") == "ABC1D23"


def test_is_valid_plate_accepts_old_format() -> None:
    assert is_valid_plate("ABC1234") is True


def test_is_valid_plate_accepts_mercosul_format() -> None:
    assert is_valid_plate("ABC1D23") is True


def test_validate_and_normalize_plate_raises_for_invalid_plate() -> None:
    with pytest.raises(ValueError, match="Placa inválida"):
        validate_and_normalize_plate("placa-invalida")
