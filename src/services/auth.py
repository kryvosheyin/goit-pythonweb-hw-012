from datetime import datetime, timedelta, timezone
from typing import Optional

from aiocache import cached
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt

from src.database.models import User, UserRole
from src.database.db import get_db
from src.conf.config import settings
from src.services.users import UserService
from src.utils import constants


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password) -> bool:
        """
        Verify plain password with hashed password

        Args:
            plain_password (str): Plain password
            hashed_password (str): Hashed password

        Returns:
            True if passwords match, False otherwise
        """

        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Get hashed password

        Args:
            password (str): password

        Returns:
            Hashed password
        """

        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Create access token

    Args:
        data (dict): Data
        expires_delta (Optional[int], optional): Expiration time in seconds

    Returns:
        JWT token
    """

    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.JWT_EXPIRATION_SECONDS
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def cache_builder(func, args, kwargs) -> str:
    """
    Cache key builder

    Args:
        func (Callable): Function to cache
        args (Tuple): Function arguments
        kwargs (Dict): Function keyword arguments

    Returns:
        Cache key
    """

    return f"username: {args[0]}"


@cached(ttl=300, key_builder=cache_builder)
async def get_user_from_db(username: str, db: AsyncSession) -> User:
    """
    Get user from database

    Args:
        username (str): Username
        db (AsyncSession): DB session

    Returns:
        User
    """

    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current user

    Args:
        token (str, optional): JWT token
        db (AsyncSession, optional): Database session

    Returns:
        User
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=constants.COULD_NOT_VALIDATE_CREDENTIALS,
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception

    user = await get_user_from_db(username, db)

    if user is None:
        raise credentials_exception
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user

    Args:
        current_user (User, optional): Current user

    Returns:
        User: Admin user object
    """

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=constants.PERMISSION_DENIED)
    return current_user


def create_email_token(data: dict) -> str:
    """
    Create email token

    Args:
        data (dict): Data to encode

    Returns:
        JWT token
    """

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> str:
    """
    Get email from token

    Args:
        token (str): JWT token

    Returns:
        Email

    Raises:
        Wrong token
    """

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.WRONG_TOKEN,
        )


async def get_password_from_token(token: str) -> str:
    """
    Get password from token

    Args:
        token (str): JWT token

    Returns:
        Password

    Raises:
        Wrong token
    """

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        password = payload["password"]
        return password
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=constants.WRONG_TOKEN,
        )
