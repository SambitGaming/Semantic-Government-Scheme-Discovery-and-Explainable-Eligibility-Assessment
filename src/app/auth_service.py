
"""Authentication and user-profile storage for the scholarship assistant."""

import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(
    os.getenv(
        "SCHOLARSHIP_DB_PATH",
        str(PROJECT_ROOT / "data" / "government_schemes.db"),
    )
)

bearer_scheme = HTTPBearer(auto_error=False)
TOKEN_LIFETIME_HOURS = 24 * 7


def get_connection():
    """Open the existing project database."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(DB_PATH), timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_auth_tables():
    """Create authentication tables without changing existing tables."""
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id INTEGER PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                state TEXT,
                category TEXT,
                annual_income REAL,
                education_level TEXT,
                study_mode TEXT,
                course TEXT,
                occupation TEXT,
                year_of_study INTEGER,
                disability_percentage REAL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id)
                    REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id
            ON user_sessions(user_id)
        """)

        connection.commit()


def utc_now():
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    """Hash a password with a unique salt using scrypt."""
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=2**14,
        r=8,
        p=1,
        dklen=32,
    )
    return f"scrypt${salt.hex()}${derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, salt_hex, digest_hex = stored_hash.split("$", 2)
        if algorithm != "scrypt":
            return False

        derived = hashlib.scrypt(
            password.encode("utf-8"),
            salt=bytes.fromhex(salt_hex),
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )
        return hmac.compare_digest(derived.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def create_session(user_id: int) -> str:
    """Create an opaque random bearer token and store only its hash."""
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = utc_now()
    expires = now + timedelta(hours=TOKEN_LIFETIME_HOURS)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_sessions
                (token_hash, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (token_hash, user_id, expires.isoformat(), now.isoformat()),
        )
        connection.commit()

    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
):
    """Require a valid, unexpired session for protected endpoints."""
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_hash = hashlib.sha256(
        credentials.credentials.encode()
    ).hexdigest()

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT u.user_id, u.username, u.email, s.expires_at
            FROM user_sessions s
            JOIN users u ON u.user_id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if not row:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session.",
            )

        if datetime.fromisoformat(row["expires_at"]) <= utc_now():
            connection.execute(
                "DELETE FROM user_sessions WHERE token_hash = ?",
                (token_hash,),
            )
            connection.commit()
            raise HTTPException(
                status_code=401,
                detail="Session expired. Please log in again.",
            )

        return {
            "user_id": row["user_id"],
            "username": row["username"],
            "email": row["email"],
            "token_hash": token_hash,
        }


def save_profile(user_id: int, profile: dict):
    """Insert or update the authenticated user's questionnaire answers."""
    allowed_fields = {
        "age", "gender", "state", "category", "annual_income",
        "education_level", "study_mode", "course", "occupation",
        "year_of_study", "disability_percentage",
    }

    profile = {
        key: value
        for key, value in profile.items()
        if key in allowed_fields
    }

    now = utc_now().isoformat()

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO user_profiles (
                user_id, age, gender, state, category, annual_income,
                education_level, study_mode, course, occupation,
                year_of_study, disability_percentage, updated_at
            )
            VALUES (
                :user_id, :age, :gender, :state, :category, :annual_income,
                :education_level, :study_mode, :course, :occupation,
                :year_of_study, :disability_percentage, :updated_at
            )
            ON CONFLICT(user_id) DO UPDATE SET
                age = excluded.age,
                gender = excluded.gender,
                state = excluded.state,
                category = excluded.category,
                annual_income = excluded.annual_income,
                education_level = excluded.education_level,
                study_mode = excluded.study_mode,
                course = excluded.course,
                occupation = excluded.occupation,
                year_of_study = excluded.year_of_study,
                disability_percentage = excluded.disability_percentage,
                updated_at = excluded.updated_at
            """,
            {
                "user_id": user_id,
                **{field: profile.get(field) for field in allowed_fields},
                "updated_at": now,
            },
        )
        connection.commit()


def get_profile(user_id: int):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM user_profiles WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if not row:
        return None

    result = dict(row)
    result.pop("user_id", None)
    result.pop("updated_at", None)
    return result


def revoke_session(token_hash: str):
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM user_sessions WHERE token_hash = ?",
            (token_hash,),
        )
        connection.commit()


initialize_auth_tables()
