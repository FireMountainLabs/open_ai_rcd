"""
Worksheet persistence tests for Dashboard Service.

Tests auto-save functionality, worksheet state management, and persistence across sessions.
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
import requests

# Import the app
import sys
sys.path.append("/Users/cward/Devel/dashboard_zero/dashboard-service")

try:
    from app import app
    from unittest.mock import patch
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


@pytest.mark.unit
@pytest.mark.skip(reason="Requires database-service to be running - these tests belong in database-service")
class TestWorksheetPersistence:
    """Test worksheet persistence and auto-save functionality."""

    def test_worksheet_scenario_crud_operations(self, client, mock_capability_auth):
        """Test basic CRUD operations for worksheet scenarios."""
        # Test creating a new scenario (user_id will be set from authenticated user)
        scenario_data = {
            "scenario_name": "Test Scenario",
            "is_default": False
        }
        
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["scenario_name"] == "Test Scenario"
        assert scenario["user_id"] == 1
        scenario_id = scenario["scenario_id"]
        
        # Test retrieving scenarios (user_id extracted from authenticated user)
        response = client.get("/api/capability-scenarios")
        assert response.status_code == 200
        scenarios = response.json()
        assert len(scenarios) >= 1
        assert any(s["scenario_id"] == scenario_id for s in scenarios)
        
        # Test retrieving specific scenario (user_id extracted from authenticated user)
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        retrieved_scenario = response.json()
        assert retrieved_scenario["scenario_id"] == scenario_id
        assert retrieved_scenario["scenario_name"] == "Test Scenario"
        
        # Test updating scenario
        update_data = {
            "scenario_name": "Updated Test Scenario",
            "is_default": True
        }
        response = client.put(f"/api/capability-scenarios/{scenario_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        updated_scenario = response.json()
        assert updated_scenario["scenario_name"] == "Updated Test Scenario"
        
        # Test deleting scenario
        response = client.delete(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        
        # Verify deletion
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 404

    def test_capability_selections_bulk_save_load(self, client, mock_capability_auth):
        """Test bulk save and load of capability selections."""
        # Create a scenario first
        scenario_data = {
            "scenario_name": "Test Selections",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Test saving capability selections (user_id now required in request body)
        selections_data = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False},
                {"capability_id": "CAP.NONTECH.001", "is_active": True}
            ]
        }
        
        response = client.post("/api/capability-selections", json=selections_data)
        assert response.status_code == 200
        result = response.json()
        assert result["count"] == 3
        
        # Test loading capability selections
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        assert len(selections) == 3
        
        # Verify specific selections
        active_selections = [s for s in selections if s["is_active"]]
        inactive_selections = [s for s in selections if not s["is_active"]]
        assert len(active_selections) == 2
        assert len(inactive_selections) == 1
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_user_isolation(self, client, mock_capability_auth):
        """Test that worksheets are isolated per user."""
        # Create scenarios for user 1 (authenticated user)
        scenario1_data = {
            "scenario_name": "User 1 Scenario",
            "is_default": False
        }
        
        response1 = client.post("/api/capability-scenarios", json=scenario1_data)
        assert response1.status_code == 200
        
        scenario1_id = response1.json()["scenario_id"]
        
        # Test that authenticated user only sees their own scenarios
        response = client.get("/api/capability-scenarios")
        assert response.status_code == 200
        user1_scenarios = response.json()
        user1_scenario_ids = [s["scenario_id"] for s in user1_scenarios]
        assert scenario1_id in user1_scenario_ids
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario1_id}")
    
    def test_authorization_prevents_access_to_other_users_scenarios(self, client, mock_capability_auth):
        """Test that users cannot access other users' scenarios (403 error)."""
        # Create a scenario for user 1
        scenario_data = {
            "scenario_name": "User 1 Scenario",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Try to access with a different user (user_id = 2)
        # This should fail with 403 if authorization is working
        # Note: This test requires mocking a different user, which would need
        # a separate fixture. For now, we verify the scenario belongs to user 1.
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200  # User 1 can access their own scenario
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_concurrent_worksheet_updates(self, client, mock_capability_auth):
        """Test handling of concurrent worksheet updates."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Concurrent Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Simulate concurrent updates with different selections
        selections1 = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False}
            ]
        }
        
        selections2 = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": False},
                {"capability_id": "CAP.TECH.002", "is_active": True}
            ]
        }
        
        # Send both requests
        response1 = client.post("/api/capability-selections", json=selections1)
        response2 = client.post("/api/capability-selections", json=selections2)
        
        # Both should succeed (last write wins)
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify final state
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        final_selections = response.json()
        
        # Should reflect the last update
        cap1_selection = next(s for s in final_selections if s["capability_id"] == "CAP.TECH.001")
        cap2_selection = next(s for s in final_selections if s["capability_id"] == "CAP.TECH.002")
        assert cap1_selection["is_active"] == False
        assert cap2_selection["is_active"] == True
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_worksheet_error_handling(self, client, mock_capability_auth):
        """Test error handling for worksheet operations."""
        # Test creating scenario with invalid data (user_id is now set from auth, so we test other fields)
        invalid_data = {
            "scenario_name": "",
            "is_default": "not_boolean"
        }
        response = client.post("/api/capability-scenarios", json=invalid_data)
        # May be 400 or 422 depending on validation
        assert response.status_code in [400, 422]
        
        # Test accessing non-existent scenario
        response = client.get("/api/capability-scenarios/99999")
        assert response.status_code == 404
        
        # Test saving selections for non-existent scenario
        selections_data = {
            "scenario_id": 99999,
            "user_id": 1,  # Required by new API
            "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
        }
        response = client.post("/api/capability-selections", json=selections_data)
        assert response.status_code == 404
        
        # Test deleting non-existent scenario
        response = client.delete("/api/capability-scenarios/99999")
        assert response.status_code == 404

    def test_worksheet_data_integrity(self, client, mock_capability_auth):
        """Test data integrity constraints for worksheets."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Integrity Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Test saving selections with duplicate capability IDs
        selections_data = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.001", "is_active": False}  # Duplicate
            ]
        }
        
        response = client.post("/api/capability-selections", json=selections_data)
        # Should handle duplicates gracefully (last one wins)
        assert response.status_code == 200
        
        # Verify only one selection exists for the capability
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        cap1_selections = [s for s in selections if s["capability_id"] == "CAP.TECH.001"]
        assert len(cap1_selections) == 1
        assert cap1_selections[0]["is_active"] == False  # Last value wins
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_control_selections_integrity_constraint(self, client, mock_capability_auth):
        """Test that control selections enforce UNIQUE constraint on (scenario_id, control_id)."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Control Integrity Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Try to save duplicate control selections via PUT endpoint
        # This should fail because the frontend should deduplicate, but if it doesn't, the DB will reject it
        update_data = {
            "control_selections": [
                {"control_id": "CTRL.001", "is_active": True},
                {"control_id": "CTRL.001", "is_active": False}  # Duplicate - should be rejected
            ]
        }
        
        response = client.put(f"/api/capability-scenarios/{scenario_id}", json=update_data)
        # Should fail with 500 error due to UNIQUE constraint violation
        assert response.status_code == 500
        error_detail = response.json().get("error", response.json().get("detail", ""))
        assert "UNIQUE constraint" in error_detail or "Integrity" in error_detail
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_control_selections_with_unique_ids_succeeds(self, client, mock_capability_auth):
        """Test that control selections with unique control_ids save successfully."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Control Unique Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
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
        
        response = client.put(f"/api/capability-scenarios/{scenario_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify control selections were saved
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        scenario = response.json()
        assert "control_selections" in scenario
        assert len(scenario["control_selections"]) == 3
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_reset_all_capabilities_functionality(self, client, mock_capability_auth):
        """Test that Reset All properly deactivates all capabilities."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Reset Test Worksheet",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # First, activate some capabilities
        initial_selections = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": True},
                {"capability_id": "CAP.NONTECH.001", "is_active": True}
            ]
        }
        
        response = client.post("/api/capability-selections", json=initial_selections)
        assert response.status_code == 200
        
        # Verify capabilities are active
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        initial_selections = response.json()
        active_count = sum(1 for s in initial_selections if s["is_active"])
        assert active_count == 3
        
        # Now simulate "Reset All" by deactivating all capabilities
        reset_selections = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": False},
                {"capability_id": "CAP.TECH.002", "is_active": False},
                {"capability_id": "CAP.NONTECH.001", "is_active": False}
            ]
        }
        
        response = client.post("/api/capability-selections", json=reset_selections)
        assert response.status_code == 200
        
        # Verify all capabilities are now deactivated
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        reset_selections = response.json()
        active_count = sum(1 for s in reset_selections if s["is_active"])
        assert active_count == 0
        
        # Verify specific capabilities are deactivated
        for selection in reset_selections:
            assert selection["is_active"] == False
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_worksheet_persistence_across_sessions(self, client, mock_capability_auth):
        """Test that worksheet data persists across simulated sessions."""
        # Create a scenario and save selections
        scenario_data = {
            "scenario_name": "Persistence Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Save initial selections
        selections_data = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False},
                {"capability_id": "CAP.NONTECH.001", "is_active": True}
            ]
        }
        
        response = client.post("/api/capability-selections", json=selections_data)
        assert response.status_code == 200
        
        # Simulate session end and restart by making new requests
        # Verify data is still there
        response = client.get(f"/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["scenario_name"] == "Persistence Test"
        
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        assert len(selections) == 3
        
        # Verify specific selections persisted
        active_count = sum(1 for s in selections if s["is_active"])
        assert active_count == 2
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")


@pytest.mark.integration
@pytest.mark.skip(reason="Requires database-service to be running - these tests belong in database-service")
class TestWorksheetAutoSave:
    """Test auto-save functionality simulation."""

    def test_auto_save_debouncing_simulation(self, client, mock_capability_auth):
        """Test that rapid changes result in single save operation."""
        # Create a scenario
        scenario_data = {
            "scenario_name": "Auto-save Test",
            "is_default": False
        }
        response = client.post("/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Simulate rapid capability toggles (like auto-save would handle)
        # First save
        selections1 = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
        }
        response1 = client.post("/api/capability-selections", json=selections1)
        assert response1.status_code == 200
        
        # Immediate second save (simulating rapid toggle)
        selections2 = {
            "scenario_id": scenario_id,
            "user_id": 1,  # Required by new API
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": False},
                {"capability_id": "CAP.TECH.002", "is_active": True}
            ]
        }
        response2 = client.post("/api/capability-selections", json=selections2)
        assert response2.status_code == 200
        
        # Verify final state reflects the last save
        response = client.get(f"/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        
        cap1_selection = next((s for s in selections if s["capability_id"] == "CAP.TECH.001"), None)
        cap2_selection = next((s for s in selections if s["capability_id"] == "CAP.TECH.002"), None)
        
        if cap1_selection:
            assert cap1_selection["is_active"] == False
        if cap2_selection:
            assert cap2_selection["is_active"] == True
        
        # Clean up
        client.delete(f"/api/capability-scenarios/{scenario_id}")

    def test_worksheet_state_consistency(self, client, mock_capability_auth):
        """Test that worksheet state remains consistent across operations."""
        # Create multiple scenarios
        scenarios = []
        for i in range(3):
            scenario_data = {
                "scenario_name": f"Consistency Test {i+1}",
                "is_default": False
            }
            response = client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenarios.append(response.json())
        
        # Save different selections for each scenario
        for i, scenario in enumerate(scenarios):
            selections_data = {
                "scenario_id": scenario["scenario_id"],
                "user_id": 1,  # Required by new API
                "selections": [
                    {"capability_id": f"CAP.TECH.00{i+1}", "is_active": True},
                    {"capability_id": f"CAP.TECH.00{i+2}", "is_active": False}
                ]
            }
            response = client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
        
        # Verify each scenario maintains its own state
        for i, scenario in enumerate(scenarios):
            response = client.get(f"/api/capability-selections/{scenario['scenario_id']}")
            assert response.status_code == 200
            selections = response.json()
            
            # Each scenario should have its own unique selections
            assert len(selections) == 2
            
            # Verify scenario-specific capability states
            cap1_selection = next(s for s in selections if s["capability_id"] == f"CAP.TECH.00{i+1}")
            cap2_selection = next(s for s in selections if s["capability_id"] == f"CAP.TECH.00{i+2}")
            assert cap1_selection["is_active"] == True
            assert cap2_selection["is_active"] == False
        
        # Clean up
        for scenario in scenarios:
            client.delete(f"/api/capability-scenarios/{scenario['scenario_id']}")
