"""
Database Manager for Data Processing Microservice

Handles all database operations including schema creation, data insertion,
and metadata management for the SQLite database.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations for the data processing microservice.

    Handles schema creation, data insertion, and metadata storage with proper
    error handling and transaction management.
    """

    def __init__(self, db_path: Path):
        """
        Initialize the database manager.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

    def _get_connection(self) -> sqlite3.Connection:
        """
        Get database connection, creating if necessary.

        Returns:
            SQLite database connection
        """
        if self.connection is None:
            # Ensure directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self.connection = sqlite3.connect(str(self.db_path))
            self.connection.row_factory = sqlite3.Row  # Enable column access by name

            logger.info(f"Connected to database: {self.db_path}")

        return self.connection

    def create_tables(self) -> None:
        """
        Create all required database tables with proper schema.
        """
        logger.info("Creating database tables")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Create risks table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS risks (
                risk_id TEXT PRIMARY KEY,
                risk_title TEXT NOT NULL,
                risk_description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create controls table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS controls (
                control_id TEXT PRIMARY KEY,
                control_title TEXT NOT NULL,
                control_description TEXT,
                asset_type TEXT,
                control_type TEXT,
                security_function TEXT,
                maturity_level TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create questions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS questions (
                question_id TEXT PRIMARY KEY,
                question_text TEXT NOT NULL,
                category TEXT,
                topic TEXT,
                managing_role TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create definitions table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS definitions (
                definition_id TEXT PRIMARY KEY,
                term TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create risk-control mapping table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS risk_control_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                risk_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (risk_id) REFERENCES risks (risk_id),
                FOREIGN KEY (control_id) REFERENCES controls (control_id),
                UNIQUE(risk_id, control_id)
            )
        """
        )

        # Create question-risk mapping table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_risk_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                risk_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions (question_id),
                FOREIGN KEY (risk_id) REFERENCES risks (risk_id),
                UNIQUE(question_id, risk_id)
            )
        """
        )

        # Create question-control mapping table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS question_control_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_id TEXT NOT NULL,
                control_id TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions (question_id),
                FOREIGN KEY (control_id) REFERENCES controls (control_id),
                UNIQUE(question_id, control_id)
            )
        """
        )

        # Create file metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS file_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_type TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_exists BOOLEAN NOT NULL,
                file_size INTEGER,
                file_modified_time TIMESTAMP,
                version TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create processing metadata table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS processing_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data_version TEXT,
                total_risks INTEGER,
                total_controls INTEGER,
                total_questions INTEGER,
                total_risk_control_mappings INTEGER,
                total_question_risk_mappings INTEGER,
                total_question_control_mappings INTEGER,
                processing_status TEXT DEFAULT 'completed'
            )
        """
        )

        conn.commit()
        logger.info("Database tables created successfully")

    def migrate_database(self) -> None:
        """
        Run database migrations to update schema if needed.

        This method handles schema evolution and data migration.
        """
        logger.info("Running database migrations")

        conn = self._get_connection()
        cursor = conn.cursor()

        # Check if this is a new database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' " "AND name='processing_metadata'")
        is_new_db = cursor.fetchone() is None

        if is_new_db:
            logger.info("New database detected, no migrations needed")
            return

        # Add any future migrations here
        # Example: Add new columns, create indexes, etc.

        conn.commit()
        logger.info("Database migrations completed")

    def insert_data(
        self,
        table_name: str,
        data_df: Optional[pd.DataFrame],
        timestamp: Optional[str] = None,
    ) -> None:
        """
        Insert data into the specified table.

        Args:
            table_name: Name of the target table
            data_df: DataFrame containing data to insert
            timestamp: Optional timestamp for created_at/updated_at fields
        """
        if data_df is None or data_df.empty:
            logger.warning(f"No data to insert into {table_name}")
            return

        logger.info(f"Inserting {len(data_df)} records into {table_name}")

        conn = self._get_connection()

        try:
            # Prepare data for insertion
            if timestamp:
                data_df = data_df.copy()
                data_df["created_at"] = timestamp
                data_df["updated_at"] = timestamp

            # Insert data using pandas to_sql with if_exists='replace'
            data_df.to_sql(table_name, conn, if_exists="replace", index=False, method="multi")

            conn.commit()
            logger.info(f"Successfully inserted {len(data_df)} records into {table_name}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting data into {table_name}: {e}")
            raise

    def insert_file_metadata(
        self,
        data_type: str,
        filename: str,
        file_exists: bool,
        file_size: Optional[int] = None,
        file_modified_time: Optional[str] = None,
        version: str = "unknown",
    ) -> None:
        """
        Insert file metadata into the database.

        Args:
            data_type: Type of data (risks, controls, questions)
            filename: Name of the file
            file_exists: Whether the file exists
            file_size: Size of the file in bytes
            file_modified_time: File modification timestamp
            version: Version extracted from filename
        """
        logger.info(f"Inserting file metadata for {data_type}: {filename}")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO file_metadata
                (data_type, filename, file_exists, file_size, file_modified_time,
                 version)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    data_type,
                    filename,
                    file_exists,
                    file_size,
                    file_modified_time,
                    version,
                ),
            )

            conn.commit()
            logger.info(f"File metadata inserted for {filename}")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting file metadata: {e}")
            raise

    def insert_processing_metadata(
        self,
        data_version: str,
        total_risks: int,
        total_controls: int,
        total_questions: int,
        total_risk_control_mappings: int = 0,
        total_question_risk_mappings: int = 0,
        total_question_control_mappings: int = 0,
        processing_status: str = "completed",
    ) -> None:
        """
        Insert processing metadata into the database.

        Args:
            data_version: Version of the processed data
            total_risks: Total number of risks processed
            total_controls: Total number of controls processed
            total_questions: Total number of questions processed
            total_risk_control_mappings: Total number of risk-control mappings
            total_question_risk_mappings: Total number of question-risk mappings
            total_question_control_mappings: Total number of question-control mappings
            processing_status: Status of the processing operation
        """
        logger.info("Inserting processing metadata")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO processing_metadata
                (data_version, total_risks, total_controls, total_questions,
                 total_risk_control_mappings, total_question_risk_mappings,
                 total_question_control_mappings, processing_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data_version,
                    total_risks,
                    total_controls,
                    total_questions,
                    total_risk_control_mappings,
                    total_question_risk_mappings,
                    total_question_control_mappings,
                    processing_status,
                ),
            )

            conn.commit()
            logger.info("Processing metadata inserted successfully")

        except Exception as e:
            conn.rollback()
            logger.error(f"Error inserting processing metadata: {e}")
            raise

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get information about a table.

        Args:
            table_name: Name of the table

        Returns:
            List of dictionaries containing table information
        """
        # Validate table name to prevent SQL injection
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()

        return [dict(column) for column in columns]

    def get_table_count(self, table_name: str) -> int:
        """
        Get the number of records in a table.

        Args:
            table_name: Name of the table

        Returns:
            Number of records in the table
        """
        # Validate table name to prevent SQL injection
        import re

        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            raise ValueError(f"Invalid table name: {table_name}")

        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]

    def close_connection(self) -> None:
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()
