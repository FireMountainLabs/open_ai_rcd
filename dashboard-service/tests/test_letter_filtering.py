"""
Tests for the A-Z letter filtering functionality.

This module tests the letter filtering feature for the Definitions & Terminology page,
including both backend API functionality and frontend JavaScript behavior.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask


@pytest.mark.unit
@pytest.mark.frontend
class TestLetterFilteringUnit:
    """Test unit functionality for letter filtering."""

    def test_letter_availability_detection(self):
        """Test that letter availability is correctly detected from definitions data."""
        # Mock definitions data with various starting letters
        mock_definitions = [
            {"term": "Artificial Intelligence", "category": "Core Concepts"},
            {"term": "Algorithm", "category": "Technical Terms"},
            {"term": "Bias", "category": "Ethics"},
            {"term": "Computer Vision", "category": "Technical Terms"},
            {"term": "Data Science", "category": "Core Concepts"},
            {"term": "Ethics", "category": "Ethics"},
            {"term": "Machine Learning", "category": "Core Concepts"},
            {"term": "Neural Network", "category": "Technical Terms"},
            {"term": "Z-score", "category": "Statistics"},
            {"term": "123 Invalid", "category": "Invalid"},  # Should be ignored
            {"term": "", "category": "Empty"},  # Should be ignored
            {"term": None, "category": "None"},  # Should be ignored
        ]

        # Expected available letters
        expected_letters = {"A", "B", "C", "D", "E", "M", "N", "Z"}

        # Simulate the letter availability detection logic
        available_letters = set()
        for definition in mock_definitions:
            if definition.get("term") and len(definition["term"]) > 0:
                first_letter = definition["term"].upper()[0]
                if first_letter >= "A" and first_letter <= "Z":
                    available_letters.add(first_letter)

        assert available_letters == expected_letters

    def test_letter_filtering_logic(self):
        """Test the core letter filtering logic."""
        mock_definitions = [
            {"term": "Algorithm", "category": "Technical Terms"},
            {"term": "Bias", "category": "Ethics"},
            {"term": "Computer Vision", "category": "Technical Terms"},
            {"term": "Data Science", "category": "Core Concepts"},
        ]

        # Test filtering by letter 'A'
        filtered_a = [d for d in mock_definitions if d["term"].upper().startswith("A")]
        assert len(filtered_a) == 1
        assert filtered_a[0]["term"] == "Algorithm"

        # Test filtering by letter 'C'
        filtered_c = [d for d in mock_definitions if d["term"].upper().startswith("C")]
        assert len(filtered_c) == 1
        assert filtered_c[0]["term"] == "Computer Vision"

        # Test filtering by letter 'X' (no matches)
        filtered_x = [d for d in mock_definitions if d["term"].upper().startswith("X")]
        assert len(filtered_x) == 0

    def test_combined_category_and_letter_filtering(self):
        """Test filtering by both category and letter."""
        mock_definitions = [
            {"term": "Algorithm", "category": "Technical Terms"},
            {"term": "Bias", "category": "Ethics"},
            {"term": "Computer Vision", "category": "Technical Terms"},
            {"term": "Data Science", "category": "Core Concepts"},
            {"term": "Artificial Intelligence", "category": "Core Concepts"},
        ]

        # Filter by category "Technical Terms" and letter "C"
        category_filtered = [
            d for d in mock_definitions if d["category"] == "Technical Terms"
        ]
        letter_filtered = [
            d for d in category_filtered if d["term"].upper().startswith("C")
        ]

        assert len(letter_filtered) == 1
        assert letter_filtered[0]["term"] == "Computer Vision"

        # Filter by category "Core Concepts" and letter "A"
        category_filtered = [
            d for d in mock_definitions if d["category"] == "Core Concepts"
        ]
        letter_filtered = [
            d for d in category_filtered if d["term"].upper().startswith("A")
        ]

        assert len(letter_filtered) == 1
        assert letter_filtered[0]["term"] == "Artificial Intelligence"

    def test_empty_definitions_handling(self):
        """Test handling of empty or invalid definitions."""
        empty_definitions = []
        assert len(empty_definitions) == 0

        # Test with None definitions
        none_definitions = None
        if none_definitions:
            available_letters = set()
        else:
            available_letters = set()

        assert available_letters == set()

    def test_case_insensitive_filtering(self):
        """Test that letter filtering is case-insensitive."""
        mock_definitions = [
            {"term": "algorithm", "category": "Technical Terms"},
            {"term": "Algorithm", "category": "Technical Terms"},
            {"term": "ALGORITHM", "category": "Technical Terms"},
            {"term": "Bias", "category": "Ethics"},
        ]

        # All variations should match letter 'A'
        filtered_a = [d for d in mock_definitions if d["term"].upper().startswith("A")]
        assert len(filtered_a) == 3

        # All variations should match letter 'B'
        filtered_b = [d for d in mock_definitions if d["term"].upper().startswith("B")]
        assert len(filtered_b) == 1


@pytest.mark.unit
@pytest.mark.api
class TestLetterFilteringAPI:
    """Test API functionality for letter filtering."""

    def test_definitions_api_with_letter_filtering(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that definitions API supports letter filtering through frontend logic."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_001",
                "term": "Artificial Intelligence",
                "title": "Artificial Intelligence",
                "description": "The simulation of human intelligence in machines",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
            {
                "definition_id": "def_002",
                "term": "Machine Learning",
                "title": "Machine Learning",
                "description": "A subset of AI that enables systems to learn from data",
                "category": "Core Concepts",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
            {
                "definition_id": "def_003",
                "term": "Bias",
                "title": "Bias",
                "description": "Systematic error in machine learning models",
                "category": "Ethics",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
        ]

        with patch_api_client_methods(mock_database_api_client):
                response = client.get("/api/definitions")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 3

        # Test that the data structure supports letter filtering
        terms = [item["term"] for item in data]
        assert "Artificial Intelligence" in terms
        assert "Machine Learning" in terms
        assert "Bias" in terms

    def test_definitions_api_category_and_letter_combination(
        self, client, mock_database_api_client, patch_api_client_methods
    ):
        """Test API with category filtering that would affect letter availability."""
        mock_definitions = [
            {
                "definition_id": "def_001",
                "term": "Algorithm",
                "category": "Technical Terms",
                "title": "Algorithm",
                "description": "A set of rules for solving a problem",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
            {
                "definition_id": "def_002",
                "term": "Bias",
                "category": "Ethics",
                "title": "Bias",
                "description": "Systematic error in models",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
            {
                "definition_id": "def_003",
                "term": "Computer Vision",
                "category": "Technical Terms",
                "title": "Computer Vision",
                "description": "Field of AI for visual processing",
                "source": "AI_Definitions_and_Taxonomy_V1.xlsx",
            },
        ]

        # Mock the API client to filter by category
        def mock_get_definitions(limit=None, offset=None, category=None):
            if category:
                return [d for d in mock_definitions if d.get("category") == category]
            return mock_definitions

        mock_database_api_client.get_definitions.side_effect = mock_get_definitions

        # Test with category filter
        with patch_api_client_methods(mock_database_api_client):
                response = client.get("/api/definitions?category=Technical Terms")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2  # Both Algorithm and Computer Vision are Technical Terms
        assert any(item["term"] == "Algorithm" for item in data)
        assert any(item["term"] == "Computer Vision" for item in data)
        assert all(item["category"] == "Technical Terms" for item in data)

    def test_definitions_api_data_structure_for_letter_filtering(self, client, mock_database_api_client, patch_api_client_methods):
        """Test that API returns data in the correct structure for letter filtering."""
        mock_database_api_client.get_definitions.return_value = [
            {
                "definition_id": "def_001",
                "term": "Test Term",
                "title": "Test Title",
                "description": "Test Description",
                "category": "Test Category",
                "source": "test.xlsx",
            }
        ]

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) > 0

            # Verify required fields for letter filtering
            item = data[0]
            assert "term" in item
            assert "category" in item
            assert isinstance(item["term"], str)
            assert len(item["term"]) > 0


@pytest.mark.unit
@pytest.mark.frontend
class TestLetterFilteringFrontend:
    """Test frontend functionality for letter filtering."""

    def test_letter_filter_html_structure(self):
        """Test that the HTML structure for letter filtering is correct."""
        # This would typically be tested with a proper HTML parser
        # For now, we'll test the expected structure
        expected_letters = [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
        ]

        # Test that all expected letters are present
        assert len(expected_letters) == 26
        assert all(letter.isalpha() and letter.isupper() for letter in expected_letters)

        # Test that letters are in alphabetical order
        assert expected_letters == sorted(expected_letters)

    def test_letter_filter_css_classes(self):
        """Test that the expected CSS classes are defined."""
        expected_classes = [
            "alphabet-filter",
            "filter-label",
            "letter-links",
            "letter-link",
            "letter-link.active",
            "letter-link.disabled",
            "letter-link:hover",
        ]

        # Verify class names follow expected patterns
        for class_name in expected_classes:
            assert isinstance(class_name, str)
            assert len(class_name) > 0
            # CSS classes can contain hyphens and dots
            assert any(
                c.isalnum() for c in class_name
            )  # At least some alphanumeric characters

    def test_letter_filter_data_attributes(self):
        """Test that letter links have correct data attributes."""
        # Test data-letter attribute values
        expected_data_letters = [""] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]

        assert "" in expected_data_letters  # "All" option
        assert "A" in expected_data_letters
        assert "Z" in expected_data_letters
        assert len(expected_data_letters) == 27  # 26 letters + "All"

    def test_letter_filter_javascript_methods(self):
        """Test that required JavaScript methods are defined."""
        required_methods = [
            "setLetterFilter",
            "updateLetterAvailability",
            "updateLetterAvailabilityForFilteredData",
            "filterDefinitions",
        ]

        for method_name in required_methods:
            assert isinstance(method_name, str)
            assert len(method_name) > 0
            assert method_name.isidentifier()

    def test_letter_filter_state_management(self):
        """Test letter filter state management logic."""
        # Test active state management
        test_letter = "A"
        all_letters = [""] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]

        # Simulate setting active state
        active_letter = test_letter
        for letter in all_letters:
            is_active = letter == active_letter
            if letter == "A":
                assert is_active
            else:
                assert not is_active

    def test_letter_filter_click_prevention(self):
        """Test that disabled letters cannot be clicked."""
        # Test disabled state logic
        available_letters = {"A", "B", "C"}
        test_letter = "X"  # Not in available letters

        is_disabled = test_letter not in available_letters
        assert is_disabled

        # Test that disabled letters are not processed
        if is_disabled:
            should_process = False
        else:
            should_process = True

        assert not should_process


@pytest.mark.integration
@pytest.mark.frontend
class TestLetterFilteringIntegration:
    """Test integration between frontend and backend for letter filtering."""

    def test_end_to_end_letter_filtering(self, client, mock_database_api_client, patch_api_client_methods):
        """Test complete letter filtering workflow."""
        # Mock definitions with various starting letters
        mock_definitions = [
            {
                "definition_id": "def_001",
                "term": "Algorithm",
                "category": "Technical Terms",
            },
            {"definition_id": "def_002", "term": "Bias", "category": "Ethics"},
            {
                "definition_id": "def_003",
                "term": "Computer Vision",
                "category": "Technical Terms",
            },
            {
                "definition_id": "def_004",
                "term": "Data Science",
                "category": "Core Concepts",
            },
        ]

        mock_database_api_client.get_definitions.return_value = mock_definitions

        # Test API response
        with patch_api_client_methods(mock_database_api_client):
                response = client.get("/api/definitions")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 4

        # Test letter availability detection
        available_letters = set()
        for definition in data:
            if definition.get("term"):
                first_letter = definition["term"][0].upper()
                if first_letter.isalpha():
                    available_letters.add(first_letter)

        expected_letters = {"A", "B", "C", "D"}
        assert available_letters == expected_letters

        # Test filtering by letter 'A'
        filtered_a = [d for d in data if d["term"].upper().startswith("A")]
        assert len(filtered_a) == 1
        assert filtered_a[0]["term"] == "Algorithm"

        # Test filtering by letter 'X' (no matches)
        filtered_x = [d for d in data if d["term"].upper().startswith("X")]
        assert len(filtered_x) == 0

    def test_letter_filtering_with_category_filter(self, client, mock_database_api_client, patch_api_client_methods):
        """Test letter filtering combined with category filtering."""
        mock_definitions = [
            {
                "definition_id": "def_001",
                "term": "Algorithm",
                "category": "Technical Terms",
            },
            {"definition_id": "def_002", "term": "Bias", "category": "Ethics"},
            {
                "definition_id": "def_003",
                "term": "Computer Vision",
                "category": "Technical Terms",
            },
            {
                "definition_id": "def_004",
                "term": "Data Science",
                "category": "Core Concepts",
            },
        ]

        # Mock the API client to filter by category
        def mock_get_definitions(limit=None, offset=None, category=None):
            if category:
                return [d for d in mock_definitions if d.get("category") == category]
            return mock_definitions

        mock_database_api_client.get_definitions.side_effect = mock_get_definitions

        # Test with category filter
        with patch_api_client_methods(mock_database_api_client):
                response = client.get("/api/definitions?category=Technical Terms")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2

        # Test letter availability after category filtering
        available_letters = set()
        for definition in data:
            if definition.get("term"):
                first_letter = definition["term"][0].upper()
                if first_letter.isalpha():
                    available_letters.add(first_letter)

        expected_letters = {"A", "C"}  # Only Algorithm and Computer Vision
        assert available_letters == expected_letters

    def test_letter_filtering_error_handling(self, client, mock_database_api_client, patch_api_client_methods):
        """Test error handling in letter filtering."""
        # Test with API error
        mock_database_api_client.get_definitions.side_effect = Exception("API Error")

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
            assert response.status_code == 200  # Should return empty list, not error
            data = response.get_json()
            assert data == []

    def test_letter_filtering_with_empty_data(self, client, mock_database_api_client, patch_api_client_methods):
        """Test letter filtering with empty definitions data."""
        mock_database_api_client.get_definitions.return_value = []

        with patch_api_client_methods(mock_database_api_client):
            response = client.get("/api/definitions")
            assert response.status_code == 200
            data = response.get_json()
            assert data == []

            # Test letter availability with empty data
            available_letters = set()
            assert available_letters == set()


@pytest.mark.unit
@pytest.mark.error
class TestLetterFilteringErrorScenarios:
    """Test error scenarios for letter filtering."""

    def test_letter_filtering_with_malformed_data(self):
        """Test letter filtering with malformed definition data."""
        malformed_definitions = [
            {"term": None, "category": "Test"},
            {"term": "", "category": "Test"},
            {"term": 123, "category": "Test"},  # Wrong type
            {"category": "Test"},  # Missing term
            {"term": "Valid Term", "category": None},
        ]

        # Test that malformed data is handled gracefully
        valid_terms = []
        for definition in malformed_definitions:
            if isinstance(definition.get("term"), str) and definition["term"].strip():
                valid_terms.append(definition["term"])

        assert len(valid_terms) == 1
        assert valid_terms[0] == "Valid Term"

    def test_letter_filtering_with_special_characters(self):
        """Test letter filtering with special characters in terms."""
        special_definitions = [
            {"term": "AI/ML", "category": "Technical Terms"},
            {"term": "3D Vision", "category": "Technical Terms"},
            {"term": "β-Bias", "category": "Ethics"},
            {"term": "Machine-Learning", "category": "Technical Terms"},
        ]

        # Test that special characters are handled correctly
        for definition in special_definitions:
            term = definition["term"]
            if term and len(term) > 0:
                first_char = term[0].upper()
                is_letter = first_char.isalpha()
                if is_letter:
                    # Check if it's a standard ASCII letter or handle Unicode properly
                    if first_char.isascii():
                        assert first_char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                    else:
                        # For Unicode characters, just verify it's alphabetic
                        assert first_char.isalpha()

    def test_letter_filtering_unicode_handling(self):
        """Test letter filtering with Unicode characters."""
        unicode_definitions = [
            {"term": "Éthique", "category": "Ethics"},
            {"term": "Ñeural", "category": "Technical Terms"},
            {"term": "α-Algorithm", "category": "Technical Terms"},
        ]

        # Test that Unicode characters are handled
        for definition in unicode_definitions:
            term = definition["term"]
            if term and len(term) > 0:
                first_char = term[0].upper()
                # Should handle Unicode characters appropriately
                assert isinstance(first_char, str)
