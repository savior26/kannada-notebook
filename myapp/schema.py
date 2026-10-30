from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from myapp.utils.time import to_india_time


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=8)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    created_at: datetime

    @field_validator("created_at", mode="before")
    @classmethod
    def serialize_created_at_in_india_time(cls, value: datetime) -> datetime:
        return to_india_time(value)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=4, max_length=8)
