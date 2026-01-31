"""
End-to-end worksheet persistence tests using launcher --dev.

Tests complete worksheet workflows including auto-save, persistence across sessions,
and integration with the full system.
"""

import pytest
import requests
import time
import subprocess
import os
import signal
from pathlib import Path


@pytest.mark.e2e
@pytest.mark.launcher
@pytest.mark.slow
class TestWorksheetE2E:
    """End-to-end tests for worksheet functionality using launcher."""

    DASHBOARD_URL = "http://localhost:5000"
    DATABASE_URL = "http://localhost:5001"
    
    @pytest.fixture(scope="class")
    def launcher_process(self):
        """Start the launcher with --dev flag for testing."""
        launcher_path = Path("/Users/cward/Devel/dashboard_zero/launch_dataviewer")
        
        if not launcher_path.exists():
            pytest.skip("Launcher script not found")
        
        # Start launcher in background
        process = subprocess.Popen(
            [str(launcher_path), "--dev", "--no-auth"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Wait for services to start
        max_wait = 30
        for i in range(max_wait):
            try:
                response = requests.get(f"{self.DASHBOARD_URL}/api/health", timeout=2)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        else:
            process.terminate()
            pytest.skip("Services failed to start within timeout")
        
        yield process
        
        # Cleanup
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            process.wait(timeout=10)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_worksheet_create_and_auto_save(self, launcher_process):
        """Test creating a worksheet and verifying auto-save functionality."""
        # Create a new worksheet scenario
        scenario_data = {
            "user_id": 1,
            "scenario_name": "E2E Test Worksheet",
            "is_default": False
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario = response.json()
        scenario_id = scenario["scenario_id"]
        
        # Save capability selections (simulating auto-save)
        selections_data = {
            "scenario_id": scenario_id,
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False},
                {"capability_id": "CAP.NONTECH.001", "is_active": True}
            ]
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=selections_data)
        assert response.status_code == 200
        save_result = response.json()
        assert save_result["count"] == 3
        
        # Verify worksheet persists
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        retrieved_scenario = response.json()
        assert retrieved_scenario["scenario_name"] == "E2E Test Worksheet"
        
        # Verify selections persist
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        assert len(selections) == 3
        
        # Clean up
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_worksheet_persistence_across_sessions(self, launcher_process):
        """Test that worksheets persist across simulated browser sessions."""
        # Create worksheet with initial state
        scenario_data = {
            "user_id": 1,
            "scenario_name": "Session Persistence Test",
            "is_default": False
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Save initial selections
        initial_selections = {
            "scenario_id": scenario_id,
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": True},
                {"capability_id": "CAP.NONTECH.001", "is_active": False}
            ]
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=initial_selections)
        assert response.status_code == 200
        
        # Simulate session end (no actual browser restart, just verify data persistence)
        time.sleep(1)
        
        # Simulate new session - verify data is still there
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        scenario = response.json()
        assert scenario["scenario_name"] == "Session Persistence Test"
        
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        selections = response.json()
        assert len(selections) == 3
        
        # Verify specific selections persisted correctly
        active_selections = [s for s in selections if s["is_active"]]
        inactive_selections = [s for s in selections if not s["is_active"]]
        assert len(active_selections) == 2
        assert len(inactive_selections) == 1
        
        # Clean up
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_save_as_flow(self, launcher_process):
        """Test Save As flow by creating a scenario and saving selections."""
        import datetime
        name = datetime.datetime.utcnow().strftime('%Y.%m.%d.%H.%M.%S') + '_capability_worksheet'
        # Create scenario (Save As equivalent server-side)
        scenario_data = {"user_id": 1, "scenario_name": name, "is_default": False}
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        # Save current selections to that scenario
        selections_data = {
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False}
            ]
        }
        response = requests.put(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}", json=selections_data)
        assert response.status_code == 200
        # Verify
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["scenario_name"] == name
        # Cleanup
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_save_as_with_control_selections_no_duplicates(self, launcher_process):
        """Test Save As flow with control selections that don't have duplicates."""
        import datetime
        name = datetime.datetime.utcnow().strftime('%Y.%m.%d.%H.%M.%S') + '_control_worksheet'
        # Create scenario
        scenario_data = {"user_id": 1, "scenario_name": name, "is_default": False}
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Save selections with unique control selections (no duplicates)
        selections_data = {
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True}
            ],
            "control_selections": [
                {"control_id": "CTRL.001", "is_active": True},
                {"control_id": "CTRL.002", "is_active": False}
            ]
        }
        response = requests.put(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}", json=selections_data)
        assert response.status_code == 200
        
        # Verify control selections were saved
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        data = response.json()
        assert "control_selections" in data
        assert len(data["control_selections"]) == 2
        
        # Cleanup
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_save_as_with_duplicate_control_selections_fails(self, launcher_process):
        """Test that Save As with duplicate control selections fails with UNIQUE constraint error."""
        import datetime
        name = datetime.datetime.utcnow().strftime('%Y.%m.%d.%H.%M.%S') + '_duplicate_test'
        # Create scenario
        scenario_data = {"user_id": 1, "scenario_name": name, "is_default": False}
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Try to save duplicate control selections (should fail)
        selections_data = {
            "control_selections": [
                {"control_id": "CTRL.001", "is_active": True},
                {"control_id": "CTRL.001", "is_active": False}  # Duplicate
            ]
        }
        response = requests.put(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}", json=selections_data)
        # Should fail with 500 error due to UNIQUE constraint
        assert response.status_code == 500
        error_detail = response.json().get("detail", "")
        assert "UNIQUE constraint" in error_detail or "Integrity" in error_detail
        
        # Cleanup
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_multiple_worksheets_state_isolation(self, launcher_process):
        """Test that multiple worksheets maintain separate state."""
        # Create multiple worksheets
        scenarios = []
        for i in range(3):
            scenario_data = {
                "user_id": 1,
                "scenario_name": f"Isolation Test Worksheet {i+1}",
                "is_default": False
            }
            response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenarios.append(response.json())
        
        # Save different selections for each worksheet
        for i, scenario in enumerate(scenarios):
            selections_data = {
                "scenario_id": scenario["scenario_id"],
                "selections": [
                    {"capability_id": f"CAP.TECH.00{i+1}", "is_active": True},
                    {"capability_id": f"CAP.TECH.00{i+2}", "is_active": False},
                    {"capability_id": f"CAP.NONTECH.00{i+1}", "is_active": i % 2 == 0}
                ]
            }
            response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=selections_data)
            assert response.status_code == 200
        
        # Verify each worksheet maintains its own state
        for i, scenario in enumerate(scenarios):
            response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario['scenario_id']}")
            assert response.status_code == 200
            selections = response.json()
            
            # Each worksheet should have its own unique selections
            assert len(selections) == 3
            
            # Verify worksheet-specific capability states
            cap1_selection = next(s for s in selections if s["capability_id"] == f"CAP.TECH.00{i+1}")
            cap2_selection = next(s for s in selections if s["capability_id"] == f"CAP.TECH.00{i+2}")
            cap3_selection = next(s for s in selections if s["capability_id"] == f"CAP.NONTECH.00{i+1}")
            
            assert cap1_selection["is_active"] == True
            assert cap2_selection["is_active"] == False
            assert cap3_selection["is_active"] == (i % 2 == 0)
        
        # Clean up
        for scenario in scenarios:
            requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario['scenario_id']}")

    def test_worksheet_delete_and_cleanup(self, launcher_process):
        """Test worksheet deletion and proper cleanup."""
        # Create worksheet with selections
        scenario_data = {
            "user_id": 1,
            "scenario_name": "Cleanup Test Worksheet",
            "is_default": False
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Add selections
        selections_data = {
            "scenario_id": scenario_id,
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False}
            ]
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=selections_data)
        assert response.status_code == 200
        
        # Verify worksheet and selections exist
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Delete worksheet
        response = requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 200
        
        # Verify worksheet is deleted
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
        assert response.status_code == 404
        
        # Verify selections are also cleaned up
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 404

    def test_worksheet_user_isolation_e2e(self, launcher_process):
        """Test user isolation in worksheet management."""
        # Create worksheets for different users
        user1_scenario = {
            "user_id": 1,
            "scenario_name": "User 1 Worksheet",
            "is_default": False
        }
        
        user2_scenario = {
            "user_id": 2,
            "scenario_name": "User 2 Worksheet",
            "is_default": False
        }
        
        response1 = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=user1_scenario)
        response2 = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=user2_scenario)
        
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
        
        requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=user1_selections)
        requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=user2_selections)
        
        # Verify user isolation
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios?user_id=1")
        assert response.status_code == 200
        user1_scenarios = response.json()
        user1_scenario_ids = [s["scenario_id"] for s in user1_scenarios]
        assert scenario1_id in user1_scenario_ids
        assert scenario2_id not in user1_scenario_ids
        
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios?user_id=2")
        assert response.status_code == 200
        user2_scenarios = response.json()
        user2_scenario_ids = [s["scenario_id"] for s in user2_scenarios]
        assert scenario2_id in user2_scenario_ids
        assert scenario1_id not in user2_scenario_ids
        
        # Clean up
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario1_id}")
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario2_id}")

    def test_worksheet_error_handling_e2e(self, launcher_process):
        """Test error handling in worksheet operations."""
        # Test accessing non-existent worksheet
        response = requests.get(f"{self.DATABASE_URL}/api/capability-scenarios/99999")
        assert response.status_code == 404
        
        # Test saving selections for non-existent worksheet
        selections_data = {
            "scenario_id": 99999,
            "selections": [{"capability_id": "CAP.TECH.001", "is_active": True}]
        }
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=selections_data)
        assert response.status_code == 404
        
        # Test invalid data format
        invalid_scenario = {
            "user_id": "invalid",
            "scenario_name": "",
            "is_default": "not_boolean"
        }
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=invalid_scenario)
        assert response.status_code == 422
        
        # Test invalid selections format
        invalid_selections = {
            "scenario_id": 1,
            "selections": "not_a_list"
        }
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=invalid_selections)
        assert response.status_code == 422

    def test_reset_all_functionality_e2e(self, launcher_process):
        """Test Reset All functionality in end-to-end scenario."""
        # Create worksheet with active capabilities
        scenario_data = {
            "user_id": 1,
            "scenario_name": "Reset All E2E Test",
            "is_default": False
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Activate some capabilities
        initial_selections = {
            "scenario_id": scenario_id,
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": True},
                {"capability_id": "CAP.NONTECH.001", "is_active": True},
                {"capability_id": "CAP.NONTECH.002", "is_active": False}
            ]
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=initial_selections)
        assert response.status_code == 200
        
        # Verify initial state has active capabilities
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        initial_selections = response.json()
        active_count = sum(1 for s in initial_selections if s["is_active"])
        assert active_count == 3
        
        # Simulate "Reset All" by deactivating all capabilities
        reset_selections = {
            "scenario_id": scenario_id,
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": False},
                {"capability_id": "CAP.TECH.002", "is_active": False},
                {"capability_id": "CAP.NONTECH.001", "is_active": False},
                {"capability_id": "CAP.NONTECH.002", "is_active": False}
            ]
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=reset_selections)
        assert response.status_code == 200
        
        # Verify all capabilities are now deactivated
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        assert response.status_code == 200
        reset_selections = response.json()
        active_count = sum(1 for s in reset_selections if s["is_active"])
        assert active_count == 0
        
        # Verify specific capabilities are deactivated
        for selection in reset_selections:
            assert selection["is_active"] == False
        
        # Clean up
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")

    def test_worksheet_performance_e2e(self, launcher_process):
        """Test worksheet operations performance with larger datasets."""
        # Create worksheet
        scenario_data = {
            "user_id": 1,
            "scenario_name": "Performance Test Worksheet",
            "is_default": False
        }
        
        response = requests.post(f"{self.DATABASE_URL}/api/capability-scenarios", json=scenario_data)
        assert response.status_code == 200
        scenario_id = response.json()["scenario_id"]
        
        # Create large selection set (simulating many capabilities)
        large_selections = {
            "scenario_id": scenario_id,
            "selections": []
        }
        
        # Generate 100 capability selections
        for i in range(100):
            large_selections["selections"].append({
                "capability_id": f"CAP.TECH.{i:03d}",
                "is_active": i % 2 == 0
            })
        
        # Test save performance
        start_time = time.time()
        response = requests.post(f"{self.DATABASE_URL}/api/capability-selections", json=large_selections)
        save_time = time.time() - start_time
        
        assert response.status_code == 200
        assert save_time < 5.0  # Should complete within 5 seconds
        
        # Test load performance
        start_time = time.time()
        response = requests.get(f"{self.DATABASE_URL}/api/capability-selections/{scenario_id}")
        load_time = time.time() - start_time
        
        assert response.status_code == 200
        assert load_time < 2.0  # Should complete within 2 seconds
        
        selections = response.json()
        assert len(selections) == 100
        
        # Clean up
        requests.delete(f"{self.DATABASE_URL}/api/capability-scenarios/{scenario_id}")
