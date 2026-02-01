"""Database connection managers and initialization."""

import sqlite3
import logging
from contextlib import contextmanager
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization."""

    def __init__(self, db_path: str):
        self.db_path = db_path

    @contextmanager
    def get_db_connection(self):
        """Context manager for main database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            if conn:
                conn.close()
