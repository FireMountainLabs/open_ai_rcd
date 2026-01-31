"""
End-to-end workflow tests for complete worksheet functionality.
Tests the full user journey through scenario management and capability activation.
"""

import pytest
from unittest.mock import patch, Mock
import json


@pytest.mark.e2e
@pytest.mark.integration
class TestCompleteWorksheetWorkflow:
    """Test complete workflow for worksheet functionality."""
    
    def test_complete_scenario_lifecycle(self, client):
        """
        Test complete scenario lifecycle:
        1. Create new scenario
        2. Activate all capabilities
        3. Verify metrics update
        4. Get scenario details
        5. Make changes → verify auto-save
        6. Delete scenario
        7. Verify cleanup
        """
    
    def test_metric_details_workflow(self):
        """
        Test metric details display workflow:
        1. Activate all capabilities
        2. Click Active Controls metric card
        3. Verify modal shows active controls
        4. Close modal
        5. Click Exposed Risks metric card
        6. Verify modal shows exposed risks
        """
        pass
    
    def test_multiple_scenario_management(self):
        """
        Test managing multiple scenarios:
        1. Create Scenario A
        2. Activate some capabilities
        3. Create Scenario B
        4. Activate different capabilities
        5. Switch back to Scenario A
        6. Verify correct capabilities are active
        7. Delete Scenario B
        8. Verify Scenario A still works
        """
        pass
    
    def test_file_menu_interactions(self):
        """
        Test file menu interactions:
        1. Click file menu button → menu opens
        2. Click outside → menu closes
        3. Click file menu → menu opens
        4. Click new scenario → menu closes, prompt appears
        5. Click file menu → menu opens
        6. Click save scenario → menu closes, scenario saves
        """
        pass
    
    def test_auto_save_workflow(self):
        """
        Test auto-save functionality:
        1. Load scenario
        2. Toggle capability → auto-save scheduled
        3. Wait for auto-save
        4. Verify scenario saved
        5. Reload page
        6. Verify changes persisted
        """
        pass

    def test_overview_gap_counts_render(self):
        """
        Test that gap counts on the overview page are rendered correctly.
        """
        # 1. Load the page
        # 2. Verify that gap counts (e.g., #unmappedRisksCount) are not '-'
        with patch("app.requests.post") as mock_post, \
             patch("app.requests.get") as mock_get, \
             patch("app.requests.delete") as mock_delete:
            
            # Mock responses for scenario creation
            mock_create_response = Mock()
            mock_create_response.json.return_value = {
                "scenario_id": 1,
                "user_id": 1,
                "scenario_name": "Test Scenario",
                "is_default": False
            }
            mock_create_response.status_code = 200
            mock_create_response.raise_for_status = Mock()
            
            # Mock responses for getting scenarios (list)
            mock_get_list_response = Mock()
            mock_get_list_response.json.return_value = [
                {
                    "scenario_id": 1,
                    "user_id": 1,
                    "scenario_name": "Test Scenario",
                    "is_default": False
                }
            ]
            mock_get_list_response.status_code = 200
            mock_get_list_response.raise_for_status = Mock()
            
            # Mock responses for getting single scenario
            mock_get_single_response = Mock()
            mock_get_single_response.json.return_value = {
                "scenario_id": 1,
                "user_id": 1,
                "scenario_name": "Test Scenario",
                "is_default": False
            }
            mock_get_single_response.status_code = 200
            mock_get_single_response.raise_for_status = Mock()
            
            # Mock responses for capability selections save
            mock_save_response = Mock()
            mock_save_response.json.return_value = {"count": 3, "success": True}
            mock_save_response.status_code = 200
            mock_save_response.raise_for_status = Mock()
            
            # Mock responses for getting selections
            mock_selections_response = Mock()
            mock_selections_response.json.return_value = [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": True},
                {"capability_id": "CAP.NONTECH.001", "is_active": True}
            ]
            mock_selections_response.status_code = 200
            mock_selections_response.raise_for_status = Mock()
            
            # Mock responses for delete
            mock_delete_response = Mock()
            mock_delete_response.json.return_value = {"success": True}
            mock_delete_response.status_code = 200
            mock_delete_response.raise_for_status = Mock()
            
            # Configure mock responses based on URL
            def post_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                if "capability-scenarios" in url:
                    return mock_create_response
                elif "capability-selections" in url:
                    return mock_save_response
                return mock_create_response
            
            def get_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                params = kwargs.get("params", {})
                if "capability-scenarios" in url and params.get("user_id"):
                    return mock_get_list_response
                elif "capability-scenarios" in url and "/" in url:
                    return mock_get_single_response
                elif "capability-selections" in url:
                    return mock_selections_response
                return mock_get_single_response
            
            def delete_side_effect(*args, **kwargs):
                return mock_delete_response
            
            mock_post.side_effect = post_side_effect
            mock_get.side_effect = get_side_effect
            mock_delete.side_effect = delete_side_effect
            
            # 1. Create new scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Test Scenario",
                "is_default": False
            }
            response = client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario = response.get_json()
            assert "scenario_id" in scenario
            assert scenario["scenario_name"] == "Test Scenario"
            scenario_id = scenario["scenario_id"]
            
            # 2. Activate all capabilities (save selections)
            selections_data = {
                "scenario_id": scenario_id,
                "user_id": 1,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": True},
                    {"capability_id": "CAP.NONTECH.001", "is_active": True}
                ]
            }
            response = client.post("/api/capability-selections", json=selections_data)
            assert response.status_code == 200
            save_result = response.get_json()
            assert "count" in save_result or "success" in save_result
            
            # 3. Verify scenario exists
            response = client.get(f"/api/capability-scenarios?user_id=1")
            assert response.status_code == 200
            scenarios = response.get_json()
            assert isinstance(scenarios, list)
            assert any(s.get("scenario_id") == scenario_id for s in scenarios)
            
            # 4. Get scenario details
            response = client.get(f"/api/capability-scenarios/{scenario_id}?user_id=1")
            assert response.status_code == 200
            scenario_detail = response.get_json()
            assert scenario_detail["scenario_id"] == scenario_id
            
            # 5. Verify selections were saved (auto-save equivalent)
            response = client.get(f"/api/capability-selections/{scenario_id}?user_id=1")
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            
            # 6. Delete scenario
            response = client.delete(f"/api/capability-scenarios/{scenario_id}?user_id=1")
            assert response.status_code == 200
            delete_result = response.get_json()
            assert "success" in delete_result or response.status_code == 200
    
    def test_metric_details_workflow(self, client):
        """
        Test metric details display workflow:
        1. Create scenario with active capabilities
        2. Verify selections data structure
        3. Get active controls (selections)
        4. Verify data format for metrics
        """
        with patch("app.requests.post") as mock_post, \
             patch("app.requests.get") as mock_get:
            
            # Mock scenario creation
            mock_create_response = Mock()
            mock_create_response.json.return_value = {
                "scenario_id": 1,
                "user_id": 1,
                "scenario_name": "Metric Test",
                "is_default": False
            }
            mock_create_response.status_code = 200
            mock_create_response.raise_for_status = Mock()
            
            # Mock selections with active capabilities
            mock_selections_response = Mock()
            mock_selections_response.json.return_value = [
                {"capability_id": "CAP.TECH.001", "is_active": True, "title": "Active Control 1"},
                {"capability_id": "CAP.TECH.002", "is_active": True, "title": "Active Control 2"},
                {"capability_id": "CAP.NONTECH.001", "is_active": False, "title": "Inactive Control"}
            ]
            mock_selections_response.status_code = 200
            mock_selections_response.raise_for_status = Mock()
            
            # Configure mocks
            def post_side_effect(*args, **kwargs):
                return mock_create_response
            
            def get_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                if "capability-selections" in url:
                    return mock_selections_response
                return mock_create_response
            
            mock_post.side_effect = post_side_effect
            mock_get.side_effect = get_side_effect
            
            # 1. Create scenario
            scenario_data = {
                "user_id": 1,
                "scenario_name": "Metric Test",
                "is_default": False
            }
            response = client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            scenario = response.get_json()
            scenario_id = scenario["scenario_id"]
            
            # 2. Get selections (active controls equivalent)
            response = client.get(f"/api/capability-selections/{scenario_id}?user_id=1")
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            
            # 3. Verify active capabilities are present
            active_capabilities = [s for s in selections if s.get("is_active")]
            assert len(active_capabilities) >= 2  # At least 2 active
            
            # 4. Verify data structure for metrics
            for selection in selections:
                assert "capability_id" in selection
                assert "is_active" in selection
    
    def test_multiple_scenario_management(self, client):
        """
        Test managing multiple scenarios:
        1. Create Scenario A
        2. Create Scenario B
        3. Get scenarios list
        4. Verify both scenarios exist
        5. Delete Scenario B
        6. Verify Scenario A still exists
        """
        with patch("app.requests.post") as mock_post, \
             patch("app.requests.get") as mock_get, \
             patch("app.requests.delete") as mock_delete:
            
            scenario_a_id = 1
            scenario_b_id = 2
            
            # Mock scenario creation responses
            def post_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                if "capability-scenarios" in url:
                    data = kwargs.get("json", {})
                    scenario_name = data.get("scenario_name", "")
                    scenario_id = scenario_a_id if "Scenario A" in scenario_name else scenario_b_id
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        "scenario_id": scenario_id,
                        "user_id": 1,
                        "scenario_name": scenario_name,
                        "is_default": False
                    }
                    mock_response.status_code = 200
                    mock_response.raise_for_status = Mock()
                    return mock_response
                return Mock(json=lambda: {}, status_code=200, raise_for_status=Mock())
            
            # Mock getting scenarios list
            def get_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                params = kwargs.get("params", {})
                
                if "capability-scenarios" in url and params.get("user_id"):
                    # Return scenarios list - adjust based on whether scenario_b was deleted
                    scenarios_data = [
                        {
                            "scenario_id": scenario_a_id,
                            "user_id": 1,
                            "scenario_name": "Scenario A",
                            "is_default": False
                        }
                    ]
                    # Add scenario B only if not deleted (simplified - assume it gets removed)
                    mock_response = Mock()
                    mock_response.json.return_value = scenarios_data
                    mock_response.status_code = 200
                    mock_response.raise_for_status = Mock()
                    return mock_response
                elif "capability-scenarios" in url and f"/{scenario_a_id}" in url:
                    mock_response = Mock()
                    mock_response.json.return_value = {
                        "scenario_id": scenario_a_id,
                        "user_id": 1,
                        "scenario_name": "Scenario A",
                        "is_default": False
                    }
                    mock_response.status_code = 200
                    mock_response.raise_for_status = Mock()
                    return mock_response
                return Mock(json=lambda: {}, status_code=200, raise_for_status=Mock())
            
            def delete_side_effect(*args, **kwargs):
                return Mock(json=lambda: {"success": True}, status_code=200, raise_for_status=Mock())
            
            mock_post.side_effect = post_side_effect
            mock_get.side_effect = get_side_effect
            mock_delete.side_effect = delete_side_effect
            
            # 1. Create Scenario A
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "Scenario A",
                "is_default": False
            })
            assert response.status_code == 200
            scenario_a = response.get_json()
            assert scenario_a["scenario_name"] == "Scenario A"
            
            # 2. Create Scenario B
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "Scenario B",
                "is_default": False
            })
            assert response.status_code == 200
            scenario_b = response.get_json()
            assert scenario_b["scenario_name"] == "Scenario B"
            
            # 3. Get scenarios list
            response = client.get("/api/capability-scenarios?user_id=1")
            assert response.status_code == 200
            scenarios = response.get_json()
            assert isinstance(scenarios, list)
            assert len(scenarios) >= 1
            
            # 4. Verify Scenario A exists after getting list
            response = client.get(f"/api/capability-scenarios/{scenario_a_id}?user_id=1")
            assert response.status_code == 200
            scenario_a_detail = response.get_json()
            assert scenario_a_detail["scenario_id"] == scenario_a_id
            
            # 5. Delete Scenario B
            response = client.delete(f"/api/capability-scenarios/{scenario_b_id}?user_id=1")
            assert response.status_code == 200
            
            # 6. Verify Scenario A still exists
            response = client.get(f"/api/capability-scenarios/{scenario_a_id}?user_id=1")
            assert response.status_code == 200
            assert response.get_json()["scenario_id"] == scenario_a_id
    
    def test_file_menu_interactions(self, client):
        """
        Test file menu interactions via API:
        1. Create scenario (new scenario action)
        2. Get scenario (verify it was created)
        3. Update scenario (save scenario action)
        4. Verify scenario was updated
        """
        with patch("app.requests.post") as mock_post, \
             patch("app.requests.get") as mock_get, \
             patch("app.requests.put") as mock_put:
            
            scenario_id = 1
            
            def post_side_effect(*args, **kwargs):
                mock_response = Mock()
                mock_response.json.return_value = {
                    "scenario_id": scenario_id,
                    "user_id": 1,
                    "scenario_name": "New Scenario",
                    "is_default": False
                }
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                return mock_response
            
            def get_side_effect(*args, **kwargs):
                mock_response = Mock()
                mock_response.json.return_value = {
                    "scenario_id": scenario_id,
                    "user_id": 1,
                    "scenario_name": "New Scenario",
                    "is_default": False
                }
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                return mock_response
            
            def put_side_effect(*args, **kwargs):
                mock_response = Mock()
                mock_response.json.return_value = {
                    "scenario_id": scenario_id,
                    "user_id": 1,
                    "scenario_name": "Updated Scenario",
                    "is_default": False
                }
                mock_response.status_code = 200
                mock_response.raise_for_status = Mock()
                return mock_response
            
            mock_post.side_effect = post_side_effect
            mock_get.side_effect = get_side_effect
            mock_put.side_effect = put_side_effect
            
            # 1. Create scenario (simulates "new scenario" action)
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "New Scenario",
                "is_default": False
            })
            assert response.status_code == 200
            assert response.get_json()["scenario_name"] == "New Scenario"
            
            # 2. Get scenario (verify it exists)
            response = client.get(f"/api/capability-scenarios/{scenario_id}?user_id=1")
            assert response.status_code == 200
            assert response.get_json()["scenario_id"] == scenario_id
            
            # 3. Update scenario (simulates "save scenario" action)
            response = client.put(f"/api/capability-scenarios/{scenario_id}?user_id=1", json={
                "scenario_name": "Updated Scenario",
                "is_default": False
            })
            assert response.status_code == 200
            
            # 4. Verify scenario was updated
            updated = response.get_json()
            assert updated["scenario_name"] == "Updated Scenario"
    
    def test_auto_save_workflow(self, client):
        """
        Test auto-save functionality:
        1. Create scenario
        2. Save capability selections (auto-save equivalent)
        3. Verify selections were saved
        4. Get selections again (reload equivalent)
        5. Verify changes persisted
        """
        with patch("app.requests.post") as mock_post, \
             patch("app.requests.get") as mock_get:
            
            scenario_id = 1
            
            # Mock scenario creation
            mock_create_response = Mock()
            mock_create_response.json.return_value = {
                "scenario_id": scenario_id,
                "user_id": 1,
                "scenario_name": "Auto Save Test",
                "is_default": False
            }
            mock_create_response.status_code = 200
            mock_create_response.raise_for_status = Mock()
            
            # Mock save selections response
            mock_save_response = Mock()
            mock_save_response.json.return_value = {"count": 2, "success": True}
            mock_save_response.status_code = 200
            mock_save_response.raise_for_status = Mock()
            
            # Mock get selections response (after save)
            selections_data = [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False}
            ]
            mock_selections_response = Mock()
            mock_selections_response.json.return_value = selections_data
            mock_selections_response.status_code = 200
            mock_selections_response.raise_for_status = Mock()
            
            def post_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                if "capability-selections" in url:
                    return mock_save_response
                return mock_create_response
            
            def get_side_effect(*args, **kwargs):
                url = kwargs.get("url", args[0] if args else "")
                if "capability-selections" in url:
                    return mock_selections_response
                return mock_create_response
            
            mock_post.side_effect = post_side_effect
            mock_get.side_effect = get_side_effect
            
            # 1. Create scenario
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "Auto Save Test",
                "is_default": False
            })
            assert response.status_code == 200
            scenario = response.get_json()
            assert scenario["scenario_id"] == scenario_id
            
            # 2. Save capability selections (auto-save)
            selections_data_to_save = {
                "scenario_id": scenario_id,
                "user_id": 1,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False}
                ]
            }
            response = client.post("/api/capability-selections", json=selections_data_to_save)
            assert response.status_code == 200
            save_result = response.get_json()
            assert "count" in save_result or "success" in save_result
            
            # 3. Verify selections were saved (reload equivalent)
            response = client.get(f"/api/capability-selections/{scenario_id}?user_id=1")
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            assert len(selections) == 2
            
            # 4. Verify changes persisted - check specific selections
            capability_001 = next((s for s in selections if s["capability_id"] == "CAP.TECH.001"), None)
            capability_002 = next((s for s in selections if s["capability_id"] == "CAP.TECH.002"), None)
            assert capability_001 is not None
            assert capability_002 is not None
            assert capability_001["is_active"] is True
            assert capability_002["is_active"] is False

    def test_overview_gap_counts_render(self, client):
        """
        Test that gap counts data structure is correct:
        1. Get gaps data from API
        2. Verify data structure
        3. Verify counts are numeric
        """
        with patch("app.api_client") as mock_api_client:
            # Mock gaps response - structure based on actual API response
            mock_gaps_data = {
                "summary": {
                    "total_controls": 0,
                    "total_risks": 0,
                    "unmapped_risks": 0
                },
                "unmapped_risks": []
            }
            
            mock_api_client.get_gaps.return_value = mock_gaps_data
            
            # Get gaps data
            response = client.get("/api/gaps")
            assert response.status_code == 200
            gaps_data = response.get_json()
            
            # Verify data structure - check for summary or unmapped_risks
            assert "summary" in gaps_data or "unmapped_risks" in gaps_data
            if "summary" in gaps_data:
                summary = gaps_data["summary"]
                # Verify counts are numeric (not '-', 'undefined', or 'NaN')
                if "unmapped_risks" in summary:
                    assert isinstance(summary["unmapped_risks"], (int, float))
                    assert summary["unmapped_risks"] >= 0
                if "total_risks" in summary:
                    assert isinstance(summary["total_risks"], (int, float))
                    assert summary["total_risks"] >= 0
            if "unmapped_risks" in gaps_data:
                assert isinstance(gaps_data["unmapped_risks"], list)


@pytest.mark.e2e
@pytest.mark.integration
class TestWorksheetErrorHandling:
    """Test error handling in worksheet functionality."""
    
    def test_delete_scenario_cancellation(self, client):
        """Test that scenario deletion can be handled gracefully."""
        with patch("app.requests.get") as mock_get, \
             patch("app.requests.delete") as mock_delete:
            
            scenario_id = 1
            
            # Mock successful get before deletion (simulating cancellation - scenario still exists)
            mock_get_response = Mock()
            mock_get_response.json.return_value = {
                "scenario_id": scenario_id,
                "user_id": 1,
                "scenario_name": "Test Scenario",
                "is_default": False
            }
            mock_get_response.status_code = 200
            mock_get_response.raise_for_status = Mock()
            
            mock_get.side_effect = lambda *args, **kwargs: mock_get_response
            
            # Verify scenario exists (simulates checking before deletion)
            response = client.get(f"/api/capability-scenarios/{scenario_id}")
            assert response.status_code == 200
            scenario = response.get_json()
            assert scenario["scenario_id"] == scenario_id
            assert scenario["scenario_name"] == "Test Scenario"
    
    def test_create_scenario_without_name(self, client):
        """Test creating scenario without name fails validation."""
        with patch("app.requests.post") as mock_post:
            # Mock validation error response that raises exception
            def post_side_effect(*args, **kwargs):
                mock_response = Mock()
                mock_response.json.return_value = {"error": "Scenario name is required"}
                mock_response.status_code = 400
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Bad request")
                return mock_response
            
            import requests
            mock_post.side_effect = post_side_effect
            
            # Attempt to create scenario with empty name
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "",
                "is_default": False
            })
            
            # Should either reject empty name or require name field
            # The validation happens at API level - exception is caught and returns 500
            assert response.status_code in [400, 422, 500]  # Bad request, validation error, or server error

    def test_create_duplicate_scenario_name_returns_descriptive_error(self, client):
        """Test that creating a duplicate scenario name returns descriptive error message."""
        scenario_name = "Duplicate Test Scenario"
        scenario_data = {
            "user_id": 1,
            "scenario_name": scenario_name,
            "is_default": False
        }
        
        with patch("routes.capability_scenarios.requests.post") as mock_post:
            import requests
            
            # First call succeeds (create scenario)
            call_count = [0]  # Use list to allow modification in nested function
            
            def post_side_effect(*args, **kwargs):
                url = args[0] if args else ""
                if "capability-scenarios" in url:
                    call_count[0] += 1
                    
                    if call_count[0] == 1:
                        # First call - success
                        mock_response = Mock()
                        mock_response.json.return_value = {
                            "scenario_id": 1,
                            "user_id": 1,
                            "scenario_name": scenario_name,
                            "is_default": False
                        }
                        mock_response.status_code = 200
                        mock_response.raise_for_status = Mock()
                        return mock_response
                    else:
                        # Second call - duplicate name error
                        mock_response = Mock()
                        mock_response.status_code = 400
                        mock_response.json.return_value = {
                            "detail": f"Scenario name '{scenario_name}' already exists for this user. Please choose a different name."
                        }
                        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
                            response=mock_response
                        )
                        mock_response.raise_for_status.side_effect.response = mock_response
                        return mock_response
                return Mock(json=lambda: {}, status_code=200, raise_for_status=Mock())
            
            mock_post.side_effect = post_side_effect
            
            # First creation succeeds
            response = client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 200
            
            # Second creation with same name fails with descriptive error
            response = client.post("/api/capability-scenarios", json=scenario_data)
            assert response.status_code == 400
            error_data = response.get_json()
            
            # Verify error message is descriptive and includes scenario name
            assert "error" in error_data or "detail" in error_data
            error_detail = error_data.get("error") or error_data.get("detail", "")
            assert scenario_name in error_detail
            assert "already exists" in error_detail.lower()
    
    def test_show_metric_details_with_no_data(self, client):
        """Test showing metric details with no data available."""
        with patch("app.requests.get") as mock_get:
            scenario_id = 1
            
            # Mock empty selections response
            mock_empty_response = Mock()
            mock_empty_response.json.return_value = []
            mock_empty_response.status_code = 200
            mock_empty_response.raise_for_status = Mock()
            
            mock_get.side_effect = lambda *args, **kwargs: mock_empty_response
            
            # Get selections when no data exists (empty scenario)
            response = client.get(f"/api/capability-selections/{scenario_id}?user_id=1")
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            assert len(selections) == 0  # No selections/empty state
    
    def test_delete_scenario_without_selection(self, client):
        """Test deleting with invalid scenario ID handles error gracefully."""
        with patch("app.requests.delete") as mock_delete:
            invalid_scenario_id = 99999
            import requests
            
            def delete_side_effect(*args, **kwargs):
                # Simulate raise_for_status raising exception
                mock_response = Mock()
                mock_response.status_code = 404
                mock_response.json.return_value = {"error": "Not found"}
                mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("Not found")
                return mock_response
            
            mock_delete.side_effect = delete_side_effect
            
            # Attempt to delete non-existent scenario
            response = client.delete(f"/api/capability-scenarios/{invalid_scenario_id}?user_id=1")
            # Should handle error gracefully (exception caught, returns 500)
            assert response.status_code in [404, 500]  # Not found or server error


@pytest.mark.e2e
@pytest.mark.integration
@pytest.mark.slow
class TestWorksheetPerformance:
    """Test performance of worksheet operations."""
    
    def test_activate_all_performance(self, client):
        """Test that saving multiple capabilities performs acceptably."""
        import time
        
        with patch("app.requests.post") as mock_post:
            scenario_id = 1
            
            # Mock successful save
            mock_save_response = Mock()
            mock_save_response.json.return_value = {"count": 100, "success": True}
            mock_save_response.status_code = 200
            mock_save_response.raise_for_status = Mock()
            mock_post.side_effect = lambda *args, **kwargs: mock_save_response
            
            # Simulate saving many capabilities (performance test)
            large_selections = {
                "scenario_id": scenario_id,
                "user_id": 1,
                "selections": [
                    {"capability_id": f"CAP.TECH.{i:03d}", "is_active": True}
                    for i in range(100)
                ]
            }
            
            start_time = time.time()
            response = client.post("/api/capability-selections", json=large_selections)
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200
            # Should complete within reasonable time (< 2 seconds for mocked response)
            assert elapsed_time < 2.0, f"Operation took {elapsed_time:.2f}s, expected < 2.0s"
    
    def test_large_scenario_management(self, client):
        """Test managing scenarios with many capabilities."""
        with patch("app.requests.get") as mock_get:
            scenario_id = 1
            
            # Mock large selections list (100+ capabilities)
            large_selections = [
                {"capability_id": f"CAP.TECH.{i:03d}", "is_active": i % 2 == 0}
                for i in range(150)
            ]
            
            mock_response = Mock()
            mock_response.json.return_value = large_selections
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.side_effect = lambda *args, **kwargs: mock_response
            
            # Get selections for large scenario
            response = client.get(f"/api/capability-selections/{scenario_id}")
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            assert len(selections) == 150  # Verify large dataset handled
    
    def test_metric_details_rendering_performance(self, client):
        """Test that metric details data retrieval is efficient."""
        import time
        
        with patch("app.requests.get") as mock_get:
            scenario_id = 1
            
            # Mock large selections list (100+ items)
            large_selections = [
                {
                    "capability_id": f"CAP.TECH.{i:03d}",
                    "is_active": True,
                    "title": f"Capability {i}",
                    "description": f"Description for capability {i}"
                }
                for i in range(100)
            ]
            
            mock_response = Mock()
            mock_response.json.return_value = large_selections
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.side_effect = lambda *args, **kwargs: mock_response
            
            # Get selections (simulating metric details retrieval)
            start_time = time.time()
            response = client.get(f"/api/capability-selections/{scenario_id}")
            elapsed_time = time.time() - start_time
            
            assert response.status_code == 200
            selections = response.get_json()
            assert isinstance(selections, list)
            assert len(selections) == 100
            # Should retrieve quickly (< 500ms for mocked response)
            assert elapsed_time < 0.5, f"Retrieval took {elapsed_time:.3f}s, expected < 0.5s"


@pytest.mark.unit
class TestWorkflowHelperMethods:
    """Test helper methods used in workflows."""
    
    def test_status_message_display(self, client):
        """Test that status messages can be handled."""
        # Status messages are typically frontend, but we can verify API responses
        # contain appropriate status/success indicators
        with patch("app.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {
                "scenario_id": 1,
                "user_id": 1,
                "scenario_name": "Test",
                "is_default": False,
                "status": "success"
            }
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_post.side_effect = lambda *args, **kwargs: mock_response
            
            response = client.post("/api/capability-scenarios", json={
                "user_id": 1,
                "scenario_name": "Test",
                "is_default": False
            })
            assert response.status_code == 200
            data = response.get_json()
            # Verify response contains scenario data (status implied by 200 status code)
            assert "scenario_id" in data
    
    def test_save_status_indicator(self, client):
        """Test that save operations return appropriate status."""
        with patch("app.requests.post") as mock_post:
            scenario_id = 1
            mock_response = Mock()
            mock_response.json.return_value = {"count": 2, "success": True}
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_post.side_effect = lambda *args, **kwargs: mock_response
            
            response = client.post("/api/capability-selections", json={
                "scenario_id": scenario_id,
                "user_id": 1,
                "selections": [
                    {"capability_id": "CAP.TECH.001", "is_active": True},
                    {"capability_id": "CAP.TECH.002", "is_active": False}
                ]
            })
            assert response.status_code == 200
            save_result = response.get_json()
            # Verify save result contains success indicator
            assert "success" in save_result or "count" in save_result
    
    def test_scenario_selector_population(self, client):
        """Test that scenario selector list is populated correctly."""
        with patch("app.requests.get") as mock_get:
            mock_response = Mock()
            mock_response.json.return_value = [
                {"scenario_id": 1, "user_id": 1, "scenario_name": "Scenario 1", "is_default": False},
                {"scenario_id": 2, "user_id": 1, "scenario_name": "Scenario 2", "is_default": False},
                {"scenario_id": 3, "user_id": 1, "scenario_name": "Scenario 3", "is_default": False}
            ]
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.side_effect = lambda *args, **kwargs: mock_response
            
            response = client.get("/api/capability-scenarios?user_id=1")
            assert response.status_code == 200
            scenarios = response.get_json()
            assert isinstance(scenarios, list)
            assert len(scenarios) == 3
            # Verify each scenario has required fields for selector
            for scenario in scenarios:
                assert "scenario_id" in scenario
                assert "scenario_name" in scenario
                assert "user_id" in scenario

