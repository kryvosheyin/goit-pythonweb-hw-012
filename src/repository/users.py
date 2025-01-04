from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.schemas.contacts import UserCreate
from src.database.models import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        """
        Init UserRepository

        Args:
            session (AsyncSession): An AsyncSession object connected to the database
        """

        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Fetch user by ID

        Args:
            user_id (int): user ID

        Returns:
            User
        """

        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Fetch user by username

        Args:
            username (str): username

        Returns:
            User
        """

        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Fetch user by email

        Args:
            email (str): user email

        Returns:
            User
        """

        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """
        Create user

        Args:
            body (UserCreate): UserCreate
            avatar (str, optional): user avatar URL

        Returns:
            User
        """

        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Confirmation email

        Args:
            email (str): Email for confirmation

        Returns:
            None.
        """
        user = await self.get_user_by_email(email)
        user.is_confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Update user avatar URL

        Args:
            email (str): user email
            url (str): url

        Returns:
            User with updated avatar URL
        """

        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(self, user_id: int, password: str):
        """
        Update user password

        Args:
            user_id (int): User ID
            password (str): User password

        Returns:
            User with the updated password
        """

        user = await self.get_user_by_id(user_id)
        if user:
            user.hashed_password = password
            await self.db.commit()
            await self.db.refresh(user)

        return user
