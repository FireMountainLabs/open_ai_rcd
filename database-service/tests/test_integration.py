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

sys.path.append("/home/fml/dashboard_zero/database-service")

# Conditional imports
try:
    from app import app, get_db_connection, validate_database
    from unittest.mock import patch
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


class TestDatabaseOperations:
    """Test database operations and workflows."""

    def test_database_validation_success(self, sample_database, mock_config_manager):
        """Test database validation with valid database."""
        with patch("app.DB_PATH", str(sample_database)):
            result = validate_database()
            assert result is True

    def test_database_validation_missing_file(self, mock_config_manager):
        """Test database validation with missing database file."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
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

        with patch("app.DB_PATH", str(db_path)):
            result = validate_database()
            assert result is False

    def test_database_connection_context_manager(
        self, sample_database, mock_config_manager
    ):
        """Test database connection context manager."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                assert conn is not None
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM risks")
                count = cursor.fetchone()[0]
                assert count > 0

    def test_database_connection_error_handling(self, mock_config_manager):
        """Test database connection error handling."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            with pytest.raises(Exception):  # Should raise HTTPException
                with get_db_connection() as conn:
                    pass


class TestDataRetrievalWorkflows:
    """Test complete data retrieval workflows."""

    def test_complete_risk_retrieval_workflow(
        self, sample_database, mock_config_manager
    ):
        """Test complete workflow for retrieving risk data."""
        with patch("app.DB_PATH", str(sample_database)):
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

                cursor.execute(
                    """
                    SELECT q.question_id, q.question_text
                    FROM questions q
                    JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
                    WHERE qrm.risk_id = ?
                """,
                    (risk_id,),
                )
                questions = cursor.fetchall()
                assert len(questions) > 0

    def test_complete_control_retrieval_workflow(
        self, sample_database, mock_config_manager
    ):
        """Test complete workflow for retrieving control data."""
        with patch("app.DB_PATH", str(sample_database)):
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

    def test_complete_question_retrieval_workflow(
        self, sample_database, mock_config_manager
    ):
        """Test complete workflow for retrieving question data."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Test basic question retrieval
                cursor.execute("SELECT * FROM questions LIMIT 1")
                question = cursor.fetchone()
                assert question is not None

                # Test question with relationships
                question_id = question["question_id"]
                cursor.execute(
                    """
                    SELECT r.risk_id, r.risk_title
                    FROM risks r
                    JOIN question_risk_mapping qrm ON r.risk_id = qrm.risk_id
                    WHERE qrm.question_id = ?
                """,
                    (question_id,),
                )
                risks = cursor.fetchall()
                assert len(risks) > 0


class TestSearchWorkflows:
    """Test search functionality workflows."""

    def test_cross_entity_search_workflow(self, sample_database, mock_config_manager):
        """Test searching across all entities."""
        with patch("app.DB_PATH", str(sample_database)):
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

                # Search questions
                cursor.execute(
                    """
                    SELECT 'question' as type, question_id as id, question_text as title,
                           '' as description
                    FROM questions
                    WHERE question_text LIKE ?
                """,
                    (search_pattern,),
                )
                question_results = cursor.fetchall()

                # Combine results
                all_results = (
                    list(risk_results) + list(control_results) + list(question_results)
                )
                assert len(all_results) > 0

                # Verify result structure
                for result in all_results:
                    assert "type" in result.keys()
                    assert "id" in result.keys()
                    assert "title" in result.keys()
                    assert "description" in result.keys()

    def test_relationship_search_workflow(self, sample_database, mock_config_manager):
        """Test searching through relationships."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Find all relationships for a specific risk
                risk_id = "AIR.001"

                # Get associated controls
                cursor.execute(
                    """
                    SELECT c.control_id, c.control_title, 'risk_control' as relationship_type
                    FROM controls c
                    JOIN risk_control_mapping rcm ON c.control_id = rcm.control_id
                    WHERE rcm.risk_id = ?
                """,
                    (risk_id,),
                )
                control_relationships = cursor.fetchall()

                # Get associated questions
                cursor.execute(
                    """
                    SELECT q.question_id, q.question_text, 'question_risk' as relationship_type
                    FROM questions q
                    JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
                    WHERE qrm.risk_id = ?
                """,
                    (risk_id,),
                )
                question_relationships = cursor.fetchall()

                all_relationships = list(control_relationships) + list(
                    question_relationships
                )
                assert len(all_relationships) > 0


class TestStatisticsWorkflows:
    """Test statistics calculation workflows."""

    def test_complete_statistics_calculation(
        self, sample_database, mock_config_manager
    ):
        """Test complete statistics calculation workflow."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Count main entities
                cursor.execute("SELECT COUNT(*) FROM risks")
                total_risks = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM controls")
                total_controls = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM questions")
                total_questions = cursor.fetchone()[0]

                # Count relationships
                cursor.execute("SELECT COUNT(*) FROM risk_control_mapping")
                risk_control_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
                question_risk_count = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM question_control_mapping")
                question_control_count = cursor.fetchone()[0]

                total_relationships = (
                    risk_control_count + question_risk_count + question_control_count
                )

                # Verify counts
                assert total_risks > 0
                assert total_controls > 0
                assert total_questions > 0
                assert total_relationships > 0

                # Verify relationship counts are reasonable
                assert risk_control_count > 0
                assert question_risk_count > 0
                assert question_control_count > 0

    def test_coverage_analysis_workflow(self, sample_database, mock_config_manager):
        """Test coverage analysis workflow."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Get all entities
                cursor.execute("SELECT risk_id FROM risks")
                all_risks = {row["risk_id"] for row in cursor.fetchall()}

                cursor.execute("SELECT control_id FROM controls")
                all_controls = {row["control_id"] for row in cursor.fetchall()}

                cursor.execute("SELECT question_id FROM questions")
                all_questions = {row["question_id"] for row in cursor.fetchall()}

                # Get mapped entities
                cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
                mapped_risks = {row["risk_id"] for row in cursor.fetchall()}

                cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
                mapped_controls = {row["control_id"] for row in cursor.fetchall()}

                cursor.execute("SELECT DISTINCT question_id FROM question_risk_mapping")
                mapped_questions = {row["question_id"] for row in cursor.fetchall()}

                # Add question-control mappings
                cursor.execute(
                    "SELECT DISTINCT control_id FROM question_control_mapping"
                )
                mapped_controls.update({row["control_id"] for row in cursor.fetchall()})

                cursor.execute(
                    "SELECT DISTINCT question_id FROM question_control_mapping"
                )
                mapped_questions.update(
                    {row["question_id"] for row in cursor.fetchall()}
                )

                # Calculate coverage
                risk_coverage = (
                    len(mapped_risks) / len(all_risks) * 100 if all_risks else 0
                )
                control_coverage = (
                    len(mapped_controls) / len(all_controls) * 100
                    if all_controls
                    else 0
                )
                question_coverage = (
                    len(mapped_questions) / len(all_questions) * 100
                    if all_questions
                    else 0
                )

                # Verify coverage calculations
                assert 0 <= risk_coverage <= 100
                assert 0 <= control_coverage <= 100
                assert 0 <= question_coverage <= 100

                # Verify we have some coverage
                assert risk_coverage > 0
                assert control_coverage > 0
                assert question_coverage > 0


class TestDataIntegrityWorkflows:
    """Test data integrity and validation workflows."""

    def test_foreign_key_integrity(self, sample_database, mock_config_manager):
        """Test foreign key relationships are maintained."""
        with patch("app.DB_PATH", str(sample_database)):
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

                # Test question-risk relationships
                cursor.execute(
                    """
                    SELECT q.question_id, r.risk_id
                    FROM questions q
                    JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
                    JOIN risks r ON r.risk_id = qrm.risk_id
                    LIMIT 1
                """
                )
                relationship = cursor.fetchone()
                assert relationship is not None

                # Test question-control relationships
                cursor.execute(
                    """
                    SELECT q.question_id, c.control_id
                    FROM questions q
                    JOIN question_control_mapping qcm ON q.question_id = qcm.question_id
                    JOIN controls c ON c.control_id = qcm.control_id
                    LIMIT 1
                """
                )
                relationship = cursor.fetchone()
                assert relationship is not None

    def test_data_consistency_workflow(self, sample_database, mock_config_manager):
        """Test data consistency across tables."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Verify all risk IDs in mappings exist in risks table
                cursor.execute(
                    """
                    SELECT DISTINCT rcm.risk_id
                    FROM risk_control_mapping rcm
                    LEFT JOIN risks r ON r.risk_id = rcm.risk_id
                    WHERE r.risk_id IS NULL
                """
                )
                orphaned_risks = cursor.fetchall()
                assert len(orphaned_risks) == 0

                # Verify all control IDs in mappings exist in controls table
                cursor.execute(
                    """
                    SELECT DISTINCT rcm.control_id
                    FROM risk_control_mapping rcm
                    LEFT JOIN controls c ON c.control_id = rcm.control_id
                    WHERE c.control_id IS NULL
                """
                )
                orphaned_controls = cursor.fetchall()
                assert len(orphaned_controls) == 0

                # Verify all question IDs in mappings exist in questions table
                cursor.execute(
                    """
                    SELECT DISTINCT qrm.question_id
                    FROM question_risk_mapping qrm
                    LEFT JOIN questions q ON q.question_id = qrm.question_id
                    WHERE q.question_id IS NULL
                """
                )
                orphaned_questions = cursor.fetchall()
                assert len(orphaned_questions) == 0


class TestPerformanceWorkflows:
    """Test performance-related workflows."""

    def test_large_query_performance(self, sample_database, mock_config_manager):
        """Test performance with larger queries."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Test complex join query performance
                start_time = time.time()
                cursor.execute(
                    """
                    SELECT
                        r.risk_id,
                        r.risk_title,
                        COUNT(DISTINCT rcm.control_id) as control_count,
                        COUNT(DISTINCT qrm.question_id) as question_count
                    FROM risks r
                    LEFT JOIN risk_control_mapping rcm ON r.risk_id = rcm.risk_id
                    LEFT JOIN question_risk_mapping qrm ON r.risk_id = qrm.risk_id
                    GROUP BY r.risk_id, r.risk_title
                    ORDER BY r.risk_id
                """
                )
                results = cursor.fetchall()
                end_time = time.time()

                # Verify query completed in reasonable time
                assert (
                    end_time - start_time
                ) < 1.0  # Should complete in under 1 second
                assert len(results) > 0

                # Verify result structure
                for result in results:
                    assert "risk_id" in result.keys()
                    assert "risk_title" in result.keys()
                    assert "control_count" in result.keys()
                    assert "question_count" in result.keys()

    def test_pagination_performance(self, sample_database, mock_config_manager):
        """Test pagination performance."""
        with patch("app.DB_PATH", str(sample_database)):
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Test pagination with different limits
                for limit in [1, 5, 10, 100]:
                    start_time = time.time()
                    cursor.execute("SELECT * FROM risks LIMIT ? OFFSET 0", (limit,))
                    results = cursor.fetchall()
                    end_time = time.time()

                    # Verify pagination works and is fast
                    assert len(results) <= limit
                    assert (end_time - start_time) < 0.1  # Should be very fast
