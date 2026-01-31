"""
Capability analysis endpoint tests for Database Service.

Tests the enhanced capability analysis endpoint with detailed lists for modal display.
"""

import pytest

# Import the app
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Conditional imports
try:
    from app import get_db_connection
    from unittest.mock import patch
    from db.connections import DatabaseManager
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


class TestCapabilityAnalysis:
    """Test capability analysis endpoint with detailed lists."""

    def test_analyze_capabilities_empty_list(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test capability analysis with empty capability_ids list."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Insert test data
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

                # Insert controls
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.1",
                        "Test Control 1",
                        "Test control description 1",
                        "Protect",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.2",
                        "Test Control 2",
                        "Test control description 2",
                        "Detect",
                    ),
                )

                # Insert risks
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.1", "Test Risk 1", "Test risk description 1"),
                )
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.2", "Test Risk 2", "Test risk description 2"),
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
                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.2", "CTRL.2"),
                )

                conn.commit()

            # Test with empty capability_ids
            response = test_client.post(
                "/api/capability-analysis", json={"capability_ids": []}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify summary metrics
            assert data["total_controls"] >= 2  # At least our test controls
            assert data["controls_in_capabilities"] >= 1  # At least our test control
            assert data["active_controls"] == 0
            assert (
                data["exposed_risks"] >= 2
            )  # All risks exposed when no controls active
            assert data["total_risks"] >= 2
            assert data["active_risks"] == 0
            assert data["partially_covered_risks"] == 0

            # Verify detailed lists
            assert "active_controls_list" in data
            assert "partially_covered_risks_list" in data
            assert "exposed_risks_list" in data

            assert len(data["active_controls_list"]) == 0
            assert len(data["partially_covered_risks_list"]) == 0
            assert len(data["exposed_risks_list"]) >= 2

            # Verify exposed risks list contains all risks
            exposed_risk_ids = [risk["risk_id"] for risk in data["exposed_risks_list"]]
            assert "RISK.1" in exposed_risk_ids
            assert "RISK.2" in exposed_risk_ids

    def test_analyze_capabilities_with_active_capabilities(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test capability analysis with active capabilities."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Insert test data
            with get_db_connection() as conn:
                cursor = conn.cursor()

                # Insert capabilities
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.1",
                        "Test Technical Capability 1",
                        "technical",
                        "Security",
                        "Test definition 1",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO capabilities
                    (capability_id, capability_name, capability_type, capability_domain, capability_definition)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        "CAP.TECH.2",
                        "Test Technical Capability 2",
                        "technical",
                        "Security",
                        "Test definition 2",
                    ),
                )

                # Insert controls
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.1",
                        "Test Control 1",
                        "Test control description 1",
                        "Protect",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.2",
                        "Test Control 2",
                        "Test control description 2",
                        "Detect",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.3",
                        "Test Control 3",
                        "Test control description 3",
                        "Respond",
                    ),
                )

                # Insert risks
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.1", "Test Risk 1", "Test risk description 1"),
                )
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.2", "Test Risk 2", "Test risk description 2"),
                )
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.3", "Test Risk 3", "Test risk description 3"),
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
                    INSERT INTO capability_control_mapping
                    (capability_id, control_id)
                    VALUES (?, ?)
                """,
                    ("CAP.TECH.1", "CTRL.2"),
                )
                cursor.execute(
                    """
                    INSERT INTO capability_control_mapping
                    (capability_id, control_id)
                    VALUES (?, ?)
                """,
                    ("CAP.TECH.2", "CTRL.2"),
                )

                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.1", "CTRL.1"),
                )
                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.2", "CTRL.2"),
                )
                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.3", "CTRL.3"),
                )

                conn.commit()

            # Test with active capabilities
            response = test_client.post(
                "/api/capability-analysis",
                json={"capability_ids": ["CAP.TECH.1", "CAP.TECH.2"]},
            )
            assert response.status_code == 200
            data = response.json()

            # Verify summary metrics
            assert data["total_controls"] >= 3  # At least our test controls
            assert data["controls_in_capabilities"] >= 2  # At least our test controls
            assert data["active_controls"] >= 2  # CTRL.1, CTRL.2 (duplicate CTRL.2)
            assert data["total_risks"] >= 3

            # Verify detailed lists
            assert "active_controls_list" in data
            assert "partially_covered_risks_list" in data
            assert "exposed_risks_list" in data

            # Verify active controls list
            assert len(data["active_controls_list"]) >= 2
            active_control_ids = [
                ctrl["control_id"] for ctrl in data["active_controls_list"]
            ]
            assert "CTRL.1" in active_control_ids
            assert "CTRL.2" in active_control_ids

            # Verify exposed risks list (RISK.3 should be exposed as CTRL.3 is not active)
            exposed_risk_ids = [risk["risk_id"] for risk in data["exposed_risks_list"]]
            assert "RISK.3" in exposed_risk_ids

    def test_analyze_capabilities_invalid_capability_ids(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test capability analysis with invalid capability IDs."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Insert minimal test data
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

            # Test with invalid capability IDs
            response = test_client.post(
                "/api/capability-analysis",
                json={"capability_ids": ["INVALID.1", "INVALID.2"]},
            )
            assert response.status_code == 200
            data = response.json()

            # Should return metrics as if no capabilities are active
            assert data["active_controls"] == 0
            assert data["active_risks"] == 0
            assert len(data["active_controls_list"]) == 0
            assert len(data["partially_covered_risks_list"]) == 0

    def test_analyze_capabilities_missing_request_body(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test capability analysis with missing request body."""
        with patch("app.DB_PATH", str(sample_database)):
            response = test_client.post("/api/capability-analysis")
            assert response.status_code == 422  # Validation error

    def test_analyze_capabilities_database_error(
        self, test_client, mock_config_manager
    ):
        """Test capability analysis with database error."""
        with patch("app.DB_PATH", "/nonexistent/database.db"):
            response = test_client.post(
                "/api/capability-analysis", json={"capability_ids": []}
            )
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_analyze_capabilities_partially_covered_risks(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test capability analysis with partially covered risks."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Insert test data with partially covered risks
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

                # Insert controls
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.1",
                        "Test Control 1",
                        "Test control description 1",
                        "Protect",
                    ),
                )
                cursor.execute(
                    """
                    INSERT INTO controls
                    (control_id, control_title, control_description, security_function)
                    VALUES (?, ?, ?, ?)
                """,
                    (
                        "CTRL.2",
                        "Test Control 2",
                        "Test control description 2",
                        "Detect",
                    ),
                )

                # Insert risk that requires both controls
                cursor.execute(
                    """
                    INSERT INTO risks
                    (risk_id, risk_title, risk_description)
                    VALUES (?, ?, ?)
                """,
                    ("RISK.1", "Test Risk 1", "Test risk description 1"),
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

                # Risk requires both controls, but only CTRL.1 is active
                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.1", "CTRL.1"),
                )
                cursor.execute(
                    """
                    INSERT INTO risk_control_mapping
                    (risk_id, control_id)
                    VALUES (?, ?)
                """,
                    ("RISK.1", "CTRL.2"),
                )

                conn.commit()

            # Test with one active capability (only CTRL.1 active)
            response = test_client.post(
                "/api/capability-analysis", json={"capability_ids": ["CAP.TECH.1"]}
            )
            assert response.status_code == 200
            data = response.json()

            # Verify partially covered risks
            assert data["partially_covered_risks"] == 1
            assert len(data["partially_covered_risks_list"]) == 1
            assert data["partially_covered_risks_list"][0]["risk_id"] == "RISK.1"


class TestWorksheetCRUD:
    """Test worksheet scenario CRUD operations and capability selections."""

    def test_create_capability_scenario(
        self, test_client, sample_database, mock_config_manager, test_db_manager
    ):
        """Test creating a new capability scenario."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Scenario",
                "is_default": False
            }
            
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            data = response.json()
            
            assert "scenario_id" in data
            assert data["user_id"] == 1
            assert data["scenario_name"] == "Test Scenario"
            assert data["is_default"] == False
            assert "created_at" in data
            
            # Clean up
            test_client.delete(f"/api/capability-scenarios/{data['scenario_id']}")

    def test_create_duplicate_scenario_name_fails(
        self, test_client, sample_database, mock_config_manager, test_db_manager
    ):
        """Test that creating a scenario with a duplicate name for the same user fails with descriptive error."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            scenario_name = "Duplicate Test Scenario"
            scenario_data = {
                "user_id": 1,
                "scenario_name": scenario_name,
                "is_default": False
            }
            
            # Create first scenario
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            first_scenario = response.json()
            scenario_id = first_scenario["scenario_id"]
            
            # Try to create duplicate scenario with same name for same user
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 400
            error_data = response.json()
            assert "detail" in error_data
            error_detail = error_data["detail"]
            
            # Verify descriptive error message includes scenario name
            assert scenario_name in error_detail
            assert "already exists" in error_detail.lower()
            assert "Please choose a different name" in error_detail
            
            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_create_same_scenario_name_different_users_succeeds(
        self, test_client, sample_database, mock_config_manager, test_db_manager
    ):
        """Test that creating scenarios with the same name for different users succeeds."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            scenario_name = "Shared Scenario Name"
            
            # Create scenario for user 1
            scenario_data_1 = {
                "user_id": 1,
                "scenario_name": scenario_name,
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data_1)
            assert response.status_code == 200
            scenario_1 = response.json()
            
            # Create scenario with same name for user 2 (should succeed)
            scenario_data_2 = {
                "user_id": 2,
                "scenario_name": scenario_name,
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data_2)
            assert response.status_code == 200
            scenario_2 = response.json()
            
            # Verify both scenarios exist and have same name
            assert scenario_1["scenario_name"] == scenario_name
            assert scenario_2["scenario_name"] == scenario_name
            assert scenario_1["user_id"] == 1
            assert scenario_2["user_id"] == 2
            
            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_1['scenario_id']}")
            test_client.delete(f"/api/capability-scenarios/{scenario_2['scenario_id']}")

    def test_get_capability_scenarios(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test retrieving capability scenarios for a user."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create test scenarios
            scenarios_data = [
                {"user_id": 1, "scenario_name": "Scenario 1", "is_default": False},
                {"user_id": 1, "scenario_name": "Scenario 2", "is_default": True},
                {"user_id": 2, "scenario_name": "User 2 Scenario", "is_default": False}
            ]
            
            created_scenarios = []
            for scenario_data in scenarios_data:
                response = test_client.post("/api/capability-scenarios", json=scenario_data)
                assert response.status_code == 200
                created_scenarios.append(response.json())
            
            # Test retrieving scenarios for user 1
            response = test_client.get("/api/capability-scenarios?user_id=1")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2  # Only user 1's scenarios
            scenario_names = [s["scenario_name"] for s in data]
            assert "Scenario 1" in scenario_names
            assert "Scenario 2" in scenario_names
            assert "User 2 Scenario" not in scenario_names
            
            # Test retrieving scenarios for user 2
            response = test_client.get("/api/capability-scenarios?user_id=2")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 1
            assert data[0]["scenario_name"] == "User 2 Scenario"

    def test_get_capability_scenario_with_selections(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test retrieving a specific scenario with its selections."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Scenario with Selections",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario = response.json()
            scenario_id = scenario["scenario_id"]
            
            # Add capability selections
            selections_data = {
                "scenario_id": scenario_id,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False}
                ]
            }
            response = test_client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
            
            # Retrieve scenario with selections
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            data = response.json()
            
            assert data["scenario_id"] == scenario_id
            assert data["scenario_name"] == "Test Scenario with Selections"
            assert "selections" in data
            assert len(data["selections"]) == 2
            
            # Verify selections
            active_selections = [s for s in data["selections"] if s["is_active"]]
            inactive_selections = [s for s in data["selections"] if not s["is_active"]]
            assert len(active_selections) == 1
            assert len(inactive_selections) == 1
            assert active_selections[0]["capability_id"] == "CAP.TECH.001"
            assert inactive_selections[0]["capability_id"] == "CAP.TECH.002"

    def test_update_capability_scenario(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test updating a capability scenario."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Original Name",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]
            
            # Update scenario
            update_data = {
                "scenario_name": "Updated Name",
                "is_default": True
            }
            response = test_client.put(f"/api/capability-scenarios/{scenario_id}", json=update_data)
            assert response.status_code == 200
            
            # Verify update
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            data = response.json()
            
            assert data["scenario_name"] == "Updated Name"
            assert data["is_default"] == True

    def test_delete_capability_scenario(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test deleting a capability scenario."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "To Be Deleted",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]
            
            # Add selections
            selections_data = {
                "scenario_id": scenario_id,
                "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
            }
            response = test_client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
            
            # Verify scenario exists
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            
            # Delete scenario
            response = test_client.delete(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            
            # Verify scenario is deleted
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 404
            
            # Verify selections are also deleted
            response = test_client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 404

    def test_save_capability_selections_bulk(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test bulk saving of capability selections."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Bulk Selections Test",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]
            
            # Save bulk selections
            selections_data = {
                "scenario_id": scenario_id,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False},
                    {"capability_id": "CAP.NONTECH.001", "is_active": True},
                    {"capability_id": "CAP.NONTECH.002", "is_active": False}
                ]
            }
            
            response = test_client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
            data = response.json()
            
            assert data["count"] == 4
            
            # Verify selections were saved
            response = test_client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 200
            selections = response.json()
            
            assert len(selections) == 4
            active_count = sum(1 for s in selections if s["is_active"])
            assert active_count == 2

    def test_get_capability_selections(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test retrieving capability selections for a scenario."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Selections Retrieval Test",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]
            
            # Save selections
            selections_data = {
                "scenario_id": scenario_id,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False}
                ]
            }
            response = test_client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
            
            # Retrieve selections
            response = test_client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 200
            data = response.json()
            
            assert len(data) == 2
            assert all("capability_id" in s for s in data)
            assert all("is_active" in s for s in data)
            
            # Verify specific selections
            cap1_selection = next(s for s in data if s["capability_id"] == "CAP.TECH.001")
            cap2_selection = next(s for s in data if s["capability_id"] == "CAP.TECH.002")
            assert cap1_selection["is_active"] == True
            assert cap2_selection["is_active"] == False

    def test_worksheet_error_handling(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test error handling for worksheet operations."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Test creating scenario with invalid data
            invalid_scenario = {
                "user_id": "invalid",
                "scenario_name": "",
                "is_default": "not_boolean"
            }
            response = test_client.post("/api/capability-scenarios", json=invalid_scenario)
            assert response.status_code == 422
            
            # Test accessing non-existent scenario
            response = test_client.get("/api/capability-scenarios/99999")
            assert response.status_code == 404
            
            # Test saving selections for non-existent scenario
            selections_data = {
                "scenario_id": 99999,
                "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
            }
            response = test_client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 404
            
            # Test invalid selections format
            invalid_selections = {
                "scenario_id": 1,
                "selections": "not_a_list"
            }
            response = test_client.post("/api/capability-selections", json=invalid_selections)
            assert response.status_code == 422

    def test_control_selections_validation_error(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test that control selections with missing control_id raise validation error."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Validation",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Try to save control selection with missing control_id
            update_data = {
                "control_selections": [
                    {"is_active": True}  # Missing control_id
                ]
            }
            
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=update_data
            )
            # Should fail with validation or error
            assert response.status_code in [422, 500]
            error_detail = response.json().get("detail", "")
            # FastAPI validation errors return detail as a list, so handle both cases
            if isinstance(error_detail, list):
                error_str = str(error_detail).lower()
            else:
                error_str = str(error_detail).lower()
            assert "control_id" in error_str or "invalid" in error_str or "field required" in error_str

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_control_selections_update_scenario_with_selections(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test updating scenario with both capability and control selections."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Combined Update",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Update with both selections
            update_data = {
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True}
                ],
                "control_selections": [
                    {"control_id": "CTRL.001", "is_active": True},
                    {"control_id": "CTRL.002", "is_active": False}
                ]
            }
            
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=update_data
            )
            assert response.status_code == 200

            # Verify both are saved
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            scenario = response.json()
            
            assert len(scenario["selections"]) == 1
            assert len(scenario["control_selections"]) == 2

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_worksheet_user_isolation(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test that worksheets are properly isolated per user."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenarios for different users
            user1_scenario = {
                "user_id": 1,
                "scenario_name": "User 1 Scenario",
                "is_default": False
            }
            user2_scenario = {
                "user_id": 2,
                "scenario_name": "User 2 Scenario",
                "is_default": False
            }
            
            response1 = test_client.post("/api/capability-scenarios", json=user1_scenario)
            response2 = test_client.post("/api/capability-scenarios", json=user2_scenario)
            
            assert response1.status_code == 200
            assert response2.status_code == 200
            
            scenario1_id = response1.json()["scenario_id"]
            scenario2_id = response2.json()["scenario_id"]
            
            # Add different selections for each user
            user1_selections = {
                "scenario_id": scenario1_id,
                "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
            }
            user2_selections = {
                "scenario_id": scenario2_id,
                "selections": [{"capability_id": "CAP.TECH.002", "is_active": True}]
            }
            
            test_client.post("/api/capability-selections", json=user1_selections)
            test_client.post("/api/capability-selections", json=user2_selections)
            
            # Verify user isolation
            response = test_client.get("/api/capability-scenarios?user_id=1")
            assert response.status_code == 200
            user1_scenarios = response.json()
            user1_scenario_ids = [s["scenario_id"] for s in user1_scenarios]
            assert scenario1_id in user1_scenario_ids
            assert scenario2_id not in user1_scenario_ids
            
            response = test_client.get("/api/capability-scenarios?user_id=2")
            assert response.status_code == 200
            user2_scenarios = response.json()
            user2_scenario_ids = [s["scenario_id"] for s in user2_scenarios]
            assert scenario2_id in user2_scenario_ids
            assert scenario1_id not in user2_scenario_ids

    def test_reset_all_capabilities_functionality_db(self, test_client, sample_database, mock_config_manager, test_db_manager):
        """Test that Reset All properly deactivates all capabilities in database."""
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create a scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Reset Test Worksheet",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]
            
            # First, activate some capabilities
            initial_selections = {
                "scenario_id": scenario_id,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": True},
                    {"capability_id": "CAP.NONTECH.001", "is_active": True}
                ]
            }
            
            response = test_client.post("/api/capability-selections", json=initial_selections)
            assert response.status_code == 200
            
            # Verify capabilities are active
            response = test_client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 200
            initial_selections = response.json()
            active_count = sum(1 for s in initial_selections if s["is_active"])
            assert active_count == 3
            
            # Now simulate "Reset All" by deactivating all capabilities
            reset_selections = {
                "scenario_id": scenario_id,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": False},
                    {"capability_id": "CAP.TECH.002", "is_active": False},
                    {"capability_id": "CAP.NONTECH.001", "is_active": False}
                ]
            }
            
            response = test_client.post("/api/capability-selections", json=reset_selections)
            assert response.status_code == 200
            
            # Verify all capabilities are now deactivated
            response = test_client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 200
            reset_selections = response.json()
            active_count = sum(1 for s in reset_selections if s["is_active"])
            assert active_count == 0
            
            # Verify specific capabilities are deactivated
            for selection in reset_selections:
                assert selection["is_active"] == False
            
            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")
