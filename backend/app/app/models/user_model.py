from app.models.base_uuid_model import BaseUUIDModel
from app.schemas.common_schema import IGenderEnum
from datetime import datetime
from sqlmodel import BigInteger, Field, SQLModel, Relationship, Column, DateTime, String
from typing import Optional
from sqlalchemy_utils import ChoiceType
from pydantic import EmailStr
from uuid import UUID


class UserBase(SQLModel):
    first_name: str
    last_name: str
    email: EmailStr = Field(
        nullable=True, index=True, sa_column_kwargs={"unique": True}
    )
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    birthdate: datetime | None = Field(
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )  # birthday with timezone
    phone: str | None
    gender: IGenderEnum | None = Field(
        default=IGenderEnum.other,
        sa_column=Column(ChoiceType(IGenderEnum, impl=String())),
    )
    state: str | None
    country: str | None
    address: str | None


class User(BaseUUIDModel, UserBase, table=True):
    hashed_password: str | None = Field(nullable=False, index=True)