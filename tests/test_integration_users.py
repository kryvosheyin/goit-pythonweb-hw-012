import pytest
from fastapi import HTTPException, status
from unittest import mock
from unittest.mock import AsyncMock, MagicMock

from src.utils import constants


admin_user = {
    "id": 1,
    "username": "super_admin",
    "email": "super_admin@example.com",
    "password": "securepass123",
    "role": "admin",
    "is_confirmed": True,
    "avatar": "https://example.com/avatar.png",
}

regular_user = {
    "id": 202,
    "username": "john_doe",
    "email": "johndoe@example.com",
    "password": "strongpassword456!",
    "role": "user",
    "is_confirmed": True,
    "avatar": "https://example.com/images/user_avatar.png",
}


@pytest.mark.asyncio
async def test_me(client, monkeypatch, auth_headers):
    # Mocking JWT decoding
    """
    Tests the "/users/me" endpoint for authenticated users.

    Mocks the JWT decoding and user retrieval from the database.
    Asserts that the response status is 200 and that the response
    contains the expected user details, including email, username,
    role, and avatar.
    Verifies that the JWT decode and database retrieval functions
    are called with the correct arguments.
    """

    mock_jwt = MagicMock(return_value={"sub": admin_user["username"]})
    monkeypatch.setattr("src.services.auth.jwt.decode", mock_jwt)

    # Creating mock Redis and Session instances
    mock_redis = mock.AsyncMock()
    mock_session = mock.AsyncMock()

    # Mocking user retrieval from the database
    mock_from_db = AsyncMock(return_value=admin_user)
    monkeypatch.setattr("src.services.auth.get_user_from_db", mock_from_db)

    # Making the API request
    response = client.get("/api/users/me", headers=auth_headers)

    # Assertions
    assert response.status_code == 200
    assert response.json()["email"] == admin_user["email"]
    assert response.json()["username"] == admin_user["username"]
    assert response.json()["role"] == admin_user["role"]
    assert response.json()["avatar"] == admin_user["avatar"]

    # Verifying the mock calls
    mock_jwt.assert_called_once()
    mock_from_db.assert_called_once_with(
        admin_user["username"], mock_redis, mock_session
    )


@pytest.mark.asyncio
async def test_me_unauthenticated(client, monkeypatch):
    # Mocking unauthorized access
    """
    Tests the "/users/me" endpoint returns a 401 status code and a "Not authenticated" message
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

    # Making the API request without authentication headers
    response = client.get("/api/users/me")

    # Assertions
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
