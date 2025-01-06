from datetime import datetime, timedelta, timezone
from typing import Optional


import json
from redis.asyncio import Redis
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
from src.schemas.contacts import UserOut
import logging

logger = logging.getLogger(__name__)


class Hash:
    """
    Class for password hashing and verification.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password) -> bool:
        """
        Verifies if a given password matches the hashed_password.

        Args:
            plain_password (str): The password to be checked.
            hashed_password (str): The hashed password to check against.

        Returns:
            bool: True if the password matches the hashed password, False otherwise.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Gets the hashed version of the given password.

        Args:
            password (str): The password to be hashed.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:
    """
    Creates an access token for a given user.

    Args:
        data (dict): A dictionary containing the user's data.
        expires_delta (Optional[int], optional): The time in seconds until the token expires. Defaults to None.

    Returns:
        str: The access token.
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


async def get_redis_client() -> Redis:
    """
    Returns an instance of the Redis client.

    Returns:
        Redis: An instance of the Redis client.
    """
    return Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )


async def get_user_from_db(
    username: str,
    redis: Redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Retrieves a user from Redis cache or the database.

    If the user is found in Redis, it is returned directly.
    If the user is not found in Redis, it is queried from the database.
    If the user is found in the database, it is stored in Redis and returned.
    If the user is not found in the database, None is returned.

    Args:
        username (str): The username of the user to retrieve.

    Returns:
        User: The retrieved user, or None if not found.
    """

    # check the redis first for the user
    user_data = await redis.get(f"user:{username}")
    if user_data:
        logger.info(f"Found user in Redis cache: {username}")
        return User(**json.loads(user_data))

    # if not found in Redis, query the database
    logger.info(f"User not found in Redis cache: {username}. Querying database...")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    # if not found in Redis, query the database
    if user:
        user_data = json.dumps(user.to_dict())
        await redis.set(f"user:{username}", user_data)
        return user

    return None


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis_client),
) -> User:
    """
    Retrieves the current user from the given access token.

    Args:
        token (str): The access token to retrieve the user from.
        db (AsyncSession): The database session dependency.
        redis (Redis): The Redis client dependency.

    Returns:
        User: The current user.

    Raises:
        HTTPException: If the access token is invalid, expired or the user is not found.
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

    user = await get_user_from_db(username, redis, db)

    if user is None:
        raise credentials_exception
    return user


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Retrieves the current user and ensures they are an admin.

    Args:
        current_user (User): The current user, automatically resolved by dependency injection.

    Returns:
        User: The current user if they have an admin role.

    Raises:
        HTTPException: If the current user does not have an admin role.
    """

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=constants.PERMISSION_DENIED)
    return current_user


def create_email_token(data: dict) -> str:
    """
    Creates an email verification token.

    Args:
        data (dict): The data to encode, should contain the user's email address.

    Returns:
        str: The email verification token.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> str:
    """
    Retrieves the email address from a given email verification token.

    Args:
        token (str): The email verification token.

    Returns:
        str: The email address associated with the token.

    Raises:
        HTTPException: If the token is invalid.
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
            detail=constants.INVALID_TOKEN,
        )


async def get_password_from_token(token: str) -> str:
    """
    Retrieves the password from a given token.

    Args:
        token (str): The token containing the password.

    Returns:
        str: The password extracted from the token.

    Raises:
        HTTPException: If the token is invalid.
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
            detail=constants.INVALID_TOKEN,
        )
