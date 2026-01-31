"""
Capability endpoint tests for Database Service.

Tests capability-related API endpoints for proper functionality, error handling, and response formats.
"""

import pytest
import json
import sqlite3

# Import the app
import sys

sys.path.append("/Users/cward/Devel/dashboard_zero/database-service")

# Conditional imports
try:
    from app import app, get_db_connection, validate_database
    from unittest.mock import patch
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


class TestCapabilityEndpoints:
    """Test capability-related endpoints."""

    def test_get_capabilities_success(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test successful retrieval of capabilities."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert test capability data
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Test Technical Capability",
                        "technical",
                        "Security",
                        "Test definition",
                    ),
                )
                conn.commit()

            response = test_client.get("/api/capabilities")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            capability = data[0]
            assert "capability_id" in capability
            assert "capability_name" in capability
            assert "capability_type" in capability
            assert capability["capability_id"] == "CAP.TECH.1"
            assert capability["capability_name"] == "Test Technical Capability"
            assert capability["capability_type"] == "technical"

    def test_get_capabilities_with_filters(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test capabilities endpoint with filtering."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert test data
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Technical Capability",
                        "technical",
                        "Security",
                        "Test definition",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.NONTECH.1",
                        "Non-Technical Capability",
                        "non-technical",
                        "Governance",
                        "Test definition",
                    ),
                )
                conn.commit()

            # Test filtering by type
            response = test_client.get("/api/capabilities?capability_type=technical")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["capability_type"] == "technical"

            # Test filtering by domain
            response = test_client.get("/api/capabilities?domain=Security")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["capability_domain"] == "Security"

    def test_get_capabilities_pagination(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test capabilities endpoint pagination."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert multiple test capabilities
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for i in range(5):
                    cursor.execute(
                        """
                        INSERT INTO capabilities
                        (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                        VALUES (?, ?, ?, ?, ?)
                    """,
                        (
                            f"CAP.TECH.{i}",
                            f"Test Capability {i}",
                            "technical",
                            "Security",
                            "Test definition",
                        ),
                    )
                conn.commit()

            # Test limit
            response = test_client.get("/api/capabilities?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # Test offset
            response = test_client.get("/api/capabilities?limit=2&offset=2")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_capability_by_id_success(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test successful retrieval of specific capability by ID."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert test capability
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Test Technical Capability",
                        "technical",
                        "Security",
                        "Test definition",
                    ),
                )
                conn.commit()

            response = test_client.get("/api/capabilities/CAP.TECH.1")
            assert response.status_code == 200
            data = response.json()
            assert data["capability_id"] == "CAP.TECH.1"
            assert data["capability_name"] == "Test Technical Capability"
            assert data["capability_type"] == "technical"
            assert data["capability_domain"] == "Security"

    def test_get_capability_by_id_not_found(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test capability by ID when capability doesn't exist."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/capabilities/NONEXISTENT")
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
            assert "not found" in data["detail"].lower()

    def test_get_capability_tree_success(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test successful retrieval of capability tree."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert test data with relationships
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Insert capability
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Test Technical Capability",
                        "technical",
                        "Security",
                        "Test definition",
                    ),
                )

                # Insert control
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    ("CTRL.1", "Test Control", "Test control description", "Protect"),
                )

                # Insert risk
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.1", "Test Risk", "Test risk description"),
                )

                # Insert mappings
                cursor.execute(
                    """
                    INSERT INTO capability_control_mapping
                    (capability_id, control_id)
                    VALUES (?, ?)
                """,
                    ("CAP.TECH.1", "CTRL.1"),
                )

                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.1", "CTRL.1"),
                )

                conn.commit()

            response = test_client.get("/api/capability-tree")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0

            capability_tree = data[0]
            assert "capability_id" in capability_tree
            assert "capability_name" in capability_tree
            assert "capability_type" in capability_tree
            assert "controls" in capability_tree
            assert "risks" in capability_tree
            assert isinstance(capability_tree["controls"], list)
            assert isinstance(capability_tree["risks"], list)

    def test_get_capability_tree_empty(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test capability tree when no capabilities exist."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.get("/api/capability-tree")
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 0

    def test_capabilities_database_error(self, test_client, mock_config_manager):
        """Test capabilities endpoint with database error."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.get("/api/capabilities")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_capability_by_id_database_error(self, test_client, mock_config_manager):
        """Test capability by ID endpoint with database error."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.get("/api/capabilities/CAP.TECH.1")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_capability_tree_database_error(self, test_client, mock_config_manager):
        """Test capability tree endpoint with database error."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.get("/api/capability-tree")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


class TestCapabilityStats:
    """Test capability-related statistics."""

    def test_stats_includes_capabilities(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that stats endpoint includes capability counts."""
        with patch("app.DB_PATH", str(sample_database)):
            # Insert test capability
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Test Technical Capability",
                        "technical",
                        "Security",
                        "Test definition",
                    ),
                )
                conn.commit()

            response = test_client.get("/api/stats")
            assert response.status_code == 200
            data = response.json()
            assert "total_capabilities" in data
            assert data["total_capabilities"] == 1
