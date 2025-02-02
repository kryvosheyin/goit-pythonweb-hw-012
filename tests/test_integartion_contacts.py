import pytest

from fastapi import HTTPException, status
from unittest.mock import AsyncMock, MagicMock

from src.schemas.contacts import ContactModel
from src.utils import constants

account_info = {
    "id": 1,
    "username": "john_doe",
    "email": "john.doe@example.com",
    "password": "strongpass123",
    "role": "user",
    "is_confirmed": True,
}

contacts = [
    {
        "id": 1,
        "firstname": "Alice",
        "lastname": "Smith",
        "birthday": "1988-04-22",
        "email": "alice.smith@example.com",
        "phonenumber": "5551234567",
        "created_at": "2024-01-01T10:00:00",
        "updated_at": "2024-01-01T10:00:00",
        "info": "Colleague from work",
    },
    {
        "id": 2,
        "firstname": "Bob",
        "lastname": "Johnson",
        "birthday": "1995-11-10",
        "email": "bob.johnson@example.com",
        "phonenumber": "5559876543",
        "created_at": "2024-01-02T11:30:00",
        "updated_at": "2024-01-02T11:30:00",
        "info": "Neighbor",
    },
]

payload = {
    "firstname": "Alice",
    "lastname": "Smith",
    "birthday": "1988-04-22",
    "email": "alice.smith@example.com",
    "phonenumber": "5551234567",
}


@pytest.mark.asyncio
async def test_fetch_upcoming_birthdays(client, monkeypatch, auth_headers):
    """
    Tests that the "/birthdays" endpoint returns a list of contacts with upcoming birthdays.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 200 and that the response body is a list of contacts.
    Asserts that the first contact in the list has the correct name.
    Asserts that the service function was called with the correct parameters.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    async_mock = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", async_mock)
    mock_birthdays = AsyncMock(return_value=contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_upcoming_birthdays",
        mock_birthdays,
    )
    response = client.get("/api/contacts/birthdays?days=7", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(contacts)
    assert response.json()[0]["firstname"] == contacts[0]["firstname"]
    mock_birthdays.assert_called_once_with(7, account_info)


@pytest.mark.asyncio
async def test_fetch_upcoming_birthdays_unauthenticated(client, monkeypatch):
    """
    Tests that the "/birthdays" endpoint returns a 401 status code and a "Not authenticated" message
    when the request is not authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a dictionary with a "detail"
    key containing the string "Not authenticated".
    """

    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    response = client.get("/api/contacts/birthdays?days=7")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_fetch_contacts_without_filters(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts" endpoint returns a list of all contacts when no filters are applied.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 200 and that the response body is a list of contacts.
    Asserts that the first contact in the list has the correct email.
    Asserts that the service function was called with the correct parameters.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    async_mock = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", async_mock)
    mock_contacts = AsyncMock(return_value=contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )
    response = client.get("/api/contacts/", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == len(contacts)
    assert response.json()[0]["email"] == contacts[0]["email"]
    mock_contacts.assert_called_once_with(
        firstname="", lastname="", email="", skip=0, limit=100, user=account_info
    )


@pytest.mark.asyncio
async def test_fetch_contacts_with_filters(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts" endpoint returns the filtered list of contacts
    when firstname and lastname filters are applied.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 200 and that the response body contains
    the contact matching the filters.
    Asserts that the service function was called with the correct filter parameters.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)

    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)

    mock_contacts = AsyncMock(return_value=[contacts[0]])  # Return a list
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )

    response = client.get(
        "/api/contacts/?firstname=Alice&lastname=Smith", headers=auth_headers
    )

    # Assertions
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["firstname"] == "Alice"
    assert response.json()[0]["lastname"] == "Smith"

    # Adjust assertion to match keyword arguments
    mock_contacts.assert_called_once_with(
        firstname="Alice",
        lastname="Smith",
        email="",
        skip=0,
        limit=100,
        user=account_info,
    )


@pytest.mark.asyncio
async def test_fetch_contacts_pagination(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts" endpoint returns a paginated list of contacts
    when skip and limit query parameters are applied.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 200 and that the response body
    contains the paginated contact.
    Asserts that the service function was called with the correct
    pagination parameters.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)

    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)

    paginated_contacts = [
        {
            "id": 3,
            "firstname": "Johny",
            "lastname": "Depp",
            "email": "johnie.depp@example.com",
            "phonenumber": "5556677889",
            "birthday": "1991-09-09",
            "created_at": "2024-01-03T14:00:00",
            "updated_at": "2024-01-03T14:00:00",
        }
    ]
    mock_contacts = AsyncMock(return_value=paginated_contacts)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contacts", mock_contacts
    )

    response = client.get("/api/contacts/?skip=2&limit=1", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 3
    assert response.json()[0]["firstname"] == "Johny"
    assert response.json()[0]["lastname"] == "Depp"

    mock_contacts.assert_called_once_with(
        firstname="",
        lastname="",
        email="",
        skip=2,
        limit=1,
        user=account_info,
    )


@pytest.mark.asyncio
async def test_fetch_contacts_unauthenticated(client, monkeypatch):
    """
    Tests that the "/contacts" endpoint returns a 401 status code and a "Not authenticated" message
    when the request is not authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a dictionary with a "detail"
    key containing the string "Not authenticated".
    """
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    response = client.get("/api/contacts/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_fetch_contact(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns the correct contact details.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact retrieval by ID to return a specific contact.
    Asserts that the response status is 200 and that the returned contact details
    match the expected contact data.
    Asserts that the service function was called with the correct contact ID and user details.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)

    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)

    contact = contacts[0]
    mock_contact = AsyncMock(return_value=contact)  # Return a dictionary
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contact_by_id", mock_contact
    )

    response = client.get("/api/contacts/1", headers=auth_headers)
    assert response.status_code == 200

    # Assertions
    assert response.json()["id"] == contact["id"]
    assert response.json()["firstname"] == contact["firstname"]

    mock_contact.assert_called_once_with(1, account_info)


@pytest.mark.asyncio
async def test_fetch_contact_not_found(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 404 status code
    and a "Contact not found" message when the contact ID is not found in the
    database.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact retrieval by ID to return None.
    Asserts that the response status is 404 and that the response body is a
    dictionary with a "detail" key containing the string "Contact not found".
    Asserts that the service function was called with the correct contact ID and
    user details.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    mock_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.fetch_contact_by_id", mock_contact
    )
    response = client.get("/api/contacts/999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_contact.assert_called_once_with(999, account_info)


@pytest.mark.asyncio
async def test_fetch_contact_unauthenticated(client, monkeypatch):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 401 status code
    and a "Not authenticated" message when the request is not authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a
    dictionary with a "detail" key containing the string "Not authenticated".
    """
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    response = client.get("/api/contacts/1")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_create_new_contact(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/" endpoint creates a new contact and returns a 201
    status code and the newly created contact in the response body.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact creation to return the first contact in the contacts list.
    Asserts that the response status is 201 and that the response body is a
    dictionary with the correct contact details.
    Asserts that the service function was called with the correct parameters.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    contact = contacts[0]
    mock_create_contact = AsyncMock(return_value=contact)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.create_new_contact",
        mock_create_contact,
    )
    response = client.post("/api/contacts/", json=payload, headers=auth_headers)
    contact_model = ContactModel(**payload)
    assert response.status_code == 201
    assert response.json()["id"] == contact["id"]
    assert response.json()["firstname"] == contact["firstname"]
    mock_create_contact.assert_called_once_with(contact_model, account_info)


@pytest.mark.asyncio
async def test_create_contact_with_incorrect_data(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/" endpoint returns a 422 status code and a
    dictionary with a "detail" key when attempting to create a new contact
    with incorrect data.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 422 and that the response body is a
    dictionary with the "detail" key.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    incorrect_payload = {
        "firstname": "",
    }
    response = client.post(
        "/api/contacts/", json=incorrect_payload, headers=auth_headers
    )
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_create_new_contact_unauthenticated(client, monkeypatch):
    """
    Tests that the "/contacts/" endpoint returns a 401 status code and a "Not authenticated" message
    when attempting to create a new contact without being authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a dictionary with a "detail"
    key containing the string "Not authenticated".
    """
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    response = client.post("/api/contacts/", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_update_contact(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint updates a contact and returns a 200
    status code and the updated contact in the response body.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact update to return the updated contact.
    Asserts that the response status is 200 and that the returned contact details
    match the expected contact data.
    Asserts that the service function was called with the correct contact ID,
    updated contact model and user details.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    updated_contact = {
        **contacts[0],
        "firstname": "NewTest",
        "lastname": "NewTest",
    }
    mock_update_contact = AsyncMock(return_value=updated_contact)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.update_exist_contact",
        mock_update_contact,
    )
    payload = {
        "firstname": "NewTest",
        "lastname": "NewTest",
        "birthday": "1987-10-24",
        "email": "alex@test.com",
        "phonenumber": "0123456789",
    }
    contact_id = contacts[0]["id"]
    response = client.put(
        f"/api/contacts/{contact_id}", json=payload, headers=auth_headers
    )
    contact_model = ContactModel(**payload)
    assert response.status_code == 200
    assert response.json()["id"] == updated_contact["id"]
    assert response.json()["firstname"] == updated_contact["firstname"]
    assert response.json()["lastname"] == updated_contact["lastname"]
    mock_update_contact.assert_called_once_with(contact_id, contact_model, account_info)


@pytest.mark.asyncio
async def test_update_contact_not_found(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 404 status code and a "Contact not found" message
    when attempting to update a contact that does not exist.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact update to return None.
    Asserts that the response status is 404 and that the response body is a dictionary with a "detail"
    key containing the string "Contact not found".
    Asserts that the service function was called with the correct contact ID, updated contact model and user details.
    """
    mock_jwt_decode = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt_decode)
    mock_get_user_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_get_user_from_db)
    mock_update_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.update_exist_contact",
        mock_update_contact,
    )
    payload = {
        "firstname": "tt",
        "lastname": "hh",
        "birthday": "1991-08-24",
        "email": "incorrect@example.com",
        "phonenumber": "0123456789",
    }
    response = client.put("/api/contacts/999", json=payload, headers=auth_headers)
    contact_model = ContactModel(**payload)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_update_contact.assert_called_once_with(999, contact_model, account_info)


@pytest.mark.asyncio
async def test_update_contact_with_incorrect_data(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 422 status code and a dictionary with a "detail"
    key when attempting to update a contact with incorrect data.

    Mocks the JWT decoding and the user retrieval from the database.
    Asserts that the response status is 422 and that the response body is a dictionary with a "detail" key.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    invalid_payload = {
        "firstname": "",
    }
    response = client.put("/api/contacts/1", json=invalid_payload, headers=auth_headers)
    assert response.status_code == 422
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_update_contact_unauthenticated(client, monkeypatch):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 401 status code and a "Not authenticated" message
    when attempting to update a contact without being authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a dictionary with a "detail" key
    containing the string "Not authenticated".
    """
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    response = client.put("/api/contacts/1", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_delete_contact(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint deletes a contact and returns a 200
    status code and a dictionary with a "message" key containing a success message.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact deletion to return a dictionary with a "message" key.
    Asserts that the response status is 200 and that the returned message matches the expected message.
    Asserts that the service function was called with the correct contact ID and user details.
    """
    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)

    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)

    contact_id = contacts[0]["id"]
    expected_response = {
        "message": f"Contact with ID {contact_id} successfully deleted."
    }

    mock_delete_contact = AsyncMock(return_value=expected_response)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.delete_contact",
        mock_delete_contact,
    )

    response = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)

    # Assertions
    assert response.status_code == 200
    assert response.json() == expected_response
    mock_delete_contact.assert_called_once_with(contact_id, account_info)


@pytest.mark.asyncio
async def test_delete_contact_not_found(client, monkeypatch, auth_headers):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 404 status code
    and a "Contact not found" message when attempting to delete a contact that
    does not exist.

    Mocks the JWT decoding and the user retrieval from the database.
    Mocks the contact deletion to return None.
    Asserts that the response status is 404 and that the response body is a
    dictionary with a "detail" key containing the string "Contact not found".
    Asserts that the service function was called with the correct contact ID and
    user details.
    """

    mock_jwt = MagicMock(return_value={"sub": account_info["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)
    mock_from_db = AsyncMock(return_value=account_info)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)
    mock_delete_contact = AsyncMock(return_value=None)
    monkeypatch.setattr(
        "src.services.contacts.ContactService.delete_contact",
        mock_delete_contact,
    )
    contact_id = 999
    response = client.delete(f"/api/contacts/{contact_id}", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == constants.CONTACT_NOT_FOUND
    mock_delete_contact.assert_called_once_with(contact_id, account_info)


@pytest.mark.asyncio
async def test_delete_contact_unauthenticated(client, monkeypatch):
    """
    Tests that the "/contacts/{contact_id}" endpoint returns a 401 status code
    and a "Not authenticated" message when attempting to delete a contact without
    being authenticated.

    Mocks the JWT decoding to raise an exception.
    Asserts that the response status is 401 and that the response body is a
    dictionary with a "detail" key containing the string "Not authenticated".
    """
    mock = AsyncMock(
        side_effect=HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=constants.UNAUTHORIZED,
        )
    )
    monkeypatch.setattr("src.services.auth.get_current_user", mock)
    contact_id = contacts[0]["id"]
    response = client.delete(f"/api/contacts/{contact_id}")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
