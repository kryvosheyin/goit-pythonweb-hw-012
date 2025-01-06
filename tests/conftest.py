import asyncio
import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from unittest.mock import MagicMock

from main import app
from src.database.models import Base, User, Contact
from src.database.db import get_db
from src.schemas.contacts import ContactModel
from src.services.auth import create_access_token, Hash


DB_URL = "sqlite+aiosqlite:///./test.db"


engine = create_async_engine(
    DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)


test_account = {
    "username": "test",
    "email": "test@test.com",
    "password": "testpassword",
    "role": "user",
}

account_info = {
    "username": "username",
    "email": "username@gmail.com",
    "password": "testpassword",
    "role": "user",
}

unique_email_account = {
    "username": "username",
    "email": "username@gmail.com",
    "password": "12345678",
    "role": "user",
}

unique_account_data = {
    "username": "username2",
    "email": "username2@gmail.com",
    "password": "12345678",
    "role": "user",
}


@pytest.fixture
def user():
    """
    Fixture providing a test user.

    Returns:
        User: A User object with the ID 1, username "testuser", and role "user".
    """
    return User(id=1, username="testuser", role="user")


@pytest.fixture
def contact(user: User):
    """
    Fixture providing a test contact.

    Returns:
        Contact: A Contact object with the ID 1, firstname "Alex", lastname "Kryvosheyin",
                 email "alex@test.com", phonenumber "1234567890", birthday "1987-10-24",
                 and the user from the user fixture.
    """

    return Contact(
        id=1,
        firstname="Alex",
        lastname="Kryvosheyin",
        email="alex@test.com",
        phonenumber="1234567890",
        birthday="1987-10-24",
        user=user,
    )


@pytest.fixture
def empty_contact():
    """
    Fixture providing an empty contact.

    Returns:
        None: The empty contact.
    """
    return None


@pytest.fixture
def sample_contact():
    """
    Fixture providing a sample contact model.

    Returns:
        ContactModel: A ContactModel object with the firstname "Alex", lastname "Kryvosheyin",
                      email "alex@test.com", phonenumber "1234567890", and birthday "1987-10-24".
    """
    return ContactModel(
        firstname="Alex",
        lastname="Kryvosheyin",
        email="alex@test.com",
        phonenumber="1234567890",
        birthday="1987-10-24",
    )


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    """
    Initializes the database models for testing.

    This fixture drops all existing tables and then creates them.
    It also creates a test user with the username "test", email "test@test.com", and role "user".
    The fixture will automatically be run before any test that uses the client fixture.
    """

    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_account["password"])
            current_user = User(
                username=test_account["username"],
                email=test_account["email"],
                hashed_password=hash_password,
                is_confirmed=True,
                avatar="https://twitter.com/gravatar.jpg",
                role=test_account["role"],
            )
            session.add(current_user)
            await session.commit()
            await session.refresh(current_user)
            test_account["id"] = current_user.id

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    """
    Client fixture

    This fixture creates a FastAPI TestClient that is used throughout the tests.
    It overrides the get_db dependency to use a TestingSessionLocal and commits/rollbacks
    any changes made to the database during the test.
    """

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)


@pytest.fixture
def auth_headers():
    """
    Fixture for auth headers
    """

    token = "test_token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_upload_file():
    """
    Fixture for mock upload file
    """

    mock = MagicMock()
    mock.file = MagicMock()
    mock.filename = "avatar.png"
    return mock


@pytest.fixture(scope="module")
def event_loop():
    """
    Module-scoped fixture that provides a new asyncio event loop for tests.

    This fixture is used to create and yield a new event loop for asynchronous operations
    in tests. Once the tests are completed, the event loop is closed.

    Yields:
        asyncio.AbstractEventLoop: A newly created asyncio event loop.
    """

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def get_token():
    """
    Fixture that returns a valid JWT token for the test user.

    This fixture uses the test user's data to create a valid JWT token. The token is
    generated using the `create_access_token` function from the `src/services/auth.py`
    module.

    Yields:
        str: A valid JWT token for the test user.

    """
    token = await create_access_token(data={"sub": test_account["username"]})
    return token
