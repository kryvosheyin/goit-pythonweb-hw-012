from unittest.mock import MagicMock, AsyncMock


def test_healthchecker(client, monkeypatch):
    async def mock_get_db():
        mock = MagicMock()
        mock.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=AsyncMock(return_value=1))
        )
        yield mock

    monkeypatch.setattr("src.database.db.get_db", mock_get_db)
    response = client.get("/api/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!"}
