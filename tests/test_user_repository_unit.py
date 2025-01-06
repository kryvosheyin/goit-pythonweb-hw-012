import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, MagicMock

from src.database.models import User
from src.repository.users import UserRepository
from src.schemas.contacts import UserCreate


@pytest.fixture
def mock_session():
    """
    Fixture for creating a mock AsyncSession object

    This fixture provides a mock of the AsyncSession object that is used
    in the UserRepository class. It is used in unit tests to provide
    a way to mock the database operations.

    Returns:
        AsyncMock: Mock AsyncSession object
    """
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repository(mock_session):
    """
    Fixture for creating a UserRepository instance

    This fixture provides an instance of the UserRepository
    class using a mocked AsyncSession object. It is used in unit tests
    to perform operations related to user management without interacting
    with an actual database.

    Args:
        mock_session (AsyncMock): A mocked AsyncSession instance.

    Returns:
        UserRepository: An instance of the UserRepository class.
    """

    return UserRepository(mock_session)


@pytest.fixture
def user():
    """
    Fixture for creating a User instance

    This fixture provides an instance of the User class which is used in unit tests
    to perform operations related to user management without interacting with an actual
    database.

    Returns:
        User: An instance of the User class.
    """
    return User(
        id=1,
        username="testuser",
        email="test@test.com",
        avatar="https://test.com/avatar.jpg",
        role="user",
    )


@pytest.fixture
def user_body():
    """
    Fixture for creating a UserCreate instance

    This fixture provides an instance of the UserCreate class which is used in unit tests
    to perform operations related to user management without interacting with an actual
    database.

    Returns:
        UserCreate: An instance of the UserCreate class.
    """
    return UserCreate(
        username="testuser",
        email="test@test.com",
        password="password",
        role="user",
    )


@pytest.mark.asyncio
async def test_get_user_by_id(user_repository, mock_session, user):
    """
    Unit test for fetching a user by ID from the database.

    Verifies that the `get_user_by_id` method of the `UserRepository`
    class returns a user matching the given user ID.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_id(1)
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_username(user_repository, mock_session, user):
    """
    Unit test for fetching a user by username from the database.

    Verifies that the `get_user_by_username` method of the `UserRepository`
    class returns a user matching the given username.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """

    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_username("testuser")
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repository, mock_session, user):
    """
    Unit test for fetching a user by email from the database.

    Verifies that the `get_user_by_email` method of the `UserRepository`
    class returns a user matching the given email address.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """

    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    mock_session.execute = AsyncMock(return_value=mock)
    result = await user_repository.get_user_by_email("test@test.com")
    assert result == user
    mock_session.execute.assert_called_once()
    mock_session.execute.return_value.scalar_one_or_none.assert_called_once()


@pytest.mark.asyncio
async def test_create_user(user_repository, mock_session, user, user_body):
    """
    Unit test for creating a new user in the database.

    Verifies that the `create_user` method of the `UserRepository`
    class creates a new user with the given user data and
    persists it in the database.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.
        user_body (UserCreate): The sample user data used for testing.

    Returns:
        None
    """
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
    """
    Unit test for confirming a user's email in the database.

    Verifies that the `confirmed_email` method of the `UserRepository`
    class correctly updates the `is_confirmed` attribute of a user to `True`
    when provided with a valid email address, and ensures that the session
    commit is called to persist the change.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """

    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=user))
    )
    user.is_confirmed = False
    await user_repository.confirmed_email(user.email)
    assert user.is_confirmed is True
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_avatar_url(user_repository, mock_session, user):
    """
    Unit test for updating a user's avatar URL in the database.

    Verifies that the `update_avatar_url` method of the `UserRepository`
    class correctly updates the `avatar` attribute of a user to the given
    URL, and ensures that the session commit is called to persist the
    change.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """
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
    """
    Unit test for updating a user's password in the database.

    Verifies that the `update_password` method of the `UserRepository`
    class correctly updates the `hashed_password` attribute of a user to the given
    hash, and ensures that the session commit is called to persist the
    change.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The sample user data used for testing.

    Returns:
        None
    """
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
    """
    Unit test for updating a user's password when the user is not found.

    Verifies that the `update_password` method of the `UserRepository`
    class returns `None` and does not attempt to commit the transaction
    when trying to update the password of a non-existent user.

    Args:
        user_repository (UserRepository): The instance of the `UserRepository`
            class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.

    Returns:
        None
    """

    mock_session.execute = AsyncMock(
        return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
    )
    result = await user_repository.update_password(999, "test_password_hash")
    assert result is None
    mock_session.commit.assert_not_awaited()
