import sqlite3
from datetime import datetime, timedelta, UTC
from typing import Any


class DatabaseStorage:
    def __init__(self, db_path="merchant_data.db"):
        self.db_path = db_path

    def insert_token(self, gateway_token: str, bearer_token: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
            INSERT OR REPLACE INTO merchant_tokens (gateway_token, bearer_token, created_at)
            VALUES (?, ?, ?);
            """, (gateway_token, bearer_token, datetime.now(UTC)))
            conn.commit()

    def get_token(self, gateway_token: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                               SELECT bearer_token
                               FROM merchant_tokens
                               WHERE gateway_token = ?;
                               """, (gateway_token,)).fetchone()
            return row[0] if row else None

    def delete_old_tokens(self, days=10):
        cutoff = datetime.now(UTC) - timedelta(days=days)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                         DELETE FROM merchant_tokens
                         WHERE created_at < ?;
                         """, (cutoff,))
            conn.commit()

    def upsert_auth_token(self, login: str, token: str, expires_at: datetime):
        if not all([login, token, expires_at]):
            return None

        now = datetime.now(UTC)
        margin = timedelta(minutes=5)

        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                               SELECT token, expires_at
                               FROM auth_tokens
                               WHERE login = ?;
                               """, (login,)).fetchone()

            if not row:
                conn.execute("""
                             INSERT INTO auth_tokens (login, token, expires_at)
                             VALUES (?, ?, ?);
                             """, (login, token, expires_at.isoformat()))
                conn.commit()
                return "inserted"

            _, exp_str = row
            exp_dt = datetime.fromisoformat(exp_str)

            if exp_dt > now + margin:
                return "skipped"

            conn.execute("""
                         UPDATE auth_tokens
                         SET token      = ?,
                             expires_at = ?
                         WHERE login = ?;
                         """, (token, expires_at.isoformat(), login))
            conn.commit()
            return "updated"

    def get_auth_token(self, login: str) -> tuple[Any, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                               SELECT token, expires_at
                               FROM auth_tokens
                               WHERE login = ?;
                               """, (login,)).fetchone()

        if not row:
            return None

        token, exp_str = row
        exp = datetime.fromisoformat(exp_str)
        if exp > datetime.now(UTC) + timedelta(minutes=5):
            return token
        return None
