"""Database connection managers and initialization."""

import sqlite3
import logging
from contextlib import contextmanager
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and initialization."""

    def __init__(self, db_path: str, capability_config_db_path: str):
        self.db_path = db_path
        self.capability_config_db_path = capability_config_db_path

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

    @contextmanager
    def get_capability_config_db(self):
        """Context manager for capability configuration database connections."""
        conn = None
        try:
            conn = sqlite3.connect(self.capability_config_db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except sqlite3.IntegrityError:
            # Re-raise IntegrityError so it can be handled by the caller
            raise
        except sqlite3.Error as e:
            logger.error(f"Capability config database error: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {e}")
        finally:
            if conn:
                conn.close()

    def init_capability_config_db(self):
        """Initialize the capability configuration database with schema."""
        logger.info(f"Initializing capability config database at {self.capability_config_db_path}")

        with self.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Create capability_scenarios table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capability_scenarios (
                    scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    scenario_name TEXT NOT NULL,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, scenario_name)
                )
            """
            )

            # Create capability_selections table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS capability_selections (
                    selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER NOT NULL,
                    capability_id TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
                    UNIQUE(scenario_id, capability_id)
                )
            """
            )

            # Create control_selections table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS control_selections (
                    selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scenario_id INTEGER NOT NULL,
                    control_id TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 0,
                    FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
                    UNIQUE(scenario_id, control_id)
                )
            """
            )

            # Create indexes
            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_scenario_user
                ON capability_scenarios(user_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_selection_scenario
                ON capability_selections(scenario_id)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_control_selection_scenario
                ON control_selections(scenario_id)
            """
            )

            conn.commit()
            logger.info("Capability config database initialized successfully")
