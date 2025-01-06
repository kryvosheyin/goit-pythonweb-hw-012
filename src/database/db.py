import contextlib

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)

from src.conf.config import settings


class DatabaseSessionManager:
    def __init__(self, url: str):
        """
        Init DB session manager

        Args:
            url (str): Database URL
        """

        self._engine: AsyncEngine | None = create_async_engine(url)
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Context manager for DB session

        Yields:
            AsyncSession: DB session

        Raises:
            Exception: DB session is not initialized
        """

        if self._session_maker is None:
            raise Exception("The DB session has not been initialized.")
        session = self._session_maker()
        try:
            yield session
        except SQLAlchemyError as e:
            await session.rollback()
            raise
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(settings.DB_URL)


async def get_db():
    """
    Get DB session

    Yields:
        AsyncSession: DB session
    """

    async with sessionmanager.session() as session:
        yield session
