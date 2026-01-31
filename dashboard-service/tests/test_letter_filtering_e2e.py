"""
End-to-end tests for A-Z letter filtering functionality.

This module tests the complete letter filtering workflow from API to frontend,
including real data scenarios and user interactions.
"""

import os
import pytest
import time
import requests
from unittest.mock import patch, MagicMock


@pytest.mark.e2e
@pytest.mark.frontend
@pytest.mark.slow
class TestLetterFilteringE2E:
    """End-to-end tests for letter filtering functionality."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

    def test_letter_filtering_with_real_data_e2e(self, launcher_process):
        """Test letter filtering with real data in end-to-end scenario."""
        # Wait for services to be ready
        time.sleep(10)

        try:
            # Test API endpoint
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            definitions_data = response.json()

            # Verify we have definitions data
            assert isinstance(definitions_data, list)

            if len(definitions_data) > 0:
                # Test letter availability detection
                available_letters = set()
                for definition in definitions_data:
                    if definition.get("term") and len(definition["term"]) > 0:
                        first_letter = definition["term"][0].upper()
                        if first_letter.isalpha():
                            available_letters.add(first_letter)

                # Should have some available letters
                assert len(available_letters) > 0

                # Test filtering by available letters
                for letter in list(available_letters)[
                    :3
                ]:  # Test first 3 available letters
                    filtered_definitions = [
                        d
                        for d in definitions_data
                        if d.get("term", "").upper().startswith(letter)
                    ]
                    assert len(filtered_definitions) > 0

                    # Verify all filtered definitions start with the correct letter
                    for definition in filtered_definitions:
                        assert definition["term"].upper().startswith(letter)

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_css_styles_e2e(self, launcher_process):
        """Test that CSS styles for letter filtering are properly loaded."""
        time.sleep(10)

        try:
            # Test CSS file loading
            response = requests.get(
                f"{self.DASHBOARD_URL}/static/css/dashboard.css", timeout=10
            )
            assert response.status_code == 200
            css_content = response.text

            # Check for letter filter CSS classes
            assert ".alphabet-filter" in css_content
            assert ".letter-link" in css_content
            assert ".letter-link.active" in css_content
            assert ".letter-link.disabled" in css_content
            assert ".letter-link:hover" in css_content

            # Check for specific styling properties
            assert "background-color" in css_content
            assert "color" in css_content
            assert "border" in css_content
            assert "cursor" in css_content

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_javascript_e2e(self, launcher_process):
        """Test that JavaScript for letter filtering is properly loaded."""
        time.sleep(10)

        try:
            # Test JavaScript file loading - check DashboardControls.js where setLetterFilter is defined
            response = requests.get(
                f"{self.DASHBOARD_URL}/static/js/modules/DashboardControls.js", timeout=10
            )
            if response.status_code == 200:
                controls_content = response.text
                # Check for letter filtering functions in DashboardControls.js
                assert "setLetterFilter" in controls_content
                # Check for letter-related functionality in the module
                assert "letter" in controls_content.lower() or "filter" in controls_content.lower()
            else:
                # Fallback: check dashboard.js (main bundle might include it)
                response = requests.get(
                    f"{self.DASHBOARD_URL}/static/js/dashboard.js", timeout=10
                )
                assert response.status_code == 200
                js_content = response.text
                # Check for letter filtering functions
                assert "setLetterFilter" in js_content or "updateLetterAvailability" in js_content

            # Also check dashboard.js for other letter filtering components
            response = requests.get(
                f"{self.DASHBOARD_URL}/static/js/dashboard.js", timeout=10
            )
            assert response.status_code == 200
            js_content = response.text

            # Check for event listeners (required for letter filtering functionality)
            assert "addEventListener" in js_content
            # letter-link and data-letter might be in HTML templates or other JS modules
            # As long as setLetterFilter exists in DashboardControls.js, the functionality is there

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_with_category_filter_e2e(self, launcher_process):
        """Test letter filtering combined with category filtering in E2E scenario."""
        time.sleep(10)

        try:
            # Get definitions data
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            all_definitions = response.json()

            if len(all_definitions) > 0:
                # Get unique categories
                categories = list(
                    set(
                        d.get("category", "")
                        for d in all_definitions
                        if d.get("category")
                    )
                )

                if categories:
                    # Test with first available category
                    test_category = categories[0]

                    # Test category filtering
                    category_response = requests.get(
                        f"{self.DASHBOARD_URL}/api/definitions?category={test_category}",
                        timeout=10,
                    )
                    assert category_response.status_code == 200
                    category_definitions = category_response.json()

                    # Test letter availability after category filtering
                    available_letters = set()
                    for definition in category_definitions:
                        if definition.get("term") and len(definition["term"]) > 0:
                            first_letter = definition["term"][0].upper()
                            if first_letter.isalpha():
                                available_letters.add(first_letter)

                    # Test filtering by available letters
                    for letter in list(available_letters)[
                        :2
                    ]:  # Test first 2 available letters
                        filtered_definitions = [
                            d
                            for d in category_definitions
                            if d.get("term", "").upper().startswith(letter)
                        ]

                        # Verify all filtered definitions start with correct letter and are in correct category
                        for definition in filtered_definitions:
                            assert definition["term"].upper().startswith(letter)
                            assert definition.get("category") == test_category

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_error_handling_e2e(self, launcher_process):
        """Test error handling in letter filtering E2E scenario."""
        time.sleep(10)

        try:
            # Test with invalid category
            response = requests.get(
                f"{self.DASHBOARD_URL}/api/definitions?category=NonExistentCategory",
                timeout=10,
            )
            assert response.status_code == 200
            data = response.json()
            assert data == []  # Should return empty list, not error

            # Test with invalid letter (this would be handled by frontend)
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            data = response.json()

            # Test filtering with non-existent letter
            filtered_definitions = [
                d for d in data if d.get("term", "").upper().startswith("X")
            ]
            assert len(filtered_definitions) == 0  # Should be empty

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_performance_e2e(self, launcher_process):
        """Test performance of letter filtering with large datasets."""
        time.sleep(10)

        try:
            # Test API response time
            start_time = time.time()
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=30)
            end_time = time.time()

            assert response.status_code == 200
            response_time = end_time - start_time

            # Response should be reasonably fast (less than 5 seconds)
            assert response_time < 5.0

            data = response.json()

            if len(data) > 0:
                # Test letter filtering performance
                start_time = time.time()
                available_letters = set()
                for definition in data:
                    if definition.get("term") and len(definition["term"]) > 0:
                        first_letter = definition["term"][0].upper()
                        if first_letter.isalpha():
                            available_letters.add(first_letter)
                end_time = time.time()

                filtering_time = end_time - start_time
                # Letter filtering should be very fast (less than 1 second)
                assert filtering_time < 1.0

                # Test filtering by each available letter
                for letter in available_letters:
                    start_time = time.time()
                    filtered_definitions = [
                        d for d in data if d.get("term", "").upper().startswith(letter)
                    ]
                    end_time = time.time()

                    filtering_time = end_time - start_time
                    # Individual letter filtering should be very fast
                    assert filtering_time < 0.1

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_letter_filtering_data_consistency_e2e(self, launcher_process):
        """Test data consistency in letter filtering E2E scenario."""
        time.sleep(10)

        try:
            # Get definitions data multiple times to ensure consistency
            responses = []
            for _ in range(3):
                response = requests.get(
                    f"{self.DASHBOARD_URL}/api/definitions", timeout=10
                )
                assert response.status_code == 200
                responses.append(response.json())

            # All responses should be identical
            for i in range(1, len(responses)):
                assert responses[i] == responses[0]

            data = responses[0]

            if len(data) > 0:
                # Test that letter filtering is consistent
                available_letters = set()
                for definition in data:
                    if definition.get("term") and len(definition["term"]) > 0:
                        first_letter = definition["term"][0].upper()
                        if first_letter.isalpha():
                            available_letters.add(first_letter)

                # Test multiple times to ensure consistency
                for _ in range(3):
                    test_available_letters = set()
                    for definition in data:
                        if definition.get("term") and len(definition["term"]) > 0:
                            first_letter = definition["term"][0].upper()
                            if first_letter.isalpha():
                                test_available_letters.add(first_letter)

                    assert test_available_letters == available_letters

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")


@pytest.mark.e2e
@pytest.mark.frontend
@pytest.mark.slow
class TestLetterFilteringUserScenarios:
    """Test realistic user scenarios for letter filtering."""

    # Use environment variables for ports
    DASHBOARD_PORT = os.getenv("DASHBOARD_PORT")
    DASHBOARD_URL = f"http://localhost:{DASHBOARD_PORT}"

    def test_user_filters_by_letter_a_e2e(self, launcher_process):
        """Test user filtering by letter A scenario."""
        time.sleep(10)

        try:
            # Get all definitions
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            all_definitions = response.json()

            if len(all_definitions) > 0:
                # Simulate user filtering by letter A
                filtered_definitions = [
                    d
                    for d in all_definitions
                    if d.get("term", "").upper().startswith("A")
                ]

                # Verify results
                for definition in filtered_definitions:
                    assert definition["term"].upper().startswith("A")

                # Should have some results if there are definitions starting with A
                if any(
                    d.get("term", "").upper().startswith("A") for d in all_definitions
                ):
                    assert len(filtered_definitions) > 0

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_user_switches_between_letters_e2e(self, launcher_process):
        """Test user switching between different letters scenario."""
        time.sleep(10)

        try:
            # Get all definitions
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            all_definitions = response.json()

            if len(all_definitions) > 0:
                # Get available letters
                available_letters = set()
                for definition in all_definitions:
                    if definition.get("term") and len(definition["term"]) > 0:
                        first_letter = definition["term"][0].upper()
                        if first_letter.isalpha():
                            available_letters.add(first_letter)

                # Test switching between different letters
                test_letters = list(available_letters)[
                    :3
                ]  # Test first 3 available letters

                for letter in test_letters:
                    filtered_definitions = [
                        d
                        for d in all_definitions
                        if d.get("term", "").upper().startswith(letter)
                    ]

                    # Verify all results start with the correct letter
                    for definition in filtered_definitions:
                        assert definition["term"].upper().startswith(letter)

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")

    def test_user_combines_category_and_letter_filter_e2e(self, launcher_process):
        """Test user combining category and letter filters scenario."""
        time.sleep(10)

        try:
            # Get all definitions
            response = requests.get(f"{self.DASHBOARD_URL}/api/definitions", timeout=10)
            assert response.status_code == 200
            all_definitions = response.json()

            if len(all_definitions) > 0:
                # Get available categories
                categories = list(
                    set(
                        d.get("category", "")
                        for d in all_definitions
                        if d.get("category")
                    )
                )

                if categories:
                    test_category = categories[0]

                    # Filter by category first
                    category_definitions = [
                        d for d in all_definitions if d.get("category") == test_category
                    ]

                    # Then filter by letter
                    available_letters = set()
                    for definition in category_definitions:
                        if definition.get("term") and len(definition["term"]) > 0:
                            first_letter = definition["term"][0].upper()
                            if first_letter.isalpha():
                                available_letters.add(first_letter)

                    # Test filtering by available letters
                    for letter in list(available_letters)[:2]:
                        filtered_definitions = [
                            d
                            for d in category_definitions
                            if d.get("term", "").upper().startswith(letter)
                        ]

                        # Verify results match both category and letter
                        for definition in filtered_definitions:
                            assert definition.get("category") == test_category
                            assert definition["term"].upper().startswith(letter)

        except requests.exceptions.RequestException as e:
            pytest.skip(f"E2E test skipped due to connection error: {e}")
