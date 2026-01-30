"""Database utilities for Flowable."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

DB_PATH = Path(__file__).parent / "starter.db"


@contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    """Database connection context manager."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
