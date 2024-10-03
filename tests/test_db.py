import sqlite3

import pytest
from telegram import User

from db.db import DB


@pytest.fixture
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


def test_log_interaction(db, user):
    """Test logging an interaction."""
    db.log_interaction(user, "Hello", "Hi there!")
    history = db.get_chat_history(str(user.id))
    assert len(history) == 2
    assert history[0]["content"] == "Hello"
    assert history[1]["content"] == "Hi there!"


def test_get_chat_history_empty(db, user):
    """Test retrieval of chat history when empty."""
    history = db.get_chat_history(str(user.id))
    assert history == []


def test_clear_chat_history(db, user):
    """Test clearing chat history."""
    db.log_interaction(user, "Hello", "Hi there!")
    user_id = str(user.id)
    db.clear_chat_history(user_id)
    history = db.get_chat_history(user_id)
    assert history == []


def test_check_user_messages(db, user):
    """Test checking the number of user messages."""
    user_id = str(user.id)
    assert db.check_user_messages(user_id) == 0
    db.log_interaction(user, "Hello", "Hi there!")
    assert db.check_user_messages(user_id) == 1


def test_set_and_get_user_pipeline(db):
    """Test setting and getting user pipeline."""
    user_id = str(123)
    db.set_user_pipeline(user_id, "pipeline1")
    assert db.get_user_pipeline(user_id) == "pipeline1"
