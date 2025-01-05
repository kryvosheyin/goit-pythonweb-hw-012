from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

from src.database.models import UserRole


class ContactModel(BaseModel):

    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    birthday: date
    email: EmailStr = Field(min_length=7, max_length=100)
    phonenumber: str = Field(min_length=7, max_length=20)
    info: Optional[str] = None


class ContactResponseModel(ContactModel):

    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):

    message: str


class User(BaseModel):

    id: int
    username: str
    email: str
    avatar: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):

    username: str
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
    role: UserRole


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    is_confirmed: bool
    created_at: datetime
    role: UserRole

    class Config:
        from_attributes = True  # Pydantic v2 equivalent of `orm_mode`


class Token(BaseModel):

    access_token: str
    token_type: str


class RequestEmail(BaseModel):

    email: EmailStr


class UpdatePassword(BaseModel):

    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
