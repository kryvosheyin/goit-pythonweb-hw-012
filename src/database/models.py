from datetime import datetime, date
from enum import Enum
from sqlalchemy import Integer, String, func, Column, ForeignKey, Enum as AEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Boolean, Date, DateTime


class Base(DeclarativeBase):
    """
    Base model
    """

    pass


class Contact(Base):
    """
    Contact model

    Inherits Base (DeclarativeBase): Base model from declarative base SQLAlchemy

    Attributes:
        id (int): Contact ID
        firstname (str): Contact first name
        lastname (str): Contact last name
        birthday (date): Contact birthdate
        email (str): Contact email
        phonenumber (str): Contact phone number
        info (str): Contact information
        created_at (datetime): Time creation contact
        updated_at (datetime): Time updated contact
        user_id (int): The foreign key referencing the user who owns the contact
        user (User): Contact user
    """

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str] = mapped_column(String(50), nullable=False)
    lastname: Mapped[str] = mapped_column(String(50), nullable=False)
    birthday: Mapped[date] = mapped_column("birthday", Date, nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    phonenumber: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    info: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        "created_at", DateTime, default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        "updated_at", DateTime, default=func.now(), onupdate=func.now()
    )
    user_id = Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    user = relationship("User", backref="contacts")


class UserRole(str, Enum):
    """
    Enum for User roles
    """

    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    User model

    Inherits Base (DeclarativeBase): Base model from declarative base SQLAlchemy

    Attributes:
        id (int): User ID
        username (str): User username
        email (str): User email
        hashed_password (str): User hashed password
        avatar (str): User avatar
        is_confirmed (bool): Whether the user has confirmed their email
        created_at (datetime): Time user creation
        role (UserRole): User role
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    avatar = Column(String(255), nullable=True)
    is_confirmed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    role = Column(AEnum(UserRole), default=UserRole.USER, nullable=False)
