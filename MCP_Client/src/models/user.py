from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=2, max_length=100)
    phone_number: str = Field(..., min_length=10, max_length=10)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator("phone_number")
    @classmethod
    def validate_phone_number(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("Phone number must contain exactly 10 digits")
        return value


class UserCreateResponse(BaseModel):
    customer_uuid: str
    access_token: str
    refresh_token: str
    expires_in: int
    