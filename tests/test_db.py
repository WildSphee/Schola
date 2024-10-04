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
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
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


def test_count_user_history(db, user):
    """Test counting the number of user messages."""
    user_id = str(user.id)
    assert db.count_user_history(user_id) == 0
    db.log_interaction(user, "Hello", "Hi there!")
    assert db.count_user_history(user_id) == 1


def test_set_and_get_user_pipeline(db):
    """Test setting and getting user pipeline."""
    user_id = str(123)
    db.set_user_pipeline(user_id, "pipeline1")
    assert db.get_user_pipeline(user_id) == "pipeline1"


def test_add_and_get_user_subjects(db):
    """Test adding and getting user subjects."""
    user_id = str(123)
    db.add_user_subject(user_id, "Math")
    db.add_user_subject(user_id, "Science")
    subjects = db.get_user_subjects(user_id)
    assert subjects == ["Math", "Science"]


def test_clear_user_subjects(db):
    """Test clearing user subjects."""
    user_id = str(123)
    db.add_user_subject(user_id, "Math")
    db.add_user_subject(user_id, "Science")
    db.clear_user_subjects(user_id)
    subjects = db.get_user_subjects(user_id)
    assert subjects == []


def test_set_and_get_current_subject(db):
    """Test setting and getting current subject."""
    user_id = str(123)
    db.set_current_subject(user_id, "History")
    assert db.get_current_subject(user_id) == "History"
    # Change current subject
    db.set_current_subject(user_id, "Geography")
    assert db.get_current_subject(user_id) == "Geography"


def test_set_and_get_nick_name(db):
    """Test setting and getting nick name."""
    user_id = str(123)
    db.set_nick_name(user_id, "Johnny")
    assert db.get_nick_name(user_id) == "Johnny"
    # Change nick name
    db.set_nick_name(user_id, "John")
    assert db.get_nick_name(user_id) == "John"


def test_subject_info_table(db):
    """Test inserting and querying subject_info table."""
    cursor = db.conn.cursor()
    # Insert a subject
    cursor.execute(
        """
        INSERT INTO subject_info (subject_name, subject_description, use_datasource)
        VALUES (?, ?, ?)
        """,
        ("Mathematics", "Study of numbers and shapes", True),
    )
    db.conn.commit()
    # Query the subject
    cursor.execute(
        "SELECT subject_name, subject_description, use_datasource FROM subject_info WHERE subject_name = ?",
        ("Mathematics",),
    )
    result = cursor.fetchone()
    assert result == (
        "Mathematics",
        "Study of numbers and shapes",
        1,
    )  # SQLite stores booleans as integers


def test_interaction_methods(db, user):
    """Test interaction methods with multiple messages."""
    user_id = str(user.id)
    db.log_interaction(user, "Hi", "Hello!")
    db.log_interaction(user, "How are you?", "I'm fine, thank you.")
    history = db.get_chat_history(user_id)
    assert len(history) == 4
    assert history[0]["content"] == "Hi"
    assert history[1]["content"] == "Hello!"
    assert history[2]["content"] == "How are you?"
    assert history[3]["content"] == "I'm fine, thank you."
    assert db.count_user_history(user_id) == 2  # Only user messages are counted


def test_user_not_found(db):
    """Test methods when user does not exist."""
    user_id = "999"
    assert db.get_user_pipeline(user_id) is None
    assert db.get_user_subjects(user_id) == []
    assert db.get_current_subject(user_id) is None
    assert db.get_nick_name(user_id) is None


def test_update_last_interaction(db):
    """Test that last_interaction is updated."""
    user_id = str(123)
    db.set_user_pipeline(user_id, "pipeline1")
    cursor = db.conn.cursor()
    cursor.execute(
        "SELECT last_interaction FROM user WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchone()
    first_timestamp = result[0]

    db.set_current_subject(user_id, "History")
    cursor.execute(
        "SELECT last_interaction FROM user WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchone()
    second_timestamp = result[0]

    assert second_timestamp >= first_timestamp


def test_singleton_db():
    """Test that DB class is a singleton."""
    db1 = DB()
    db2 = DB()
    assert db1 is db2
