from unittest.mock import MagicMock, AsyncMock


def test_healthchecker(client, monkeypatch):
    async def mock_get_db():
        """
        Mock for src.database.db.get_db

        This mock function is used to mock out the database session in the healthchecker
        test. It returns a mock session object that returns a mock result object with
        a scalar_one_or_none method that returns 1.
        """
        mock = MagicMock()
        mock.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=AsyncMock(return_value=1))
        )
        yield mock

    monkeypatch.setattr("src.database.db.get_db", mock_get_db)
    response = client.get("/api/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!"}
