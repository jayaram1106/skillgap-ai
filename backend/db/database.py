"""
SkillGap AI - SQLite Database Connection & Lifecycle Manager.

Configures:
- Foreign key constraint enforcement on every connection.
- Write-Ahead Logging (WAL) journal mode for high concurrency.
- 5000ms busy timeout to prevent lock contention.
- Parameterized execution context managers.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional

# Default database location inside backend/db/
DEFAULT_DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DEFAULT_DB_DIR, "skillgap.db")
SCHEMA_PATH = os.path.join(DEFAULT_DB_DIR, "schema.sql")


def get_db_path() -> str:
    """Return configured SQLite database file path."""
    return os.getenv("SQLITE_DB_PATH", DEFAULT_DB_PATH)


def configure_pragmas(conn: sqlite3.Connection) -> None:
    """
    Apply essential SQLite PRAGMA settings on every connection.
    - foreign_keys = ON: Mandatory per SQLite specs (disabled by default in SQLite).
    - journal_mode = WAL: Enables non-blocking concurrent reads during writes.
    - busy_timeout = 5000: Wait up to 5 seconds if database is temporarily locked.
    - synchronous = NORMAL: Safe and fast with WAL journal mode.
    """
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("PRAGMA busy_timeout = 5000;")
    cursor.execute("PRAGMA journal_mode = WAL;")
    cursor.execute("PRAGMA synchronous = NORMAL;")
    cursor.close()


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Create and return a configured SQLite connection with Row factory and PRAGMAs.
    """
    target_path = db_path or get_db_path()

    # Ensure parent directory exists
    parent_dir = os.path.dirname(target_path)
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)

    conn = sqlite3.connect(target_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    configure_pragmas(conn)
    return conn


@contextmanager
def get_db(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager yielding a transactional database connection.
    Automatically commits on normal completion or rolls back on error.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None, schema_file: Optional[str] = None) -> None:
    """
    Initialize SQLite database schema from schema.sql.
    Idempotent operation (uses CREATE TABLE IF NOT EXISTS).
    """
    target_path = db_path or get_db_path()
    sql_path = schema_file or SCHEMA_PATH

    if not os.path.exists(sql_path):
        raise FileNotFoundError(f"Schema file not found at: {sql_path}")

    with open(sql_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db(target_path) as conn:
        conn.executescript(schema_sql)
