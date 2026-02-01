"""
Integration tests for Database Service.

Tests complete workflows and database operations.
"""

import pytest
import sqlite3
import json
import time

# Import the app
import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.append(str(Path(__file__).parent.parent))

# Conditional imports
try:
    from app import app, get_db_connection, validate_database, reinitialize_repositories
    from unittest.mock import patch
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


class TestDatabaseOperations:
    """Test database operations and workflows."""

    def test_database_validation_success(self, sample_database, mock_config_manager):
        """Test database validation with valid database."""
        reinitialize_repositories(str(sample_database))
        result = validate_database()
        assert result is True

    def test_database_validation_missing_file(self, mock_config_manager):
        """Test database validation with missing database file."""
        reinitialize_repositories("/nonexistent/database.db")
        result = validate_database()
        assert result is False

    def test_database_validation_missing_tables(self, temp_dir, mock_config_manager):
        """Test database validation with missing required tables."""
        # Create database with missing tables
        db_path = temp_dir / "incomplete.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE risks (id TEXT PRIMARY KEY)")
        conn.commit()
        conn.close()

        reinitialize_repositories(str(db_path))
        result = validate_database()
        assert result is False

    def test_database_connection_context_manager(
        self, sample_database, mock_config_manager
    ):
        """Test database connection context manager."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            assert conn is not None
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM risks")
            count = cursor.fetchone()[0]
            assert count > 0

    def test_database_connection_error_handling(self, mock_config_manager):
        """Test database connection error handling."""
        with patch("sqlite3.connect") as mock_connect:
            mock_connect.side_effect = sqlite3.Error("Connection failed")
            with pytest.raises(Exception):
                with get_db_connection() as conn:
                    pass


class TestDataRetrievalWorkflows:
    """Test complete data retrieval workflows."""

    def test_complete_risk_retrieval_workflow(
        self, sample_database, mock_config_manager
    ):
        """Test complete workflow for retrieving risk data."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Test basic risk retrieval
            cursor.execute("SELECT * FROM risks LIMIT 1")
            risk = cursor.fetchone()
            assert risk is not None

            # Test risk with relationships
            risk_id = risk["risk_id"]
            cursor.execute(
                """
                SELECT c.control_id, c.control_title
                FROM controls c
                JOIN risk_control_mapping rcm ON c.control_id = rcm.control_id
                WHERE rcm.risk_id = ?
            """,
                (risk_id,),
            )
            controls = cursor.fetchall()
            assert len(controls) > 0

    def test_complete_control_retrieval_workflow(
        self, sample_database, mock_config_manager
    ):
        """Test complete workflow for retrieving control data."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Test basic control retrieval
            cursor.execute("SELECT * FROM controls LIMIT 1")
            control = cursor.fetchone()
            assert control is not None

            # Test control with relationships
            control_id = control["control_id"]
            cursor.execute(
                """
                SELECT r.risk_id, r.risk_title
                FROM risks r
                JOIN risk_control_mapping rcm ON r.risk_id = rcm.risk_id
                WHERE rcm.control_id = ?
            """,
                (control_id,),
            )
            risks = cursor.fetchall()
            assert len(risks) > 0


class TestSearchWorkflows:
    """Test search functionality workflows."""

    def test_cross_entity_search_workflow(self, sample_database, mock_config_manager):
        """Test searching across entities."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            search_term = "privacy"
            search_pattern = f"%{search_term}%"

            # Search risks
            cursor.execute(
                """
                SELECT 'risk' as type, risk_id as id, risk_title as title,
                       risk_description as description
                FROM risks
                WHERE risk_title LIKE ? OR risk_description LIKE ?
            """,
                (search_pattern, search_pattern),
            )
            risk_results = cursor.fetchall()

            # Search controls
            cursor.execute(
                """
                SELECT 'control' as type, control_id as id, control_title as title,
                       control_description as description
                FROM controls
                WHERE control_title LIKE ? OR control_description LIKE ?
            """,
                (search_pattern, search_pattern),
            )
            control_results = cursor.fetchall()

            # Combine results
            all_results = list(risk_results) + list(control_results)
            assert len(all_results) > 0

            # Verify result structure
            for result in all_results:
                assert "type" in result.keys()
                assert "id" in result.keys()
                assert "title" in result.keys()
                assert "description" in result.keys()


class TestStatisticsWorkflows:
    """Test statistics calculation workflows."""

    def test_complete_statistics_calculation(
        self, sample_database, mock_config_manager
    ):
        """Test complete statistics calculation workflow."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Count main entities
            cursor.execute("SELECT COUNT(*) FROM risks")
            total_risks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM controls")
            total_controls = cursor.fetchone()[0]

            # Count relationships
            cursor.execute("SELECT COUNT(*) FROM risk_control_mapping")
            risk_control_count = cursor.fetchone()[0]

            total_relationships = risk_control_count

            # Verify counts
            assert total_risks > 0
            assert total_controls > 0

            # Verify relationship counts are reasonable
            assert risk_control_count > 0

    def test_coverage_analysis_workflow(self, sample_database, mock_config_manager):
        """Test coverage analysis workflow."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all entities
            cursor.execute("SELECT risk_id FROM risks")
            all_risks = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT control_id FROM controls")
            all_controls = {row["control_id"] for row in cursor.fetchall()}

            # Get mapped entities
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risks = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_controls = {row["control_id"] for row in cursor.fetchall()}

            # Calculate coverage
            risk_coverage = (
                len(mapped_risks) / len(all_risks) * 100 if all_risks else 0
            )
            control_coverage = (
                len(mapped_controls) / len(all_controls) * 100
                if all_controls
                else 0
            )

            # Verify coverage calculations
            assert 0 <= risk_coverage <= 100
            assert 0 <= control_coverage <= 100

            # Verify we have some coverage
            assert risk_coverage > 0
            assert control_coverage > 0


class TestDataIntegrityWorkflows:
    """Test data integrity and validation workflows."""

    def test_foreign_key_integrity(self, sample_database, mock_config_manager):
        """Test foreign key relationships are maintained."""
        reinitialize_repositories(str(sample_database))
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Test risk-control relationships
            cursor.execute(
                """
                SELECT r.risk_id, c.control_id
                FROM risks r
                JOIN risk_control_mapping rcm ON r.risk_id = rcm.risk_id
                JOIN controls c ON c.control_id = rcm.control_id
                LIMIT 1
            """
            )
            relationship = cursor.fetchone()
            assert relationship is not None
