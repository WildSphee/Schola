import os
import sqlite3
import threading
from datetime import datetime
from typing import Dict, List, Optional

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
    # Ensure singleton DB
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
        # Create interactions table
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
        # Create user table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user (
                user_id TEXT PRIMARY KEY,
                pipeline TEXT,
                subjects TEXT,  -- Comma-separated list of subjects
                current_subject TEXT,
                nick_name TEXT,
                last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        # Create subject_info table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subject_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_name TEXT NOT NULL,
                subject_description TEXT,
                use_datasource BOOLEAN
            )
            """
        )
        self.conn.commit()

    # Chat history management
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

    def count_user_history(self, user_id: str) -> int:
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
                INSERT INTO user (user_id, pipeline, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET pipeline=excluded.pipeline, last_interaction=excluded.last_interaction
                """,
                (user_id, pipeline, datetime.now()),
            )

    def get_user_pipeline(self, user_id: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT pipeline FROM user WHERE user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None

    # Methods to manage user's selected subjects
    def add_user_subject(self, user_id: str, subject: int) -> None:
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT subjects FROM user WHERE user_id = ?",
                (user_id,),
            )
            subject = str(subject)

            result = cursor.fetchone()
            if result and result[0]:
                subjects = result[0].split(",")
                if subject not in subjects:
                    subjects.append(subject)
            else:
                subjects = [subject]
            subjects_str = ",".join(subjects)
            # Use INSERT ... ON CONFLICT to insert or update
            self.conn.execute(
                """
                INSERT INTO user (user_id, subjects, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET subjects=excluded.subjects, last_interaction=excluded.last_interaction
                """,
                (user_id, subjects_str, datetime.now()),
            )

    def get_user_subjects(self, user_id: str) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT subjects FROM user WHERE user_id = ?",
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
                UPDATE user SET subjects = '', last_interaction = ? WHERE user_id = ?
                """,
                (datetime.now(), user_id),
            )

    # Methods to manage current_subject
    def set_current_subject(self, user_id: str, subject: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO user (user_id, current_subject, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET current_subject=excluded.current_subject, last_interaction=excluded.last_interaction
                """,
                (user_id, subject, datetime.now()),
            )

    def get_current_subject(self, user_id: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT current_subject FROM user WHERE user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None

    # Methods to manage nick_name
    def set_nick_name(self, user_id: str, nick_name: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO user (user_id, nick_name, last_interaction)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET nick_name=excluded.nick_name, last_interaction=excluded.last_interaction
                """,
                (user_id, nick_name, datetime.now()),
            )

    def get_nick_name(self, user_id: str) -> Optional[str]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT nick_name FROM user WHERE user_id = ?
            """,
            (user_id,),
        )
        result = cursor.fetchone()
        return result[0] if result else None

    def close(self):
        self.conn.close()

    # Subject_info table
    def add_subject_info(
        self, subject_name: str, subject_description: str, use_datasource: bool
    ) -> int:
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(
                """
                INSERT INTO subject_info (subject_name, subject_description, use_datasource)
                VALUES (?, ?, ?)
                """,
                (subject_name, subject_description, use_datasource),
            )
            return cursor.lastrowid  # Returns the id of the newly inserted row

    def get_subject_info_by_id(self, subject_id: int) -> Optional[Dict[str, any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, subject_name, subject_description, use_datasource FROM subject_info
            WHERE id = ?
            """,
            (subject_id,),
        )
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "subject_name": result[1],
                "subject_description": result[2],
                "use_datasource": bool(result[3]),
            }
        return None

    def get_subject_info_by_subject_name(
        self, subject_name: str
    ) -> Optional[Dict[str, any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, subject_name, subject_description, use_datasource FROM subject_info
            WHERE subject_name = ?
            """,
            (subject_name,),
        )
        result = cursor.fetchone()
        if result:
            return {
                "id": result[0],
                "subject_name": result[1],
                "subject_description": result[2],
                "use_datasource": bool(result[3]),
            }
        return None

    def get_all_subjects_info(self) -> List[Dict[str, any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT id, subject_name, subject_description, use_datasource FROM subject_info
            """
        )
        rows = cursor.fetchall()
        subjects = []
        for row in rows:
            subjects.append(
                {
                    "id": row[0],
                    "subject_name": row[1],
                    "subject_description": row[2],
                    "use_datasource": bool(row[3]),
                }
            )
        return subjects

    def update_subject_info_by_id(
        self,
        subject_id: int,
        subject_name: Optional[str] = None,
        subject_description: Optional[str] = None,
        use_datasource: Optional[bool] = None,
    ) -> None:
        with self.conn:
            # Build the update statement dynamically based on which parameters are provided
            fields = []
            params = []
            if subject_name is not None:
                fields.append("subject_name = ?")
                params.append(subject_name)
            if subject_description is not None:
                fields.append("subject_description = ?")
                params.append(subject_description)
            if use_datasource is not None:
                fields.append("use_datasource = ?")
                params.append(use_datasource)
            params.append(subject_id)
            sql = f"""
                UPDATE subject_info
                SET {', '.join(fields)}
                WHERE id = ?
                """
            self.conn.execute(sql, params)

    def delete_subject_info_by_id(self, subject_id: int) -> None:
        with self.conn:
            self.conn.execute(
                """
                DELETE FROM subject_info WHERE id = ?
                """,
                (subject_id,),
            )


db = DB()
