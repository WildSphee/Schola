# test_db.py
import sqlite3

from db.db import DB


def test_singleton_db():
    """Test that DB class is a singleton."""
    db1 = DB()
    db2 = DB()
    assert db1 is db2


def test_db_connection():
    """Test that the database connection is established."""
    db = DB()
    assert db.conn is not None
    assert isinstance(db.conn, sqlite3.Connection)
