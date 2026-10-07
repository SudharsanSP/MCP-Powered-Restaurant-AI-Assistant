from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, EmailStr
from typing import Optional

class LoginRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: EmailStr = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=128)

class RefreshRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: str = Field(..., min_length=32, max_length=256)


class LogoutRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    refresh_token: str = Field(..., min_length=32, max_length=256)


class CustomerLoginResponse(BaseModel):
    access_token: str
    refresh_token: str 
    expires_in: int

class AdminLoginResponse(BaseModel):
    access_token: str
    expires_in: int

class RefreshResponse(BaseModel):
    access_token: str
    expires_in: int


class LogoutResponse(BaseModel):
    message: str
