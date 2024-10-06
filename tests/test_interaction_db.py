def test_log_interaction(db, user):
    """Test logging an interaction."""
    db.log_interaction(user, "Hello", "Hi there!")
    history = db.get_chat_history(str(user.id))
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"


def test_log_interaction_with_current_fields(db, user):
    """Test logging an interaction with current_subject and current_pipeline."""
    db.log_interaction(
        user, "Hello", "Hi there!", current_subject="Math", current_pipeline="Learning"
    )
    cursor = db.conn.cursor()
    cursor.execute(
        """
        SELECT current_subject, current_pipeline FROM interactions WHERE user_id = ?
        """,
        (str(user.id),),
    )
    result = cursor.fetchone()
    assert result == ("Math", "Learning")


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
