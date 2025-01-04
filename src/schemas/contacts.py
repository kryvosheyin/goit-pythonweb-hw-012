from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional


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


class User(BaseModel):
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    email: EmailStr