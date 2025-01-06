import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactModel


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contact_repository(mock_session):
    return ContactsRepository(mock_session)


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
        phonenumber="0123456789",
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
        phonenumber="0123456789",
        birthday="1987-10-24",
    )


@pytest.mark.asyncio
async def test_fetch_contacts(contact_repository, mock_session, user, contact):
    mock = MagicMock()
    mock.scalars.return_value.all.return_value = [contact]
    mock_session.execute = AsyncMock(return_value=mock)
    all_contacts = await contact_repository.fetch_contacts(
        skip=0,
        limit=10,
        user=user,
        firstname="",
        lastname="",
        email="",
    )
    assert len(all_contacts) == 1
    assert all_contacts[0].firstname == "Alex"


@pytest.mark.asyncio
async def test_get_contact_by_id(contact_repository, mock_session, user, contact):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock)
    contact = await contact_repository.get_contact_by_id(contact_id=1, user=user)
    assert contact is not None
    assert contact.id == 1
    assert contact.firstname == "Alex"


@pytest.mark.asyncio
async def test_create_new_contact_success(
    contact_repository, mock_session, user, sample_contact
):
    result = await contact_repository.create_contact(body=sample_contact, user=user)
    assert isinstance(result, Contact)
    assert result.firstname == "Alex"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_create_new_contact_failed(
    contact_repository, mock_session, user, sample_contact
):
    result = await contact_repository.create_contact(body=sample_contact, user=user)
    assert isinstance(result, Contact)
    assert result.firstname != "Test"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user, contact):
    contact_data = ContactModel(**contact.__dict__)
    contact_data.firstname = "TestName"
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock)
    result = await contact_repository.update_contact(
        contact_id=1, body=contact_data, user=user
    )
    assert result is not None
    assert result.firstname == "TestName"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(contact)


@pytest.mark.asyncio
async def test_delete_contact(contact_repository, mock_session, user, contact):
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock)
    result = await contact_repository.delete_contact(contact_id=1, user=user)
    assert result is not None
    assert result.firstname == "Alex"
    mock_session.delete.assert_awaited_once_with(contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_contact_exists_success(
    contact_repository, mock_session, user, contact
):
    mock = MagicMock()
    mock.scalars.return_value.first.return_value = contact
    mock_session.execute = AsyncMock(return_value=mock)
    is_contact_exist = await contact_repository.is_contact(
        "alex@test.com", "3434343434", user=user
    )
    assert is_contact_exist is True


@pytest.mark.asyncio
async def test_is_contact_exists_failure(
    contact_repository, mock_session, user, empty_contact
):
    mock = MagicMock()
    mock.scalars.return_value.first.return_value = empty_contact
    mock_session.execute = AsyncMock(return_value=mock)
    is_contact_exist = await contact_repository.is_contact(
        "alex@test.com", "3434343434", user=user
    )
    assert is_contact_exist is False
