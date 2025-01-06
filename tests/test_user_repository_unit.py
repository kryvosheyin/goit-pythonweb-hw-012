import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas.contacts import UserCreate


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repository(mock_session):
    return UserRepository(mock_session)


@pytest.fixture
def user():
    return User(
        id=1,
        username="testuser",
        email="test@test.com",
        avatar="https://test.com/avatar.jpg",
        role="user",
    )


@pytest.fixture
def user_body():
    return UserCreate(
        username="testuser",
        email="test@test.com",
        password="password",
        role="user",
    )


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session, user):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_id(1)
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_username(user_repository, mock_session, user):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_username("testuser")
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, user):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_email("test@test.com")
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session, user, user_body):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    result = await user_repository.create_user(
        user_body,
        avatar="https://test.com/avatar.jpg",
    )
    assert result.email == user.email
    assert result.username == user.username
    assert result.avatar == user.avatar
    assert result.role == user.role
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_confirmed_email(user_repository, mock_session, user):
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user))
    )
    user.is_confirmed = False
    await user_repository.confirmed_email(user.email)
    assert user.is_confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session, user):
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user))
    )
    test_avatar_url = "https://test.com/avatar1.jpg"
    result = await user_repository.update_avatar_url(user.email, test_avatar_url)
    assert result.avatar == test_avatar_url
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_password(user_repository, mock_session, user):
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user))
    )
    test_password = "test_password_hash"
    result = await user_repository.update_password(user.id, test_password)
    assert result.hashed_password == test_password
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_password_user_not_found(user_repository, mock_session):
    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    result = await user_repository.update_password(999, "test_password_hash")
    assert result is None
    mock_session.commit.assert_not_awaited()
