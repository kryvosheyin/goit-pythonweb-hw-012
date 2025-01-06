from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.conf.config import settings
from src.services.auth import create_email_token

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(to_email: EmailStr, username: str, host: str) -> None:
    """
    Sends an email to a user to confirm their email address.

    Args:
        to_email: The email address of the user to receive the email.
        username: The username of the user to personalize the email.
        host: The host of the application to link the user to the verification endpoint.
    """
    try:
        token_verification = create_email_token({"sub": to_email})
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[to_email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)


async def send_password_email(
    to_email: EmailStr, username: str, host: str, reset_token: str
) -> None:
    """
    Sends an email to a user to reset their password.

    Args:
        to_email: The email address of the user to receive the email.
        username: The username of the user to personalize the email.
        host: The host of the application to link the user to the verification endpoint.
        reset_token: The token to be used for password reset.

    """

    try:
        reset_link = f"{host}api/auth/confirm_password_reset/{reset_token}"

        message = MessageSchema(
            subject="Password reset requested",
            recipients=[to_email],
            template_body={"reset_link": reset_link, "username": username},
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)
