from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


def validate_ru_phone_digits(value: str) -> str:
    v = value.strip()
    if not v.isdigit():
        raise ValueError("phone должен содержать только цифры")
    if len(v) < 10 or len(v) > 11:
        raise ValueError("phone должен содержать 10 или 11 цифр")
    return v


class BuildingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    address: str
    latitude: float
    longitude: float


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: int | None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    building: BuildingOut
    phones: list[str]
    activities: list[ActivityOut]


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1, max_length=300)
    building_id: int
    phones: list[str] = Field(default_factory=list)
    activity_ids: list[int] = Field(default_factory=list)

    @field_validator("phones")
    @classmethod
    def _validate_phones(cls, values: list[str]) -> list[str]:
        return [validate_ru_phone_digits(v) for v in values]