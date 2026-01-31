import pandas as pd

"""
Unit tests for DatabaseManager class.

Tests database operations, schema creation, and data insertion.
"""

import sqlite3
from unittest.mock import patch

import pytest

from database_manager import DatabaseManager


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    def test_init(self, temp_dir):
        """Test DatabaseManager initialization."""
        db_path = temp_dir / "test.db"
        manager = DatabaseManager(db_path)

        assert manager.db_path == db_path
        assert manager.connection is None

    def test_get_connection(self, temp_dir):
        """Test database connection creation."""
        db_path = temp_dir / "test.db"
        manager = DatabaseManager(db_path)

        conn = manager._get_connection()

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        assert manager.connection is conn

    def test_get_connection_caching(self, temp_dir):
        """Test that connection is cached."""
        db_path = temp_dir / "test.db"
        manager = DatabaseManager(db_path)

        conn1 = manager._get_connection()
        conn2 = manager._get_connection()

        assert conn1 is conn2

    def test_create_tables(self, database_manager):
        """Test database table creation."""
        database_manager.create_tables()

        # Verify tables exist
        conn = database_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        expected_tables = [
            "risks",
            "controls",
            "questions",
            "definitions",
            "risk_control_mapping",
            "question_risk_mapping",
            "question_control_mapping",
            "file_metadata",
            "processing_metadata",
        ]

        for table in expected_tables:
            assert table in tables

    def test_create_tables_idempotent(self, database_manager):
        """Test that create_tables is idempotent."""
        # Create tables twice
        database_manager.create_tables()
        database_manager.create_tables()

        # Should not raise any errors
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        # Should succeed without error

    def test_migrate_database_new_db(self, database_manager):
        """Test migration on new database."""
        # Create tables first
        database_manager.create_tables()

        # Migration should succeed
        database_manager.migrate_database()

        # Verify processing_metadata table exists
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND "
            "name='processing_metadata'"
        )
        assert cursor.fetchone() is not None

    def test_insert_data_success(self, database_manager, sample_risks_data):
        """Test successful data insertion."""
        database_manager.create_tables()

        database_manager.insert_data("risks", sample_risks_data)

        # Verify data was inserted
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        count = cursor.fetchone()[0]

        assert count == len(sample_risks_data)

    def test_insert_data_empty_dataframe(self, database_manager):
        """Test insertion with empty DataFrame."""
        database_manager.create_tables()

        empty_df = pd.DataFrame()
        database_manager.insert_data("risks", empty_df)

        # Should not raise error
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        count = cursor.fetchone()[0]

        assert count == 0

    def test_insert_data_none_dataframe(self, database_manager):
        """Test insertion with None DataFrame."""
        database_manager.create_tables()

        database_manager.insert_data("risks", None)

        # Should not raise error
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        count = cursor.fetchone()[0]

        assert count == 0

    def test_insert_data_with_timestamp(self, database_manager, sample_risks_data):
        """Test data insertion with timestamp."""
        database_manager.create_tables()

        timestamp = "2024-01-01 12:00:00"
        database_manager.insert_data("risks", sample_risks_data, timestamp)

        # Verify timestamp was set
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM risks LIMIT 1")
        result = cursor.fetchone()

        assert result[0] == timestamp

    def test_insert_file_metadata(self, database_manager):
        """Test file metadata insertion."""
        database_manager.create_tables()

        metadata = {
            "data_type": "risks",
            "filename": "test_risks.xlsx",
            "file_exists": True,
            "file_size": 1024,
            "file_modified_time": "2024-01-01 12:00:00",
            "version": "v1.0",
        }

        database_manager.insert_file_metadata(**metadata)

        # Verify metadata was inserted
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM file_metadata WHERE data_type = 'risks'")
        result = cursor.fetchone()

        assert result is not None
        assert result[1] == "risks"  # data_type
        assert result[2] == "test_risks.xlsx"  # filename

    def test_insert_processing_metadata(self, database_manager):
        """Test processing metadata insertion."""
        database_manager.create_tables()

        database_manager.insert_processing_metadata(
            data_version="v1.0",
            total_risks=10,
            total_controls=5,
            total_questions=15,
            total_risk_control_mappings=20,
            total_question_risk_mappings=25,
            total_question_control_mappings=30,
            processing_status="completed",
        )

        # Verify metadata was inserted
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM processing_metadata")
        result = cursor.fetchone()

        assert result is not None
        # Column order: id, processing_date, data_version, total_risks, total_controls,
        # total_questions, total_capabilities, total_risk_control_mappings,
        # total_question_risk_mappings, total_question_control_mappings,
        # total_capability_control_mappings, processing_status
        assert result[2] == "v1.0"  # data_version (index 2)
        assert result[3] == 10  # total_risks (index 3)
        assert result[4] == 5  # total_controls (index 4)
        assert result[5] == 15  # total_questions (index 5)
        assert result[6] == 0  # total_capabilities (index 6) - default value
        assert result[11] == "completed"  # processing_status (index 11)

    def test_get_table_info(self, database_manager):
        """Test getting table information."""
        database_manager.create_tables()

        table_info = database_manager.get_table_info("risks")

        assert isinstance(table_info, list)
        assert len(table_info) > 0

        # Check that we have expected columns
        column_names = [col["name"] for col in table_info]
        expected_columns = ["risk_id", "risk_title", "risk_description"]

        for col in expected_columns:
            assert col in column_names

    def test_get_table_count(self, database_manager, sample_risks_data):
        """Test getting table record count."""
        database_manager.create_tables()

        # Insert test data
        database_manager.insert_data("risks", sample_risks_data)

        count = database_manager.get_table_count("risks")

        assert count == len(sample_risks_data)

    def test_close_connection(self, database_manager):
        """Test connection closing."""
        # Create connection
        database_manager._get_connection()
        assert database_manager.connection is not None

        # Close connection
        database_manager.close_connection()
        assert database_manager.connection is None

    def test_context_manager(self, temp_dir):
        """Test DatabaseManager as context manager."""
        db_path = temp_dir / "context_test.db"

        with DatabaseManager(db_path) as manager:
            # Test that we can use the manager within the context
            manager.create_tables()
            # Verify connection is available when needed
            conn = manager._get_connection()
            assert conn is not None

        # Connection should be closed after context exit
        assert manager.connection is None

    def test_transaction_rollback_on_error(self, database_manager, sample_risks_data):
        """Test transaction rollback on error."""
        database_manager.create_tables()

        # Mock pandas to_sql to raise an error
        with patch("pandas.DataFrame.to_sql", side_effect=Exception("Test error")):
            with pytest.raises(Exception):
                database_manager.insert_data("risks", sample_risks_data)

        # Verify no data was inserted
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        count = cursor.fetchone()[0]

        assert count == 0

    def test_foreign_key_constraints(
        self, database_manager, sample_risks_data, sample_controls_data
    ):
        """Test foreign key constraints."""
        database_manager.create_tables()

        # Insert parent data
        database_manager.insert_data("risks", sample_risks_data)
        database_manager.insert_data("controls", sample_controls_data)

        # Create mapping data
        mapping_data = pd.DataFrame(
            {"risk_id": ["AIR.001", "AIR.002"], "control_id": ["AIGPC.1", "AIGPC.2"]}
        )

        database_manager.insert_data("risk_control_mapping", mapping_data)

        # Verify mapping was inserted
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risk_control_mapping")
        count = cursor.fetchone()[0]

        assert count == 2

    def test_unique_constraints(self, database_manager, sample_risks_data):
        """Test unique constraints."""
        database_manager.create_tables()

        # Insert data twice with same IDs
        database_manager.insert_data("risks", sample_risks_data)
        database_manager.insert_data("risks", sample_risks_data)

        # Should only have unique records
        conn = database_manager._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM risks")
        count = cursor.fetchone()[0]

        assert count == len(sample_risks_data)
