from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

from src.database.models import UserRole


class ContactModel(BaseModel):
    """
    Contact model
    """

    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    birthday: date
    email: EmailStr = Field(min_length=7, max_length=100)
    phonenumber: str = Field(min_length=7, max_length=20)
    info: Optional[str] = None


class ContactResponseModel(ContactModel):
    """
    Contact response model
    """

    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class MessageResponse(BaseModel):
    """
    Message response model
    """

    message: str


class User(BaseModel):
    """
    User model
    """

    id: int
    username: str
    email: str
    avatar: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    User create model
    """

    username: str
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
    role: UserRole


class UserOut(BaseModel):
    """
    User out model
    """

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
    """
    Token model
    """

    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    """
    Request email model
    """

    email: EmailStr


class UpdatePassword(BaseModel):
    """
    Update password model
    """

    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
