from fastapi import APIRouter, Depends, Request, UploadFile, File
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf.config import settings
from src.database.db import get_db
from src.schemas.contacts import User
from src.services.auth import get_current_user, get_current_admin_user
from src.services.upload_file import UploadFileService
from src.services.users import UserService


router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=User,
    description="Too many requests! Plrease try again later.",
)
@limiter.limit("10 per minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """
    Get the current user.

    Rate limit: 10 requests per minute.

    Returns:
        User: The current user.
    """
    return user


@router.patch("/avatar", response_model=User, summary="Update User avatar")
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update user avatar.

    This endpoint updates the user avatar.

    Args:
        file (UploadFile): The file to be uploaded.

    Returns:
        User: The user with the updated avatar.
    """
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
