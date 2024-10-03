import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel
from telegram import User

DATABASE_FILE = f"{os.getenv('DATABASE_NAME') or 'default'}.db"


class Interaction(BaseModel):
    user_id: str
    username: str
    first_name: str
    last_name: str
    user_message: str
    bot_response: str
    timestamp: datetime

    class Config:
        from_attributes = True


class DB:
    # ensure its singleton DB
    _instance_lock = threading.Lock()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(DB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                user_message TEXT,
                bot_response TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_states (
                user_id TEXT PRIMARY KEY,
                pipeline TEXT,
                subjects TEXT,  -- Comma-separated list of subjects
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        self.conn.commit()

    def log_interaction(self, user: User, user_message: str, bot_response: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO interactions (
                    user_id, username, first_name, last_name,
                    user_message, bot_response, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(user.id),
                    user.username or "",
                    user.first_name or "",
                    user.last_name or "",
                    user_message,
                    bot_response,
                    datetime.now(),
                ),
            )

    def get_chat_history(self, user_id: str) -> List[Dict[str, str]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT user_message, bot_response FROM interactions
            WHERE user_id = ?
            ORDER BY id ASC
            """,
            (user_id,),
        )
        rows = cursor.fetchall()
        history = []
        for user_message, bot_response in rows:
            history.append({"role": "user", "content": user_message or ""})
            history.append({"role": "assistant", "content": bot_response or ""})
        return history

    def clear_chat_history(self, user_id: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                DELETE FROM interactions WHERE user_id = ?
                """,
                (user_id,),
            )

    def check_user_messages(self, user_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM interactions WHERE user_id = ?
            """,
            (user_id,),
        )
        count = cursor.fetchone()[0]
        return count

    # Pipeline management methods
    def set_user_pipeline(self, user_id: str, pipeline: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO user_states (user_id, pipeline, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET pipeline=excluded.pipeline, last_interaction=excluded.last_interaction
                """,
                (user_id, pipeline, datetime.now()),
            )

    def get_user_pipeline(self, user_id: str) -> str:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT pipeline FROM user_states WHERE user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None

    # Methods to manage user's selected subjects
    def add_user_subject(self, user_id: str, subject: str) -> None:
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT subjects FROM user_states WHERE user_id = ?",
                (user_id,),
            )
            result = cursor.fetchone()
            if result and result[0]:
                subjects = result[0].split(",")
                if subject not in subjects:
                    subjects.append(subject)
            else:
                subjects = [subject]
            subjects_str = ",".join(subjects)
            self.conn.execute(
                """
                UPDATE user_states SET subjects = ?, last_interaction = ? WHERE user_id = ?
                """,
                (subjects_str, datetime.now(), user_id),
            )

    def get_user_subjects(self, user_id: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT subjects FROM user_states WHERE user_id = ?",
            (user_id,),
        )
        result = cursor.fetchone()
        if result and result[0]:
            return result[0].split(",")
        else:
            return []

    def clear_user_subjects(self, user_id: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                UPDATE user_states SET subjects = '', last_interaction = ? WHERE user_id = ?
                """,
                (datetime.now(), user_id),
            )

    def close(self):
        self.conn.close()


db = DB()
