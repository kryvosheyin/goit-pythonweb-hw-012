import pytest
from sqlalchemy import select
from unittest.mock import Mock, AsyncMock

from src.database.models import User
from src.utils import constants
from tests.conftest import TestingSessionLocal

# Updated test data
account_info = {
    "username": "johndoe",
    "email": "johndoe@example.com",
    "password": "strongpassword123",
    "role": "user",
}

unique_email_account = {
    "username": "johndoe",
    "email": "johndoe@example.com",
    "password": "mypassword456",
    "role": "user",
}

unique_account_data = {
    "username": "janedoe",
    "email": "janedoe@example.com",
    "password": "janespassword789",
    "role": "user",
}

# -----------------------------
# AUTH REGISTER TESTS
# -----------------------------


def test_signup(client, monkeypatch):
    """
    Tests the user registration endpoint.

    Asserts that a new user is created with the correct information and that the
    hashed password is not returned in the response.
    """
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == account_info["username"]
    assert data["email"] == account_info["email"]
    assert "hashed_password" not in data
    assert "avatar" in data
    assert data["role"] == account_info["role"]


def test_register_with_existing_email(client, monkeypatch):
    """
    Tests that attempting to register with an existing email address results in
    a 409 status response with the correct error message.
    """
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == constants.USER_EMAIL_ALREADY_EXISTS


def test_register_with_existing_username(client, monkeypatch):
    """
    Tests that attempting to register with an existing username results in a
    409 status response with the correct error message.
    """
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=unique_email_account)
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == constants.USER_EMAIL_ALREADY_EXISTS


def test_register_with_duplicate_email(client, monkeypatch):
    """
    Tests that attempting to register with a duplicate email address results in
    a 409 status response with the correct error message.
    """
    mock = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock)
    response = client.post("api/auth/register", json=account_info)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == constants.USER_EMAIL_ALREADY_EXISTS


# -----------------------------
# AUTH LOGIN TESTS
# -----------------------------


def test_login_with_unconfirmed_account(client):
    """
    Tests that attempting to login with an unconfirmed account results in a
    401 status response with the correct error message.
    """
    response = client.post(
        "api/auth/login",
        data={
            "username": account_info.get("username"),
            "password": account_info.get("password"),
        },
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.USER_NOT_CONFIRMED


@pytest.mark.asyncio
async def test_login(client):
    """
    Tests the login endpoint.

    Asserts that a confirmed user can log in and obtain a valid access token.
    """
    async with TestingSessionLocal() as session:
        user = await session.execute(
            select(User).where(User.email == account_info.get("email"))
        )
        user = user.scalar_one_or_none()
        if user:
            user.is_confirmed = True
            await session.commit()

    response = client.post(
        "api/auth/login",
        data={
            "username": account_info.get("username"),
            "password": account_info.get("password"),
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data


def test_login_with_wrong_password(client):
    """
    Tests that attempting to login with an incorrect password results in a
    401 status response with the correct error message.
    """
    response = client.post(
        "api/auth/login",
        data={"username": account_info.get("username"), "password": "wrongpassword"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.INVALID_CREDENTIALS


def test_login_with_wrong_username(client):
    """
    Tests that attempting to login with an incorrect username results in a
    401 status response with the correct error message.
    """
    response = client.post(
        "api/auth/login",
        data={"username": "invaliduser", "password": account_info.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == constants.INVALID_CREDENTIALS


def test_login_with_validation_error(client):
    """
    Tests that attempting to login without providing a username results
    in a 422 status response, indicating a validation error.
    """

    response = client.post(
        "api/auth/login", data={"password": account_info.get("password")}
    )
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data


# -----------------------------
# EMAIL CONFIRMATION TESTS
# -----------------------------


@pytest.mark.asyncio
async def test_confirm_email(client, monkeypatch):
    """
    Tests the email confirmation process.

    Verifies that a user's email address can be successfully confirmed if the user
    is not already confirmed. Mocks the email extraction from the token and the
    user service to simulate an unconfirmed user and asserts the correct confirmation
    message and status code are returned.
    """

    test_token = "sample_valid_token"

    async_mock = AsyncMock(return_value="johndoe@example.com")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)

    mock = Mock()
    mock.get_user_by_email = AsyncMock(return_value=Mock(is_confirmed=False))
    mock.confirmed_email = AsyncMock(return_value=True)
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)

    # Add necessary headers
    response = client.get(
        f"api/auth/confirmed_email/{test_token}",
        headers={"Authorization": f"Bearer {test_token}"},
    )

    # Assertions
    assert response.status_code == 200
    assert response.json()["message"] == constants.EMAIL_CONFIRMED

    async_mock.assert_called_once_with(test_token)
    mock.get_user_by_email.assert_called_once_with("johndoe@example.com")
    mock.confirmed_email.assert_called_once_with("johndoe@example.com")


@pytest.mark.asyncio
async def test_email_already_confirmed(client, monkeypatch):
    """
    Tests that attempting to confirm an email address that is already confirmed
    results in a 200 status response with the correct confirmation message.
    """
    async_mock = AsyncMock(return_value="johndoe@example.com")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    mock = Mock()
    mock.get_user_by_email = AsyncMock(return_value=Mock(is_confirmed=True))
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/confirmed_email/token")
    assert response.status_code == 200
    assert response.json()["message"] == constants.EMAIL_ALREADY_CONFIRMED
    async_mock.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("johndoe@example.com")
    mock.confirmed_email.assert_not_called()


# -----------------------------
# PASSWORD UPDATE TESTS
# -----------------------------


@pytest.mark.asyncio
async def test_confirm_update_password(client, monkeypatch):
    """
    Test the password update confirmation process.

    This test verifies that the password update confirmation endpoint correctly
    updates a user's password when provided with a valid token. It mocks the
    token decoding process and the user service to simulate a successful password
    update scenario.

    Steps:
    - Mocks the functions to retrieve email and password from a token.
    - Mocks the user service to return a user object when queried by email.
    - Simulates a client request to the password update confirmation endpoint.
    - Asserts that the response status code is 200 and the message indicates
      that the password has been changed.
    - Verifies that the mocked functions are called with the expected arguments.
    """

    async_mock = AsyncMock(return_value="johndoe@example.com")
    mock_from_token = AsyncMock(return_value="new_hashed_password")
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    monkeypatch.setattr("src.services.auth.get_password_from_token", mock_from_token)
    mock = Mock()
    mock.get_user_by_email = AsyncMock(
        return_value=Mock(id=1, email="johndoe@example.com")
    )
    mock.update_password = AsyncMock(return_value=None)
    monkeypatch.setattr("src.services.auth.UserService", lambda db: mock)
    response = client.get("api/auth/update_password/token")
    assert response.status_code == 200
    assert response.json()["message"] == constants.PASSWORD_CHANGED
    async_mock.assert_called_once_with("token")
    mock_from_token.assert_called_once_with("token")
    mock.get_user_by_email.assert_called_once_with("johndoe@example.com")
    mock.update_password.assert_called_once_with(1, "new_hashed_password")


# -----------------------------
# ERROR TEST CASES
# -----------------------------


@pytest.mark.asyncio
async def test_update_password_invalid_or_expired_token(client, monkeypatch):
    """
    Tests the password update confirmation endpoint with an invalid or expired token.

    Verifies that the endpoint correctly returns a 400 status code and the
    appropriate error message when provided with an invalid or expired token.

    Steps:
    - Mocks the functions to retrieve email and password from a token.
    - Simulates a client request to the password update confirmation endpoint.
    - Asserts that the response status code is 400 and the message indicates
      that the token is invalid or expired.
    - Verifies that the mocked functions are called with the expected arguments.
    """
    async_mock = AsyncMock(return_value=None)
    mock_get_password_from_token = AsyncMock(return_value=None)
    monkeypatch.setattr("src.services.auth.get_email_from_token", async_mock)
    monkeypatch.setattr(
        "src.services.auth.get_password_from_token", mock_get_password_from_token
    )
    response = client.get("api/auth/update_password/token")
    assert response.status_code == 400
    assert response.json()["detail"] == constants.INVALID_OR_EXPIRED_TOKEN
