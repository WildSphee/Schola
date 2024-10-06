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
