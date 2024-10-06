import sqlite3

import pytest
from telegram import User

from db.db import DB


@pytest.fixture(scope='session')
def db():
    """Set up an in-memory database for testing."""
    test_db = DB()
    test_db.conn = sqlite3.connect(":memory:", check_same_thread=False)
    test_db._create_tables()
    yield test_db
    test_db.close()


@pytest.fixture
def user():
    """Create a test user."""
    return User(
        id=123, is_bot=False, username="testuser", first_name="Test", last_name="User"
    )
