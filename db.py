import sqlite3
from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel
from telegram import User

DATABASE_FILE = "interactions.db"


class Interaction(BaseModel):
    user_id: str
    username: str
    first_name: str
    last_name: str
    user_message: str
    bot_response: str
    timestamp: datetime

    class Config:
        orm_mode = True


class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        self._create_table()

    def _create_table(self):
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
                    datetime.utcnow(),
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

    def _clear_chat_history(self, user: User) -> None:
        with self.conn:
            self.conn.execute(
                """
                DELETE FROM interactions WHERE user_id = ?
                """,
                (str(user.id),),
            )

    def check_user_messages(self, user: User) -> int:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) FROM interactions WHERE user_id = ?
            """,
            (str(user.id),),
        )
        count = cursor.fetchone()[0]
        return count

    def close(self):
        self.conn.close()
