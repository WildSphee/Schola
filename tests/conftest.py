import pytest
from telegram import User

from db.db import DB


@pytest.fixture(scope="function")
def db(monkeypatch):
    """Set up an in-memory database for testing using monkeypatch."""
    monkeypatch.setattr("db.db.DATABASE_FILE", ":memory:")

    test_db = DB()
    test_db._create_tables()
    yield test_db
    test_db.close()


@pytest.fixture
def user():
    """Create a test user."""
    return User(
        id=123, is_bot=False, username="testuser", first_name="Test", last_name="User"
    )
