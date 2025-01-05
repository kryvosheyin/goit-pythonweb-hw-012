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
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password) -> bool:

        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:

        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def create_access_token(data: dict, expires_delta: Optional[int] = None) -> str:

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
    return Redis(
        host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
    )


async def get_user_from_db(
    username: str,
    redis: Redis = Depends(get_redis_client),
    db: AsyncSession = Depends(get_db),
) -> User:

    # Check Redis cache first
    user_data = await redis.get(f"user:{username}")
    if user_data:
        logger.info(f"Found user in Redis cache: {username}")
        return User(**json.loads(user_data))

    # If not found in Redis, query the database
    logger.info(f"User not found in Redis cache: {username}. Querying database...")
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)

    # If not found in Redis, query the database
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

    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail=constants.PERMISSION_DENIED)
    return current_user


def create_email_token(data: dict) -> str:

    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str) -> str:

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
