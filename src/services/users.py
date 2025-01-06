from libgravatar import Gravatar
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas.contacts import UserCreate


class UserService:
    def __init__(self, db: AsyncSession):
        """
        Init UserService class

        Args:
            db: SQLAlchemy DB session.
        """

        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate) -> User:
        """
        Create user

        Args:
            body: data

        Returns:
            User

        Raises:
            ValueError
        """

        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Fetch user by ID

        Args:
            user_id: user ID

        Returns:
            User
        """

        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Fetch user by username

        Args:
            username (str): username

        Returns:
            User
        """

        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Fetch user by email

         Args:
             email (str): user email

         Returns:
             User
        """

        return await self.repository.get_user_by_email(email)

    async def confirmed_email(self, email: str) -> None:
        """
        Confirmation email

        Args:
            email (str): email to confirm.

        Returns:
            None
        """

        return await self.repository.confirmed_email(email)

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update user avatar URL

        Args:
            email (str): user email
            url (str): avatar URL

        Returns:
            User
        """

        return await self.repository.update_avatar_url(email, url)

    async def update_password(self, user_id: int, password: str) -> User:
        """
        Update user password

        Args:
            user_id (int): user ID
            password (str): user password

        Returns:
            User
        """

        return await self.repository.update_password(user_id, password)
