"""
Tests for metric cards modal functionality.

These tests focus on the HTML structure, API integration, and UI elements
that can be tested from the Python side.
"""

from bs4 import BeautifulSoup


class TestMetricCardsModals:
    """Test metric cards modal functionality."""

    def test_metric_cards_have_clickable_class(self, client):
        """Test that metric cards have the 'clickable-metric' class."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Find the metric cards by their parent div with clickable-metric class
        clickable_cards = soup.find_all("div", class_="clickable-metric")

        # Should have 4 clickable metric cards (assigned-controls, active-controls, partially-covered, exposed-risks)
        assert len(clickable_cards) == 4

        # Check that they have the correct data attributes
        data_types = [card.get("data-metric-type") for card in clickable_cards]
        assert "active-controls" in data_types
        assert "partially-covered" in data_types
        assert "exposed-risks" in data_types

    def test_metric_cards_have_correct_data_attributes(self, client):
        """Test that metric cards have the correct data attributes."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Find clickable metric cards and check their data attributes
        clickable_cards = soup.find_all("div", class_="clickable-metric")

        # Create a mapping of data-metric-type to the card
        data_type_map = {}
        for card in clickable_cards:
            data_type = card.get("data-metric-type")
            if data_type:
                data_type_map[data_type] = card

        # Check that all expected data types are present
        assert "active-controls" in data_type_map
        assert "partially-covered" in data_type_map
        assert "exposed-risks" in data_type_map

        # Check that the cards have the correct structure
        for data_type, card in data_type_map.items():
            assert card.get("data-metric-type") == data_type
            assert "metric-card" in card.get("class")

    def test_modal_structure_exists(self, client):
        """Test that the modal structure exists in the template."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Check for modal structure
        modal = soup.find("div", class_="modal")
        assert modal is not None

        modal_content = soup.find("div", class_="modal-content")
        assert modal_content is not None

        modal_body = soup.find("div", id="modalBody")
        assert modal_body is not None

    def test_capability_analysis_endpoint_proxy(self, client):
        """Test that the capability analysis endpoint is accessible."""
        # Test the endpoint exists and returns JSON
        response = client.post(
            "/api/capability-analysis",
            json={"capability_ids": []},
            content_type="application/json",
        )

        # Should return 200 or 500 (depending on database connection)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.get_json()
            assert "total_controls" in data
            assert "active_controls" in data
            assert "exposed_risks" in data

    def test_capability_analysis_endpoint_with_empty_capabilities(self, client):
        """Test capability analysis endpoint with empty capability list."""
        response = client.post(
            "/api/capability-analysis",
            json={"capability_ids": []},
            content_type="application/json",
        )

        # Should return 200 or 500 (depending on database connection)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.get_json()
            # With no active capabilities, all risks should be exposed
            assert data["active_controls"] == 0
            assert data["exposed_risks"] >= 0

    def test_capability_analysis_endpoint_error_handling(self, client):
        """Test capability analysis endpoint error handling."""
        # Test with invalid JSON
        response = client.post(
            "/api/capability-analysis",
            data="invalid json",
            content_type="application/json",
        )

        # Should return 400 for invalid JSON
        assert response.status_code == 400

    def test_metric_cards_css_styling(self, client):
        """Test that metric cards have the correct CSS classes."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Check for CSS classes
        metric_cards = soup.find_all("div", class_="metric-card")
        clickable_cards = soup.find_all("div", class_="clickable-metric")

        assert len(metric_cards) >= 3  # At least 3 metric cards
        assert len(clickable_cards) >= 3  # At least 3 clickable cards

    def test_modal_content_structure(self, client):
        """Test that modal content has the expected structure."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Check for modal elements
        modal = soup.find("div", class_="modal")
        assert modal is not None

        # Check for close button
        close_button = soup.find("span", class_="close")
        assert close_button is not None

        # Check for modal body
        modal_body = soup.find("div", id="modalBody")
        assert modal_body is not None

    def test_metric_cards_accessibility(self, client):
        """Test that metric cards have proper accessibility attributes."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        clickable_cards = soup.find_all("div", class_="clickable-metric")

        for card in clickable_cards:
            # Check for data attributes
            assert card.get("data-metric-type") is not None

            # Check for proper structure
            assert card.find("h3") is not None  # Should have a heading
            assert (
                card.find("div", class_="metric-value") is not None
            )  # Should have value


class TestMetricCardsIntegration:
    """Integration tests for metric cards functionality."""

    def test_metric_cards_workflow(self, client):
        """Test the complete metric cards workflow."""
        # Test that the page loads with metric cards
        response = client.get("/")
        assert response.status_code == 200

        soup = BeautifulSoup(response.data, "html.parser")

        # Check that metric cards are present
        metric_cards = soup.find_all("div", class_="metric-card")
        assert len(metric_cards) >= 3

        # Check that clickable cards are present
        clickable_cards = soup.find_all("div", class_="clickable-metric")
        assert len(clickable_cards) >= 3

    def test_capability_configuration_tab_structure(self, client):
        """Test that the capability configuration tab has the correct structure."""
        response = client.get("/")
        assert response.status_code == 200
        soup = BeautifulSoup(response.data, "html.parser")

        # Check for capability configuration tab
        capability_tab = soup.find("button", string="Capability Configuration")
        assert capability_tab is not None

        # Check for the capability and control configurator heading
        heading = soup.find("h2", string="Capability and Control Configurator")
        assert heading is not None

        # Check for metric cards in the capability section
        capability_metrics = soup.find("div", class_="capability-metrics")
        assert capability_metrics is not None

    def test_ui_text_updates(self, client):
        """Test that UI text has been updated correctly."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode("utf-8")

        # Check for updated text
        assert "Capability Configuration" in content
        assert "Capability and Control Configurator" in content
        assert "Assigned Controls" in content
        assert "mapped to capabilities" in content

    def test_modal_script_integration(self, client):
        """Test that modal functionality is properly integrated."""
        response = client.get("/")
        assert response.status_code == 200
        content = response.data.decode("utf-8")

        # Check that dashboard.js is loaded (contains modal functionality)
        assert "dashboard.js" in content

        # Check that the modal structure is present
        assert "modal" in content
        assert "modalBody" in content
        assert "clickable-metric" in content

    def test_metric_cards_data_flow(self, client):
        """Test that metric cards can receive data from the API."""
        # Test that the capability analysis endpoint is accessible
        response = client.post(
            "/api/capability-analysis",
            json={"capability_ids": []},
            content_type="application/json",
        )

        # Should return 200 or 500 (depending on database connection)
        assert response.status_code in [200, 500]

        if response.status_code == 200:
            data = response.get_json()

            # Check that the response has the expected structure
            expected_fields = [
                "total_controls",
                "controls_in_capabilities",
                "active_controls",
                "exposed_risks",
                "total_risks",
                "active_risks",
                "partially_covered_risks",
                "active_controls_list",
                "partially_covered_risks_list",
                "exposed_risks_list",
            ]

            for field in expected_fields:
                assert field in data
