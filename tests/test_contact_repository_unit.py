import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Contact, User
from src.repository.contacts import ContactsRepository
from src.schemas.contacts import ContactModel


@pytest.fixture
def mock_session():
    """
    Mock AsyncSession object fixture

    This fixture provides a mock of the AsyncSession object that is used
    in the ContactsRepository class. It is used in unit tests to provide
    a way to mock the database operations.

    Returns:
        AsyncMock: Mock AsyncSession object
    """
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contact_repository(mock_session):
    """
    Fixture for creating a ContactsRepository instance

    This fixture provides an instance of the ContactsRepository
    class using a mocked AsyncSession object. It is used in unit tests
    to perform operations related to contact management without interacting
    with an actual database.

    Args:
        mock_session (AsyncMock): A mocked AsyncSession instance.

    Returns:
        ContactsRepository: An instance of the ContactsRepository class.
    """

    return ContactsRepository(mock_session)


@pytest.fixture
def user():
    """
    Fixture for creating a User instance

    This fixture provides an instance of the User class which is used
    in unit tests to perform operations related to user management
    without interacting with an actual database.

    Returns:
        User: An instance of the User class.
    """
    return User(id=1, username="testuser", role="user")


@pytest.fixture
def contact(user: User):
    """
    Fixture for creating a Contact instance

    This fixture provides an instance of the Contact class which is used
    in unit tests to perform operations related to contact management
    without interacting with an actual database.

    Args:
        user (User): An instance of the User class.

    Returns:
        Contact: An instance of the Contact class.
    """
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
    """
    Fixture for creating an empty Contact instance

    This fixture provides None as the value for the empty Contact instance
    which is used in unit tests to perform operations related to contact
    management without interacting with an actual database.

    Returns:
        None: The empty value for the Contact instance.
    """
    return None


@pytest.fixture
def sample_contact():
    """
    Fixture for creating a sample ContactModel instance

    This fixture provides a prepopulated ContactModel instance which is used
    in unit tests to perform operations related to contact management without
    interacting with an actual database.

    Returns:
        ContactModel: A prepopulated ContactModel instance.
    """
    return ContactModel(
        firstname="Alex",
        lastname="Kryvosheyin",
        email="alex@test.com",
        phonenumber="0123456789",
        birthday="1987-10-24",
    )


@pytest.mark.asyncio
async def test_fetch_contacts(contact_repository, mock_session, user, contact):
    """
    Unit test for fetching contacts from the database.

    Verifies that the `fetch_contacts` method of the `ContactsRepository` class
    returns a list of contacts matching the given filters.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user whose contacts are to be fetched.
        contact (ContactModel): The sample contact used for testing.

    Returns:
        None

    """
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
    """
    Unit test for fetching a contact by ID from the database.

    Verifies that the `get_contact_by_id` method of the `ContactsRepository`
    class returns a contact matching the given contact ID.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user whose contact is to be fetched.
        contact (ContactModel): The sample contact used for testing.

    Returns:
        None
    """
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
    """
    Unit test for successfully creating a new contact in the database.

    Verifies that the `create_contact` method of the `ContactsRepository`
    class correctly creates a new contact and persists it in the database.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is creating the contact.
        sample_contact (ContactModel): The sample contact data used for testing.

    Returns:
        None
    """

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
    """
    Unit test for handling failure when creating a new contact in the database.

    Verifies that the `create_contact` method of the `ContactsRepository`
    class does not create a contact with unexpected data and ensures that
    the session methods are called appropriately.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is attempting to create the contact.
        sample_contact (ContactModel): The sample contact data used for testing.

    Returns:
        None
    """

    result = await contact_repository.create_contact(body=sample_contact, user=user)
    assert isinstance(result, Contact)
    assert result.firstname != "Test"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_contact(contact_repository, mock_session, user, contact):
    """
    Unit test for updating a contact in the database.

    Verifies that the `update_contact` method of the `ContactsRepository`
    class correctly updates a contact with the given contact ID and
    persists it in the database.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is updating the contact.
        contact (Contact): The sample contact data used for testing.

    Returns:
        None
    """
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
    """
    Unit test for deleting a contact in the database.

    Verifies that the `delete_contact` method of the `ContactsRepository`
    class correctly deletes a contact with the given contact ID and
    persists it in the database.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is deleting the contact.
        contact (Contact): The sample contact data used for testing.

    Returns:
        None
    """
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
    """
    Unit test for checking if a contact exists in the database.

    Verifies that the `is_contact` method of the `ContactsRepository` class
    correctly checks if a contact with the given contact email and phone
    number exists in the database.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is checking if the contact exists.
        contact (Contact): The sample contact data used for testing.

    Returns:
        None
    """

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
    """
    Unit test for checking if a contact exists in the database.

    Verifies that the `is_contact` method of the `ContactsRepository` class
    correctly checks if a contact with the given contact email and phone
    number exists in the database.

    Args:
        contact_repository (ContactsRepository): The instance of the
            `ContactsRepository` class being tested.
        mock_session (AsyncSession): The mocked `AsyncSession` instance used
            for testing database operations.
        user (User): The user who is checking if the contact exists.
        empty_contact (Contact): The empty contact data used for testing.

    Returns:
        None
    """
    mock = MagicMock()
    mock.scalars.return_value.first.return_value = empty_contact
    mock_session.execute = AsyncMock(return_value=mock)
    is_contact_exist = await contact_repository.is_contact(
        "alex@test.com", "3434343434", user=user
    )
    assert is_contact_exist is False
