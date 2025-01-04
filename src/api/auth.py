from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas.contacts import RequestEmail, Token, UpdatePassword, UserCreate, User
from src.services.email import send_email, send_password_email
from src.services.auth import (
    create_access_token,
    Hash,
    get_email_from_token,
    get_password_from_token,
)
from src.services.users import UserService
from src.utils import constants


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=User,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    User registration
    """

    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=constants.USER_EMAIL_ALREADY_EXISTS,
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=constants.USER_NAME_ALREADY_EXISTS,
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )

    return new_user


@router.post("/login", response_model=Token, summary="User login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    User authentication
    """

    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.INVALID_CREDENTIALS,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.USER_NOT_CONFIRMED,
        )

    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}", summary="Email confirmation")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    User email confirmation
    """

    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.is_confirmed:
        return {"message": "Your email has already been confirmed."}
    await user_service.confirmed_email(email)
    return {"message": "Your email has been confirmed."}


@router.post("/request_email", summary="Request email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request user email confirmation
    """

    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user and user.is_confirmed:
        return {"message": constants.EMAIL_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": constants.CHECK_YOUR_EMAIL}


@router.post("/update_password", summary="Update password")
async def update_password_request(
    body: UpdatePassword,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Request update user password
    """

    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if not user:
        return {"message": "Check your email for confirmation letter."}

    if not user.is_confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email is not confirmed."
        )
    password = Hash().get_password_hash(body.password)
    reset_token = await create_access_token(
        data={"sub": user.email, "password": password}
    )
    background_tasks.add_task(
        send_password_email,
        to_email=body.email,
        username=user.username,
        host=str(request.base_url),
        reset_token=reset_token,
    )
    return {"message": "Check your email for confirmation letter."}


@router.get("/confirm_update_password/{token}", summary="Password confirmation")
async def confirm_update_password(token: str, db: AsyncSession = Depends(get_db)):
    """
    Confirmation update user password
    """

    email = await get_email_from_token(token)
    password = await get_password_from_token(token)

    if not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token."
        )

    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect email."
        )
    await user_service.update_password(user.id, password)
    return {"message": "Password is updated."}
