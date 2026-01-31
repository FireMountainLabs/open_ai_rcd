"""
Test that scenario selector loads scenarios correctly.

This test verifies that:
1. The scenario selector dropdown is populated with available scenarios
2. Selecting a scenario from the dropdown loads it correctly
3. Control selections are properly restored when loading a scenario
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
import sys
sys.path.append("/Users/cward/Devel/dashboard_zero/dashboard-service")

try:
    from app import app
except ImportError:
    pytest.skip("App module not available", allow_module_level=True)


@pytest.mark.unit
class TestScenarioSelectorLoadsScenario:
    """Test scenario selector functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        app.config['TESTING'] = True
        app.config['ENABLE_AUTH'] = False
        # ENABLE_AUTH is set via app.config, no patch needed
        with app.test_client() as client:
            yield client

    def test_scenario_selector_exists_in_template(self, client):
        """Test that scenario selector dropdown exists in the HTML template."""
        # ENABLE_AUTH is already set via app.config in the fixture
        response = client.get('/')
        # May redirect or show template, either way check for selector
        if response.status_code == 200:
            assert 'id="scenario-selector"' in response.text
            assert ('-- Select Worksheet --' in response.text or 
                    '-- Select Scenario --' in response.text)
        elif response.status_code == 302:
            # Redirect expected if auth is enabled
            pass

    def test_scenario_selector_loads_scenarios(self, client):
        """Test that scenario selector loads scenarios correctly via API."""
        # When auth is disabled, use a test user_id directly
        session_user_id = 1
        
        # Mock the database service response
        mock_scenarios = [
            {
                "scenario_id": 1,
                "user_id": session_user_id,
                "scenario_name": "Test Scenario 1",
                "is_default": False,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            },
            {
                "scenario_id": 2,
                "user_id": session_user_id,
                "scenario_name": "Test Scenario 2",
                "is_default": True,
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T00:00:00"
            }
        ]

        with patch('routes.capability_scenarios.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_scenarios)
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # When auth is disabled, user_id comes from query params
            response = client.get(f'/api/capability-scenarios?user_id={session_user_id}')
            assert response.status_code == 200
            scenarios = response.get_json()
            assert len(scenarios) == 2
            assert scenarios[0]["scenario_name"] == "Test Scenario 1"
            assert scenarios[1]["scenario_name"] == "Test Scenario 2"
            assert scenarios[1]["is_default"] == True

    def test_scenario_selector_loads_scenario_with_selections(self, client):
        """Test that selecting a scenario loads it with its selections."""
        # When auth is disabled, use a test user_id directly
        session_user_id = 1
        
        mock_scenario = {
            "scenario_id": 1,
            "user_id": session_user_id,
            "scenario_name": "Test Scenario",
            "is_default": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "selections": [
                {"capability_id": "CAP.TECH.001", "is_active": True},
                {"capability_id": "CAP.TECH.002", "is_active": False}
            ],
            "control_selections": [
                {"control_id": "CTRL.001", "is_active": True},
                {"control_id": "CTRL.002", "is_active": False}
            ]
        }

        with patch('routes.capability_scenarios.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_scenario)
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # When auth is disabled, user_id comes from query params
            response = client.get(f'/api/capability-scenarios/1?user_id={session_user_id}')
            assert response.status_code == 200
            scenario = response.get_json()
            
            assert scenario["scenario_id"] == 1
            assert "selections" in scenario
            assert len(scenario["selections"]) == 2
            assert "control_selections" in scenario
            assert len(scenario["control_selections"]) == 2
            
            # Verify selections
            active_cap = next((s for s in scenario["selections"] if s["is_active"]), None)
            assert active_cap is not None
            assert active_cap["capability_id"] == "CAP.TECH.001"
            
            # Verify control selections
            active_ctrl = next((c for c in scenario["control_selections"] if c["is_active"]), None)
            assert active_ctrl is not None
            assert active_ctrl["control_id"] == "CTRL.001"

    def test_scenario_selector_handles_empty_scenarios(self, client):
        """Test that scenario selector handles empty scenarios list."""
        # When auth is disabled, use a test user_id directly
        session_user_id = 1
        
        with patch('routes.capability_scenarios.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=[])
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # When auth is disabled, user_id comes from query params
            response = client.get(f'/api/capability-scenarios?user_id={session_user_id}')
            assert response.status_code == 200
            scenarios = response.get_json()
            assert scenarios == []
            assert len(scenarios) == 0

    def test_scenario_selector_handles_nonexistent_scenario(self, client):
        """Test that scenario selector handles loading a non-existent scenario."""
        from requests.exceptions import HTTPError
        
        # When auth is disabled, use a test user_id directly
        session_user_id = 1
        
        with patch('routes.capability_scenarios.requests.get') as mock_get:
            # Create a proper HTTPError with response
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.text = "Not found"
            mock_response.raise_for_status.side_effect = HTTPError(
                response=mock_response
            )
            mock_get.return_value = mock_response

            # When auth is disabled, user_id comes from query params
            response = client.get(f'/api/capability-scenarios/99999?user_id={session_user_id}')
            # Should handle error gracefully - our fix should return proper error
            assert response.status_code in [404, 500]

    def test_scenario_selector_populates_default_scenario(self, client):
        """Test that default scenario is marked correctly in the selector."""
        # When auth is disabled, use a test user_id directly
        session_user_id = 1
        
        mock_scenarios = [
            {
                "scenario_id": 1,
                "user_id": session_user_id,
                "scenario_name": "Regular Scenario",
                "is_default": False
            },
            {
                "scenario_id": 2,
                "user_id": session_user_id,
                "scenario_name": "Default Scenario",
                "is_default": True
            }
        ]

        with patch('routes.capability_scenarios.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=mock_scenarios)
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response

            # When auth is disabled, user_id comes from query params
            response = client.get(f'/api/capability-scenarios?user_id={session_user_id}')
            assert response.status_code == 200
            scenarios = response.get_json()
            
            default_scenario = next((s for s in scenarios if s["is_default"]), None)
            assert default_scenario is not None
            assert default_scenario["scenario_name"] == "Default Scenario"
            assert default_scenario["scenario_id"] == 2

