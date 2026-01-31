"""
Integration tests for risks without questions functionality.

This module tests the complete integration of the risks without questions
feature, including database operations, API responses, and data consistency.
"""

import pytest
import sqlite3
from unittest.mock import patch


@pytest.mark.integration
@pytest.mark.risks_without_questions
class TestRisksWithoutQuestionsIntegration:
    """Integration tests for risks without questions functionality."""

    def test_risks_without_questions_database_consistency(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that the risks without questions calculation is consistent with database state."""
        with patch("app.DB_PATH", str(sample_database)):
            # Get the gaps analysis
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Get raw database counts for verification
            conn = sqlite3.connect(sample_database)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Count total risks
            cursor.execute("SELECT COUNT(*) as count FROM risks")
            total_risks = cursor.fetchone()["count"]

            # Count risks with questions
            cursor.execute(
                "SELECT COUNT(DISTINCT risk_id) as count FROM question_risk_mapping"
            )
            risks_with_questions = cursor.fetchone()["count"]

            # Calculate expected risks without questions
            expected_risks_without_questions = total_risks - risks_with_questions
            expected_percentage = (
                (expected_risks_without_questions / total_risks * 100)
                if total_risks > 0
                else 0
            )

            conn.close()

            # Validate against API response
            assert data["summary"]["total_risks"] == total_risks
            assert (
                data["summary"]["risks_without_questions"]
                == expected_risks_without_questions
            )
            assert (
                abs(
                    data["summary"]["risks_without_questions_pct"] - expected_percentage
                )
                < 0.1
            )

    def test_risks_without_questions_list_accuracy(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that the risks without questions list contains only risks without questions."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Get the list of risks without questions from API
            api_risks_without_questions = {
                risk["risk_id"] for risk in data["risks_without_questions"]
            }

            # Verify against database
            conn = sqlite3.connect(sample_database)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Get all risk IDs
            cursor.execute("SELECT risk_id FROM risks")
            all_risk_ids = {row["risk_id"] for row in cursor.fetchall()}

            # Get risk IDs that have questions
            cursor.execute("SELECT DISTINCT risk_id FROM question_risk_mapping")
            risks_with_questions = {row["risk_id"] for row in cursor.fetchall()}

            # Calculate expected risks without questions
            expected_risks_without_questions = all_risk_ids - risks_with_questions

            conn.close()

            # Validate that the API response matches the database calculation
            assert api_risks_without_questions == expected_risks_without_questions

    def test_risks_without_questions_performance(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that the risks without questions calculation performs well."""
        import time

        with patch("app.DB_PATH", str(sample_database)):
            # Measure response time
            start_time = time.time()
            response = test_client.get("/api/gaps")
            end_time = time.time()

            response_time = end_time - start_time

            # Should respond within reasonable time (1 second)
            assert response_time < 1.0
            assert response.status_code == 200

            # Validate that the response contains the expected data
            data = response.json()
            assert "risks_without_questions" in data["summary"]
            assert "risks_without_questions_pct" in data["summary"]

    def test_risks_without_questions_with_empty_database(
        self, test_client, mock_config_manager
    ):
        """Test risks without questions calculation with empty database."""
        # Create a temporary empty database
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            tmp_db_path = tmp_db.name

        try:
            # Create empty database with required tables
            conn = sqlite3.connect(tmp_db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                CREATE TABLE risks (
                    risk_id TEXT,
                    risk_title TEXT,
                    risk_description TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE questions (
                    question_id TEXT,
                    question_text TEXT,
                    category TEXT,
                    topic TEXT,
                    managing_role TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE controls (
                    control_id TEXT,
                    control_title TEXT,
                    control_description TEXT,
                    mapped_risks TEXT,
                    asset_type TEXT,
                    control_type TEXT,
                    security_function TEXT,
                    maturity_level TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE question_risk_mapping (
                    question_id TEXT,
                    risk_id TEXT,
                    PRIMARY KEY (question_id, risk_id)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE risk_control_mapping (
                    risk_id TEXT,
                    control_id TEXT,
                    PRIMARY KEY (risk_id, control_id)
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE question_control_mapping (
                    question_id TEXT,
                    control_id TEXT,
                    PRIMARY KEY (question_id, control_id)
                )
            """
            )

            conn.commit()
            conn.close()

            with patch("app.DB_PATH", tmp_db_path):
                response = test_client.get("/api/gaps")
                assert response.status_code == 200
                data = response.json()

                # With empty database, should have 0 risks without questions
                assert data["summary"]["total_risks"] == 0
                assert data["summary"]["risks_without_questions"] == 0
                assert data["summary"]["risks_without_questions_pct"] == 0
                assert data["risks_without_questions"] == []

        finally:
            # Clean up temporary database
            if os.path.exists(tmp_db_path):
                os.unlink(tmp_db_path)

    def test_risks_without_questions_with_all_risks_having_questions(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test risks without questions calculation when all risks have questions."""
        with patch("app.DB_PATH", str(sample_database)):
            # First, ensure all risks have at least one question
            conn = sqlite3.connect(sample_database)
            cursor = conn.cursor()

            # Get all risks
            cursor.execute("SELECT risk_id FROM risks")
            all_risks = [row[0] for row in cursor.fetchall()]

            # Get all questions
            cursor.execute("SELECT question_id FROM questions")
            all_questions = [row[0] for row in cursor.fetchall()]

            # Create mappings for all risks to all questions (if not already exists)
            for risk_id in all_risks:
                for question_id in all_questions:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO question_risk_mapping (question_id, risk_id)
                        VALUES (?, ?)
                    """,
                        (question_id, risk_id),
                    )

            conn.commit()
            conn.close()

            # Now test the API
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Should have 0 risks without questions
            assert data["summary"]["risks_without_questions"] == 0
            assert data["summary"]["risks_without_questions_pct"] == 0
            assert data["risks_without_questions"] == []

    def test_risks_without_questions_data_integrity(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test data integrity of risks without questions response."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/gaps")
            assert response.status_code == 200
            data = response.json()

            # Validate summary data integrity
            summary = data["summary"]
            risks_without_questions = data["risks_without_questions"]

            # Count should match list length
            assert summary["risks_without_questions"] == len(risks_without_questions)

            # Percentage should be calculated correctly
            if summary["total_risks"] > 0:
                expected_pct = (
                    summary["risks_without_questions"] / summary["total_risks"]
                ) * 100
                assert abs(summary["risks_without_questions_pct"] - expected_pct) < 0.1

            # All risks in the list should have valid structure
            for risk in risks_without_questions:
                assert "risk_id" in risk
                assert "risk_title" in risk
                assert "risk_description" in risk
                assert isinstance(risk["risk_id"], str)
                assert isinstance(risk["risk_title"], str)
                # risk_description can be None or string
                assert risk["risk_description"] is None or isinstance(
                    risk["risk_description"], str
                )

            # No duplicate risk IDs
            risk_ids = [risk["risk_id"] for risk in risks_without_questions]
            assert len(risk_ids) == len(set(risk_ids))

    def test_risks_without_questions_error_handling(
        self, test_client, mock_config_manager
    ):
        """Test error handling for risks without questions calculation."""
        # Test with invalid database path
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.get("/api/gaps")
            assert response.status_code == 500

        # Test with corrupted database
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
            tmp_db_path = tmp_db.name
            # Write invalid data to make it corrupted
            tmp_db.write(b"invalid database content")

        try:
            with patch("app.DB_PATH", tmp_db_path):
                response = test_client.get("/api/gaps")
                assert response.status_code == 500

        finally:
            if os.path.exists(tmp_db_path):
                os.unlink(tmp_db_path)
