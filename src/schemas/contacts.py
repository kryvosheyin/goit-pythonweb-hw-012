from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing import Optional

from src.database.models import UserRole


class ContactModel(BaseModel):
    """
    Contact model

    Attributes:
        firstname (str): Contact first name
        lastname (str): Contact last name
        birthday (date): Contact birth date
        email (str): Contact email
        phonenumber (str): Contact phone number
        info (str): Contact information
    """

    firstname: str = Field(min_length=2, max_length=50)
    lastname: str = Field(min_length=2, max_length=50)
    birthday: date
    email: EmailStr = Field(min_length=7, max_length=100)
    phonenumber: str = Field(min_length=7, max_length=20)
    info: Optional[str] = None


class ContactResponseModel(ContactModel):
    """
    Contact Response model

    Attributes:
        id (int): Contact ID
        created_at (datetime): Contact creation date
        updated_at (datetime): Contact update date
    """

    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


class User(BaseModel):
    """
    User model

    Attributes:
        id (int): User ID
        username (str): Username
        email (str): User email
        avatar (str): User avatar
        role (UserRole): User role
    """

    id: int
    username: str
    email: str
    avatar: str
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    """
    User Create model

    Attributes:
        username (str): Username
        email (str): User email
        password (str): User password
        role (UserRole): User Role
    """

    username: str
    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
    role: UserRole


class Token(BaseModel):
    """
    Token model

    Attributes:
        access_token (str): Access token
        token_type (str): Token type
    """

    access_token: str
    token_type: str


class RequestEmail(BaseModel):
    """
    Request email model

    Attributes:
        email (str): User email
    """

    email: EmailStr


class UpdatePassword(BaseModel):
    """
    Update password model

    Attributes:
        email (str): User email
        password (str): User password
    """

    email: EmailStr
    password: str = Field(min_length=4, max_length=128)
