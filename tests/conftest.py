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
    return User(id=1, username="testuser", role="user")


@pytest.fixture
def contact(user: User):
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
    return None


@pytest.fixture
def sample_contact():
    return ContactModel(
        firstname="Alex",
        lastname="Kryvosheyin",
        email="alex@test.com",
        phonenumber="1234567890",
        birthday="1987-10-24",
    )


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
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
    Auth headers fixture
    """

    token = "test_token"
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_upload_file():
    """
    Mock upload file fixture
    """

    mock = MagicMock()
    mock.file = MagicMock()
    mock.filename = "avatar.png"
    return mock


@pytest.fixture(scope="module")
def event_loop():

    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture()
async def get_token():
    token = await create_access_token(data={"sub": test_account["username"]})
    return token
