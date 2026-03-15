from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.money import quantize_money
from app.utils.plate import validate_and_normalize_plate


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class VehicleSortField(StrEnum):
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    BRAND = "brand"
    YEAR = "year"
    PRICE_USD = "price_usd"


def _clean_required_text(value: str, field_name: str, max_length: int) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo '{field_name}' não pode ser vazio.")
    if len(cleaned) > max_length:
        raise ValueError(f"O campo '{field_name}' deve ter no máximo {max_length} caracteres.")
    return cleaned


def _clean_optional_text(value: str | None, field_name: str, max_length: int) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        raise ValueError(f"O campo '{field_name}' não pode ser vazio.")
    if len(cleaned) > max_length:
        raise ValueError(f"O campo '{field_name}' deve ter no máximo {max_length} caracteres.")
    return cleaned


class VehicleCreate(BaseModel):
    brand: str = Field(..., examples=["Toyota"])
    model: str = Field(..., examples=["Corolla"])
    year: int = Field(..., examples=[2022], ge=1900)
    color: str = Field(..., examples=["Prata"])
    plate: str = Field(..., examples=["ABC1D23"])
    price_brl: Decimal = Field(..., gt=0, max_digits=12, decimal_places=2)

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, value: str) -> str:
        return _clean_required_text(value, "brand", 50)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str) -> str:
        return _clean_required_text(value, "model", 80)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str) -> str:
        return _clean_required_text(value, "color", 30)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int) -> int:
        max_year = datetime.now(UTC).year + 1
        if value > max_year:
            raise ValueError(f"O campo 'year' deve ser menor ou igual a {max_year}.")
        return value

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str) -> str:
        return validate_and_normalize_plate(value)

    @field_validator("price_brl")
    @classmethod
    def validate_price_brl(cls, value: Decimal) -> Decimal:
        return quantize_money(value)


class VehiclePut(VehicleCreate):
    pass


class VehiclePatch(BaseModel):
    brand: str | None = Field(default=None, examples=["Toyota"])
    model: str | None = Field(default=None, examples=["Corolla"])
    year: int | None = Field(default=None, examples=[2022], ge=1900)
    color: str | None = Field(default=None, examples=["Prata"])
    plate: str | None = Field(default=None, examples=["ABC1D23"])
    price_brl: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, value: str | None) -> str | None:
        return _clean_optional_text(value, "brand", 50)

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        return _clean_optional_text(value, "model", 80)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        return _clean_optional_text(value, "color", 30)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int | None) -> int | None:
        if value is None:
            return None
        max_year = datetime.now(UTC).year + 1
        if value > max_year:
            raise ValueError(f"O campo 'year' deve ser menor ou igual a {max_year}.")
        return value

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_and_normalize_plate(value)

    @field_validator("price_brl")
    @classmethod
    def validate_price_brl(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return quantize_money(value)


class VehicleListFilters(BaseModel):
    model_config = ConfigDict(extra="forbid")

    brand: str | None = None
    year: int | None = Field(default=None, ge=1900)
    color: str | None = None
    plate: str | None = None
    min_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    max_price: Decimal | None = Field(default=None, gt=0, max_digits=12, decimal_places=2)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    sort_by: VehicleSortField = VehicleSortField.CREATED_AT
    sort_order: SortOrder = SortOrder.DESC

    @field_validator("brand")
    @classmethod
    def validate_brand(cls, value: str | None) -> str | None:
        return _clean_optional_text(value, "brand", 50)

    @field_validator("color")
    @classmethod
    def validate_color(cls, value: str | None) -> str | None:
        return _clean_optional_text(value, "color", 30)

    @field_validator("plate")
    @classmethod
    def validate_plate(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return validate_and_normalize_plate(value)

    @field_validator("min_price", "max_price")
    @classmethod
    def validate_prices(cls, value: Decimal | None) -> Decimal | None:
        if value is None:
            return None
        return quantize_money(value)

    @field_validator("year")
    @classmethod
    def validate_year(cls, value: int | None) -> int | None:
        if value is None:
            return None
        max_year = datetime.now(UTC).year + 1
        if value > max_year:
            raise ValueError(f"O campo 'year' deve ser menor ou igual a {max_year}.")
        return value


class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    brand: str
    model: str
    year: int
    color: str
    plate: str
    price_usd: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PaginatedVehicleResponse(BaseModel):
    items: list[VehicleResponse]
    page: int
    page_size: int
    total: int
    total_pages: int
    sort_by: VehicleSortField
    sort_order: SortOrder
