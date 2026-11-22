"""Skema Pydantic untuk validasi request dan response."""
from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    password: str = Field(min_length=5, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str
    email: str | None = None
    role: str = ""
    is_active: bool = True
    theme: str = "light"
    font_scale: str = "normal"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=60)
    full_name: str = Field(min_length=3, max_length=120)
    email: str | None = None
    password: str = Field(min_length=6, max_length=128)
    role: Literal["admin", "petugas"] = "petugas"


class UserUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    role: Literal["admin", "petugas"] | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=6, max_length=128)


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6, max_length=128)


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    email: str | None = None
    theme: Literal["light", "dark", "auto"] | None = None
    font_scale: Literal["small", "normal", "large"] | None = None


class MedicineBase(BaseModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=2, max_length=150)
    category: str = "Umum"
    unit: str = "Strip"
    price: float = Field(ge=0)
    min_stock: int = Field(default=0, ge=0)
    safety_stock: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=7, ge=0, le=365)
    purchase_unit: str = "Strip"
    is_priority: bool = False


class MedicineCreate(MedicineBase):
    system_stock: int = Field(default=0, ge=0)
    physical_stock: int = Field(default=0, ge=0)


class MedicineUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    category: str | None = None
    unit: str | None = None
    price: float | None = Field(default=None, ge=0)
    min_stock: int | None = Field(default=None, ge=0)
    safety_stock: int | None = Field(default=None, ge=0)
    lead_time_days: int | None = Field(default=None, ge=0, le=365)
    purchase_unit: str | None = None
    is_priority: bool | None = None
    is_active: bool | None = None


class MedicineOut(MedicineBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_demo: bool = False
    is_active: bool = True
    system_stock: int = 0
    physical_stock: int = 0
    stock_status: str = "aman"


class SaleCreate(BaseModel):
    transaction_code: str = Field(default="", max_length=50)
    sale_date: date
    medicine_id: int
    quantity: int = Field(gt=0, le=1_000_000)
    unit_price: float = Field(ge=0)

    @field_validator("sale_date")
    @classmethod
    def valid_date(cls, value: date) -> date:
        if value.year < 2000 or value.year > 2100:
            raise ValueError("Tanggal tidak valid (tahun harus 2000-2100).")
        return value


class SaleUpdate(BaseModel):
    sale_date: date | None = None
    medicine_id: int | None = None
    quantity: int | None = Field(default=None, gt=0, le=1_000_000)
    unit_price: float | None = Field(default=None, ge=0)


class SaleOut(BaseModel):
    id: int
    transaction_code: str
    sale_date: date
    medicine_id: int
    medicine_name: str
    quantity: int
    unit_price: float
    total_price: float
    is_demo: bool = False


class WeatherCreate(BaseModel):
    weather_date: date
    temperature: float = Field(ge=-10, le=60)
    rainfall: float = Field(ge=0, le=1000)
    humidity: float = Field(ge=0, le=100)


class WeatherUpdate(BaseModel):
    temperature: float | None = Field(default=None, ge=-10, le=60)
    rainfall: float | None = Field(default=None, ge=0, le=1000)
    humidity: float | None = Field(default=None, ge=0, le=100)


class WeatherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    weather_date: date
    temperature: float
    rainfall: float
    humidity: float
    source: str
    is_demo: bool


class StockAdjustment(BaseModel):
    system_stock: int | None = Field(default=None, ge=0)
    physical_stock: int | None = Field(default=None, ge=0)
    change_type: Literal["opname", "penambahan", "pengurangan", "koreksi"] = "koreksi"
    note: str = Field(min_length=3, max_length=300)
    last_opname_date: date | None = None


class PredictionRequest(BaseModel):
    medicine_id: int
    horizon_weeks: Literal[1, 2, 4, 8, 12] = 4
    start_date: date | None = None
    model_name: Literal["auto", "random_forest", "decision_tree", "linear_regression"] = "auto"
    save: bool = True


class ImportPreviewRequest(BaseModel):
    import_type: Literal["sales", "weather", "medicines", "inventory"]
    rows: list[dict]
    file_name: str = "upload.csv"


class ImportCommitRequest(ImportPreviewRequest):
    mapping: dict[str, str]
    skip_duplicates: bool = True


class SettingUpdate(BaseModel):
    value: str


class ModelSettings(BaseModel):
    primary_model: Literal["auto", "random_forest", "decision_tree", "linear_regression"] = "auto"
    n_estimators: int = Field(default=400, ge=10, le=1500)
    max_depth: int = Field(default=4, ge=0, le=100)
    min_samples_leaf: int = Field(default=3, ge=1, le=50)
    random_state: int = Field(default=42, ge=0, le=1_000_000)
    test_ratio: float = Field(default=0.2, ge=0.1, le=0.4)
    horizon_weeks: int = Field(default=4, ge=1, le=12)
    weather_scenario: str = "normal_iklim"
    n_jobs: int = -1


class ProcurementSettings(BaseModel):
    lead_time_days: int = Field(default=7, ge=0, le=365)
    safety_stock_days: int = Field(default=14, ge=0, le=365)
    review_period_days: int = Field(default=7, ge=1, le=365)
    rounding_unit: int = Field(default=1, ge=1, le=1000)
    default_horizon_weeks: int = Field(default=4, ge=1, le=12)


class ProcurementEditItem(BaseModel):
    final_qty: int = Field(ge=0, le=1_000_000)
    reason: str = Field(min_length=3, max_length=400)


class ProcurementCreate(BaseModel):
    period_weeks: int = Field(default=4, ge=1, le=12)
    notes: str | None = None
