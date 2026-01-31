"""Tests for control selections functionality in scenarios."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from api.capability_scenarios import (
    ControlSelection,
    CapabilityScenarioUpdate,
    db_manager
)
    from db.connections import DatabaseManager
except ImportError:
    # If import fails, skip tests (for environments without FastAPI)
    pytest.skip("capability_scenarios module not available", allow_module_level=True)


@pytest.mark.unit
class TestControlSelections:
    """Test control selections CRUD operations and deduplication."""

    def test_save_control_selections_with_duplicates_raises_error(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that duplicate control selections raise UNIQUE constraint error."""
        # Create a new db_manager with the test database path
        test_db_manager = DatabaseManager(str(sample_database), str(sample_database))
        test_db_manager.init_capability_config_db()
        
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Control Selections",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Try to save duplicate control selections (should fail with UNIQUE constraint)
            update_data = {
                "control_selections": [
                    {"control_id": "CTRL.001", "is_active": True},
                    {"control_id": "CTRL.001", "is_active": False}  # Duplicate
                ]
            }
            
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=update_data
            )
            # Should fail with integrity error
            assert response.status_code == 500
            assert "UNIQUE constraint" in response.json()["detail"] or "Integrity" in response.json()["detail"]

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_save_control_selections_without_duplicates_succeeds(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that non-duplicate control selections save successfully."""
        # Create a new db_manager with the test database path
        test_db_manager = DatabaseManager(str(sample_database), str(sample_database))
        test_db_manager.init_capability_config_db()
        
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Control Selections Valid",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Save unique control selections
            update_data = {
                "control_selections": [
                    {"control_id": "CTRL.001", "is_active": True},
                    {"control_id": "CTRL.002", "is_active": False},
                    {"control_id": "CTRL.003", "is_active": True}
                ]
            }
            
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=update_data
            )
            assert response.status_code == 200

            # Verify control selections were saved
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            scenario = response.json()
            
            assert "control_selections" in scenario
            assert len(scenario["control_selections"]) == 3
            
            # Verify individual selections
            ctrl1 = next((c for c in scenario["control_selections"] if c["control_id"] == "CTRL.001"), None)
            ctrl2 = next((c for c in scenario["control_selections"] if c["control_id"] == "CTRL.002"), None)
            ctrl3 = next((c for c in scenario["control_selections"] if c["control_id"] == "CTRL.003"), None)
            
            assert ctrl1 is not None
            assert ctrl1["is_active"] == True
            assert ctrl2 is not None
            assert ctrl2["is_active"] == False
            assert ctrl3 is not None
            assert ctrl3["is_active"] == True

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_update_control_selections_replaces_existing(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that updating control selections replaces existing ones."""
        # Create a new db_manager with the test database path
        test_db_manager = DatabaseManager(str(sample_database), str(sample_database))
        test_db_manager.init_capability_config_db()
        
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Control Update",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Save initial control selections
            initial_data = {
                "control_selections": [
                    {"control_id": "CTRL.001", "is_active": True},
                    {"control_id": "CTRL.002", "is_active": True}
                ]
            }
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=initial_data
            )
            assert response.status_code == 200

            # Update with different selections
            update_data = {
                "control_selections": [
                    {"control_id": "CTRL.003", "is_active": False},
                    {"control_id": "CTRL.004", "is_active": True}
                ]
            }
            response = test_client.put(
                f"/api/capability-scenarios/{scenario_id}",
                json=update_data
            )
            assert response.status_code == 200

            # Verify old selections are gone and new ones are present
            response = test_client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            scenario = response.json()
            
            assert len(scenario["control_selections"]) == 2
            control_ids = {c["control_id"] for c in scenario["control_selections"]}
            assert "CTRL.001" not in control_ids
            assert "CTRL.002" not in control_ids
            assert "CTRL.003" in control_ids
            assert "CTRL.004" in control_ids

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_control_selections_with_invalid_data_raises_error(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test that invalid control selection data raises validation error."""
        # Create a new db_manager with the test database path
        test_db_manager = DatabaseManager(str(sample_database), str(sample_database))
        test_db_manager.init_capability_config_db()
        
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Invalid Control",
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
            # Should fail with validation error
            assert response.status_code in [422, 500]

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_control_selections_with_capability_selections(
        self, test_client, sample_database, mock_config_manager
    ):
        """Test saving both capability and control selections together."""
        # Create a new db_manager with the test database path
        test_db_manager = DatabaseManager(str(sample_database), str(sample_database))
        test_db_manager.init_capability_config_db()
        
        with patch("app.DB_PATH", str(sample_database)), \
             patch("app.CAPABILITY_CONFIG_DB_PATH", str(sample_database)), \
             patch("api.capability_scenarios.db_manager", test_db_manager):
            # Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Combined Selections",
                "is_default": False
            }
            response = test_client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario_id = response.json()["scenario_id"]

            # Save both capability and control selections
            update_data = {
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False}
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
            
            assert len(scenario["selections"]) == 2
            assert len(scenario["control_selections"]) == 2

            # Clean up
            test_client.delete(f"/api/capability-scenarios/{scenario_id}")

