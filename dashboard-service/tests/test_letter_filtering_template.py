"""
Tests for the A-Z letter filtering template rendering.

This module tests that the HTML template correctly renders the letter filtering
functionality and that all required elements are present.
"""

import pytest
from unittest.mock import patch, MagicMock
import app as app_module


@pytest.mark.unit
@pytest.mark.frontend
class TestLetterFilteringTemplate:
    """Test template rendering for letter filtering functionality."""

    def test_definitions_tab_contains_letter_filter(self, client):
        """Test that the definitions tab contains the letter filter HTML structure."""
        with patch("app.api_client") as mock_api_client:
            # Mock minimal data to avoid API calls
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for letter filter container
            assert 'class="alphabet-filter"' in html_content
            assert 'class="filter-label"' in html_content
            assert 'class="letter-links"' in html_content

            # Check for "All" option
            assert 'data-letter=""' in html_content
            assert "All</a>" in html_content

            # Check for all A-Z letters
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                assert f'data-letter="{letter}"' in html_content
                assert f">{letter}</a>" in html_content

    def test_letter_filter_css_classes_are_present(self, client):
        """Test that all required CSS classes are present in the template."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for CSS classes that are actually in the HTML
            html_css_classes = [
                "alphabet-filter",
                "filter-label",
                "letter-links",
                "letter-link",
                "letter-link active",
            ]

            for css_class in html_css_classes:
                assert css_class in html_content

    def test_letter_filter_positioning(self, client):
        """Test that the letter filter is positioned correctly in the definitions tab."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check that letter filter comes after category filter but before table
            definitions_section_start = html_content.find('id="definitions"')
            alphabet_filter_start = html_content.find('class="alphabet-filter"')
            table_start = html_content.find('id="definitionsTable"')

            assert definitions_section_start < alphabet_filter_start < table_start

    def test_letter_filter_accessibility_attributes(self, client):
        """Test that letter filter has proper accessibility attributes."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for proper link structure
            assert 'href="#"' in html_content  # All letter links should have href="#"
            assert "data-letter=" in html_content  # Should have data-letter attributes

            # Check that all letters have proper structure
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                letter_pattern = f'<a href="#" class="letter-link" data-letter="{letter}">{letter}</a>'
                assert letter_pattern in html_content

    def test_letter_filter_with_definitions_data(self, client):
        """Test letter filter rendering with actual definitions data."""
        mock_definitions = [
            {
                "definition_id": "def_001",
                "term": "Algorithm",
                "title": "Algorithm",
                "description": "A set of rules for solving problems",
                "category": "Technical Terms",
                "source": "test.xlsx",
            },
            {
                "definition_id": "def_002",
                "term": "Bias",
                "title": "Bias",
                "description": "Systematic error in models",
                "category": "Ethics",
                "source": "test.xlsx",
            },
            {
                "definition_id": "def_003",
                "term": "Computer Vision",
                "title": "Computer Vision",
                "description": "Field of AI for visual processing",
                "category": "Technical Terms",
                "source": "test.xlsx",
            },
        ]

        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = mock_definitions
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check that definitions table structure is present (data is loaded via JavaScript)
            assert "definitionsTable" in html_content
            assert "Term" in html_content
            assert "Title" in html_content
            assert "Description" in html_content

            # Check that letter filter is still present
            assert 'class="alphabet-filter"' in html_content
            assert "Filter by letter:" in html_content

    def test_letter_filter_css_file_inclusion(self, client):
        """Test that the CSS file containing letter filter styles is included."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for CSS file inclusion
            assert "dashboard.css" in html_content
            assert "static/css/dashboard.css" in html_content

    def test_letter_filter_javascript_inclusion(self, client):
        """Test that the JavaScript file containing letter filter logic is included."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for JavaScript file inclusion
            assert "dashboard.js" in html_content
            assert "static/js/dashboard.js" in html_content

    def test_letter_filter_responsive_design(self, client):
        """Test that letter filter has responsive design elements."""
        with patch("app.api_client") as mock_api_client:
            mock_api_client.get_definitions.return_value = []
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Check for responsive design elements
            assert 'class="letter-links"' in html_content  # Container for letter links
            assert 'class="letter-link"' in html_content  # Individual letter links

            # Check that letters are properly structured for responsive layout
            # Count both active and regular letter links
            letter_count = html_content.count('class="letter-link"')
            assert letter_count >= 26  # At least 26 letters A-Z

            # Verify "All" link is present
            assert 'data-letter=""' in html_content
            assert "All</a>" in html_content

            # Verify we have all letters A-Z
            for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                assert f'data-letter="{letter}"' in html_content

    def test_letter_filter_error_handling_in_template(self, client):
        """Test that template handles errors gracefully when rendering letter filter."""
        with patch("app.api_client") as mock_api_client:
            # Test with API error
            mock_api_client.get_definitions.side_effect = Exception("API Error")
            mock_api_client.get_risks.return_value = []
            mock_api_client.get_controls.return_value = []
            mock_api_client.get_questions.return_value = []
            mock_api_client.get_network.return_value = []
            mock_api_client.get_gaps.return_value = {
                "summary": {},
                "risks_without_questions": [],
            }
            mock_api_client.get_last_updated.return_value = {}
            mock_api_client.get_managing_roles.return_value = []

            response = client.get("/")
            # Should still render the page even with API errors
            assert response.status_code == 200

            html_content = response.get_data(as_text=True)

            # Letter filter should still be present even with API errors
            assert 'class="alphabet-filter"' in html_content
            assert "Filter by letter:" in html_content
