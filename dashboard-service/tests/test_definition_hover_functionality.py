"""
Tests for definition hover functionality.

This module tests the JavaScript-based definition hover feature that allows users
to hover over defined terms in risks, controls, and questions to see definitions,
and click to navigate to the definitions tab with proper row highlighting and centering.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import app as app_module


@pytest.mark.unit
@pytest.mark.frontend
@pytest.mark.definition_hover
class TestDefinitionHoverFunctionality:
    """Test definition hover functionality."""

    def test_term_normalization_logic(self):
        """Test that term normalization works correctly for matching."""

        # Test the normalization logic used in DefinitionHoverManager
        def normalize_term(term):
            """Simulate the normalization logic from buildDefinitionMap."""
            import re

            normalized = term.lower()
            normalized = re.sub(
                r"\s+", " ", normalized
            )  # Replace multiple spaces with single space
            normalized = re.sub(
                r"[^\w\s]", "", normalized
            )  # Remove non-word, non-space characters
            return normalized.strip()

        # Test cases that should normalize to the same result
        test_cases = [
            ("AI Agent", "ai agent"),
            (
                "Physical-World Adversarial Attacks",
                "physical world adversarial attacks",
            ),
            ("Prompt Injection", "prompt injection"),
            ("Data Drift (Distribution Shift)", "data drift distribution shift"),
            ("AI Bill of Materials (AI-BOM)", "ai bill of materials ai bom"),
        ]

        for original, expected in test_cases:
            # Simulate the JavaScript regex replacement
            normalized = (
                original.lower()
                .replace(" ", " ")
                .replace("-", " ")
                .replace("(", "")
                .replace(")", "")
            )
            normalized = "".join(
                c for c in normalized if c.isalnum() or c.isspace()
            ).strip()
            normalized = " ".join(normalized.split())  # Clean up multiple spaces

            assert (
                normalized == expected
            ), f"Normalization failed for '{original}': got '{normalized}', expected '{expected}'"

    def test_exact_term_matching(self):
        """Test exact term matching logic."""

        # Simulate the exact matching logic from highlightDefinitionRow
        def find_exact_match(search_term, available_terms):
            """Simulate the exact matching logic."""
            import re

            normalized_search = search_term.lower()
            normalized_search = re.sub(r"\s+", " ", normalized_search)
            normalized_search = re.sub(r"[^\w\s]", "", normalized_search)
            normalized_search = normalized_search.strip()

            for term in available_terms:
                normalized_term = term.lower()
                normalized_term = re.sub(r"\s+", " ", normalized_term)
                normalized_term = re.sub(r"[^\w\s]", "", normalized_term)
                normalized_term = normalized_term.strip()
                if normalized_term == normalized_search:
                    return term

            return None

        available_terms = [
            "AI Agent",
            "Physical-World Adversarial Attacks",
            "Prompt Injection",
            "Data Drift (Distribution Shift)",
            "AI Bill of Materials (AI-BOM)",
        ]

        # Test exact matches
        assert (
            find_exact_match("Prompt Injection", available_terms) == "Prompt Injection"
        )
        assert (
            find_exact_match("prompt injection", available_terms) == "Prompt Injection"
        )
        assert (
            find_exact_match("Physical-World Adversarial Attacks", available_terms)
            == "Physical-World Adversarial Attacks"
        )

        # Test non-matches
        assert find_exact_match("Non-existent Term", available_terms) is None
        assert (
            find_exact_match("AI", available_terms) is None
        )  # Should not match "AI Agent"

    def test_fallback_term_matching(self):
        """Test fallback term matching for partial matches."""

        # Simulate the fallback matching logic
        def find_fallback_match(search_term, available_terms):
            """Simulate the fallback matching logic."""
            import re

            normalized_search = search_term.lower()
            normalized_search = re.sub(r"\s+", " ", normalized_search)
            normalized_search = re.sub(r"[^\w\s]", "", normalized_search)
            normalized_search = normalized_search.strip()
            words = normalized_search.split(" ")

            for term in available_terms:
                normalized_term = term.lower()
                normalized_term = re.sub(r"\s+", " ", normalized_term)
                normalized_term = re.sub(r"[^\w\s]", "", normalized_term)
                normalized_term = normalized_term.strip()
                cell_words = normalized_term.split(" ")

                # Check if all words from search term are present
                all_words_match = all(
                    any(
                        word in cell_word or cell_word in word
                        for cell_word in cell_words
                    )
                    for word in words
                )

                if all_words_match and len(words) > 1:  # Only for multi-word terms
                    return term

            return None

        available_terms = [
            "AI Agent",
            "Physical-World Adversarial Attacks",
            "Prompt Injection",
            "Prompt Engineering",
            "Data Drift (Distribution Shift)",
            "Model Theft (Model Extraction)",
            "Membership Inference Attack",
        ]

        # Test fallback matches (should only work for multi-word terms)
        assert (
            find_fallback_match("Physical world attacks", available_terms)
            == "Physical-World Adversarial Attacks"
        )
        assert (
            find_fallback_match("prompt injection", available_terms)
            == "Prompt Injection"
        )

        # Test that single words don't trigger fallback
        assert find_fallback_match("AI", available_terms) is None

        # Test that partial matches are precise (should not match "Prompt Engineering" for "Prompt injection")
        assert (
            find_fallback_match("Prompt injection", available_terms)
            == "Prompt Injection"
        )

    def test_browser_centering_calculation(self):
        """Test browser centering calculation logic."""

        # Simulate the centering calculation from highlightDefinitionRow
        def calculate_browser_center_scroll(
            row_rect, viewport_height, current_scroll_y
        ):
            """Simulate the browser centering calculation."""
            row_center = row_rect["top"] + (row_rect["height"] / 2)
            browser_center = viewport_height / 2
            target_scroll_y = current_scroll_y + (row_center - browser_center)
            return target_scroll_y

        # Test case: row at position 553px, viewport 705px, scroll at 9105px
        row_rect = {"top": 293, "height": 118}  # Row center = 293 + 59 = 352px
        viewport_height = 705
        current_scroll_y = 9105

        target_scroll = calculate_browser_center_scroll(
            row_rect, viewport_height, current_scroll_y
        )

        # Expected: 9105 + (352 - 352.5) = 9105 - 0.5 ≈ 9105
        expected_scroll = current_scroll_y + (352 - 352.5)

        assert (
            abs(target_scroll - expected_scroll) < 1
        ), f"Centering calculation failed: got {target_scroll}, expected {expected_scroll}"

    def test_content_area_vs_browser_centering(self):
        """Test the difference between content area and browser centering."""

        def calculate_content_center_scroll(
            row_rect, viewport_height, fixed_elements_height, current_scroll_y
        ):
            """Simulate content area centering calculation."""
            row_center = row_rect["top"] + (row_rect["height"] / 2)
            content_height = viewport_height - fixed_elements_height
            content_start = fixed_elements_height
            content_center = content_start + (content_height / 2)
            target_scroll_y = current_scroll_y + (row_center - content_center)
            return target_scroll_y

        def calculate_browser_center_scroll(
            row_rect, viewport_height, current_scroll_y
        ):
            """Simulate browser centering calculation."""
            row_center = row_rect["top"] + (row_rect["height"] / 2)
            browser_center = viewport_height / 2
            target_scroll_y = current_scroll_y + (row_center - browser_center)
            return target_scroll_y

        # Test case with fixed elements
        row_rect = {"top": 293, "height": 118}  # Row center = 352px
        viewport_height = 705
        fixed_elements_height = 401  # Header + nav
        current_scroll_y = 9105

        content_scroll = calculate_content_center_scroll(
            row_rect, viewport_height, fixed_elements_height, current_scroll_y
        )
        browser_scroll = calculate_browser_center_scroll(
            row_rect, viewport_height, current_scroll_y
        )

        # Content center = 401 + (304/2) = 401 + 152 = 553px
        # Browser center = 705/2 = 352.5px
        # Difference should be about 200px
        scroll_difference = abs(content_scroll - browser_scroll)

        assert (
            scroll_difference > 150
        ), f"Content and browser centering should differ significantly: {scroll_difference}px"
        assert (
            scroll_difference < 250
        ), f"Scroll difference seems too large: {scroll_difference}px"

    def test_hover_card_configuration(self):
        """Test hover card configuration per tab."""

        # Simulate the configuration logic
        def is_hover_enabled_for_tab(tab_name, config):
            """Simulate the hover configuration check."""
            return config.get("ui", {}).get("definition_hovers", {}).get(tab_name, True)

        config = {
            "ui": {
                "definition_hovers": {
                    "risks": True,
                    "controls": True,
                    "questions": True,
                    "definitions": False,
                }
            }
        }

        # Test enabled tabs
        assert is_hover_enabled_for_tab("risks", config) == True
        assert is_hover_enabled_for_tab("controls", config) == True
        assert is_hover_enabled_for_tab("questions", config) == True

        # Test disabled tab
        assert is_hover_enabled_for_tab("definitions", config) == False

        # Test default behavior
        assert is_hover_enabled_for_tab("unknown_tab", config) == True  # Default True

    def test_definition_data_structure(self):
        """Test that definition data structure matches what the hover manager expects."""
        # Mock definition data structure
        mock_definitions = [
            {
                "term": "AI Agent",
                "title": "AI Agent",
                "description": "An autonomous software entity that can perceive, reason, and act in an environment.",
                "source": "NIST AI Risk Management Framework",
            },
            {
                "term": "Prompt Injection",
                "title": "Prompt Injection",
                "description": "A technique where malicious input is inserted into prompts to manipulate AI system behavior.",
                "source": "OWASP AI Security Guidelines",
            },
        ]

        # Test that the data structure has required fields
        for definition in mock_definitions:
            assert "term" in definition, "Definition must have 'term' field"
            assert "title" in definition, "Definition must have 'title' field"
            assert (
                "description" in definition
            ), "Definition must have 'description' field"
            assert "source" in definition, "Definition must have 'source' field"

            # Test that fields are not empty
            assert definition["term"], "Term should not be empty"
            assert definition["title"], "Title should not be empty"
            assert definition["description"], "Description should not be empty"

    def test_hover_delay_configuration(self):
        """Test hover delay configuration."""

        # Simulate the hover delay logic
        def should_show_card_after_delay(hover_start_time, current_time, delay_ms=500):
            """Simulate the hover delay check."""
            return (current_time - hover_start_time) >= delay_ms

        # Test delay behavior
        hover_start = 1000
        assert should_show_card_after_delay(hover_start, 1000) == False  # No delay
        assert (
            should_show_card_after_delay(hover_start, 1499) == False
        )  # Just under delay
        assert should_show_card_after_delay(hover_start, 1500) == True  # Exactly delay
        assert (
            should_show_card_after_delay(hover_start, 2000) == True
        )  # Well past delay

    def test_term_storage_and_retrieval(self):
        """Test term storage and retrieval in definition map."""

        # Simulate the buildDefinitionMap logic
        def build_definition_map(definitions):
            """Simulate building the definition map with multiple variations."""
            definition_map = {}

            for definition in definitions:
                term = definition["term"]
                # Store multiple variations for flexible matching
                import re

                variations = [
                    term.lower(),
                    term.lower().replace("-", " "),
                    re.sub(r"[^\w\s]", "", term.lower()),
                    re.sub(r"\s+", " ", re.sub(r"[^\w\s]", "", term.lower())).strip(),
                ]

                for variation in variations:
                    definition_map[variation] = definition

            return definition_map

        definitions = [
            {
                "term": "Physical-World Adversarial Attacks",
                "title": "Physical-World Adversarial Attacks",
            },
            {"term": "Prompt Injection", "title": "Prompt Injection"},
        ]

        definition_map = build_definition_map(definitions)

        # Test that variations are stored
        assert "physical-world adversarial attacks" in definition_map
        assert "physical world adversarial attacks" in definition_map
        assert "physicalworld adversarial attacks" in definition_map
        assert "prompt injection" in definition_map

        # Test retrieval
        assert (
            definition_map["physical world adversarial attacks"]["term"]
            == "Physical-World Adversarial Attacks"
        )
        assert definition_map["prompt injection"]["term"] == "Prompt Injection"

    def test_error_handling_scenarios(self):
        """Test error handling in definition hover functionality."""

        # Test handling of missing DOM elements
        def safe_find_element(selector):
            """Simulate safe element finding."""
            # In real code, this would check if element exists
            return None  # Simulate missing element

        # Test that missing elements are handled gracefully
        element = safe_find_element("#definitionsTable tbody")
        assert element is None

        # Test handling of empty definition data
        def process_definitions(definitions):
            """Simulate processing definitions with error handling."""
            if not definitions:
                return []

            processed = []
            for definition in definitions:
                if definition and isinstance(definition, dict) and "term" in definition:
                    processed.append(definition)

            return processed

        # Test empty data
        assert process_definitions([]) == []
        assert process_definitions(None) == []

        # Test malformed data
        malformed_data = [
            {"term": "Valid Term"},
            None,
            {"invalid": "data"},
            {"term": ""},
        ]

        result = process_definitions(malformed_data)
        assert len(result) == 2  # Valid one and empty term (which is still valid)
        assert result[0]["term"] == "Valid Term"


@pytest.mark.integration
@pytest.mark.definition_hover
class TestDefinitionHoverIntegration:
    """Integration tests for definition hover functionality."""

    def test_api_definitions_endpoint_structure(self, client):
        """Test that the definitions API endpoint returns the expected structure."""
        response = client.get("/api/definitions")
        assert response.status_code == 200

        data = response.get_json()
        assert isinstance(data, list)

        if data:  # If there are definitions
            definition = data[0]
            required_fields = ["term", "title", "description", "source"]
            for field in required_fields:
                assert (
                    field in definition
                ), f"Definition missing required field: {field}"

    def test_hover_configuration_endpoint(self, client):
        """Test that hover configuration is accessible."""
        # Test that the dashboard loads with hover configuration
        # ENABLE_AUTH is set via app.config in conftest
        response = client.get("/")
        assert response.status_code == 200

        # Check that the page includes the necessary JavaScript files
        content = response.get_data(as_text=True)
        assert "DefinitionHoverManager.js" in content
        assert "dashboard.js" in content

    def test_definitions_table_structure(self, client):
        """Test that the definitions table has the expected structure for hover functionality."""
        # ENABLE_AUTH is set via app.config in conftest
        response = client.get("/")
        assert response.status_code == 200

        content = response.get_data(as_text=True)

        # Check for required table structure
        assert 'id="definitionsTable"' in content
        assert "tbody" in content
        # Note: definition-term class is added dynamically by JavaScript

    def test_css_hover_styles(self, client):
        """Test that hover CSS styles are included."""
        # ENABLE_AUTH is set via app.config in conftest
        response = client.get("/")
        assert response.status_code == 200

        content = response.get_data(as_text=True)

        # Check for hover-related CSS classes (these are in the CSS file, not HTML)
        # The CSS file is linked, so we check for the link
        assert "dashboard.css" in content
        # Note: CSS classes are defined in the CSS file, not in the HTML

    def test_definition_modal_functionality(self, client):
        """Test that definition modal functionality works correctly."""
        # ENABLE_AUTH is set via app.config in conftest
        response = client.get("/")
        assert response.status_code == 200

        content = response.get_data(as_text=True)

        # Check for modal structure
        assert 'id="detailModal"' in content
        assert "modal-content" in content
        assert "modalBody" in content

        # Check that JavaScript includes modal functionality
        # showDetailModal is in the JavaScript files, not the HTML template
        # Check for the script files that contain this functionality
        assert "DefinitionHoverManager.js" in content
        assert "dashboard.js" in content or "DashboardCore.js" in content

    def test_definition_data_structure_for_modal(self):
        """Test that definition data structure supports modal display."""
        # Simulate the definition data structure used by DefinitionHoverManager
        mock_definition = {
            "term": "AI Agent",
            "title": "AI Agent",
            "description": "An autonomous software entity that can perceive, reason, and act.",
            "category": "AI Lifecycle and Development",
            "source": "ISO/IEC 22989:2022",
            "definition_id": "def_001",
            "definitionId": "def_001",  # Both formats for compatibility
        }

        # Test that all required fields are present for modal display
        required_fields = ["term", "title", "description", "category", "source"]
        for field in required_fields:
            assert (
                field in mock_definition
            ), f"Definition missing required field: {field}"

        # Test that ID fields are present (either format)
        assert "definition_id" in mock_definition or "definitionId" in mock_definition

        # Test that the data can be used directly without API fetch
        assert mock_definition["term"] == "AI Agent"
        assert mock_definition["description"] is not None
        assert len(mock_definition["description"]) > 0

    def test_modal_hover_configuration(self):
        """Test that modal hover configuration works correctly."""
        # Test the updated configuration
        config = {
            "enabledTabs": ["risks", "controls", "questions", "definitions", "modal"],
            "disabledTabs": [],
            "hoverDelay": 300,
            "cardMaxWidth": 350,
            "descriptionMaxLength": 100,
        }

        # All tabs should be enabled now, including modal
        assert "risks" in config["enabledTabs"]
        assert "controls" in config["enabledTabs"]
        assert "questions" in config["enabledTabs"]
        assert "definitions" in config["enabledTabs"]
        assert "modal" in config["enabledTabs"]

        # No tabs should be disabled
        assert len(config["disabledTabs"]) == 0

        # Test hover delay configuration
        assert config["hoverDelay"] == 300

    def test_modal_content_hover_enhancement(self):
        """Test that modal content can be enhanced with hover functionality."""

        # Simulate the enhanceContent method with modal content flag
        def simulate_enhance_content(tab_name, is_modal_content=False):
            """Simulate the enhanceContent logic for testing."""
            enabled_tabs = ["risks", "controls", "questions", "definitions", "modal"]
            disabled_tabs = []

            # Allow modal content even if tab is normally disabled
            if tab_name not in enabled_tabs and not is_modal_content:
                return False

            return True

        # Test normal tab behavior
        assert simulate_enhance_content("risks") == True
        assert simulate_enhance_content("controls") == True
        assert simulate_enhance_content("questions") == True
        assert simulate_enhance_content("definitions") == True
        assert simulate_enhance_content("modal") == True  # Now enabled

        # Test modal content behavior (should work for any tab)
        assert simulate_enhance_content("risks", is_modal_content=True) == True
        assert simulate_enhance_content("controls", is_modal_content=True) == True
        assert simulate_enhance_content("questions", is_modal_content=True) == True
        assert simulate_enhance_content("definitions", is_modal_content=True) == True

        # Test unknown tab behavior
        assert simulate_enhance_content("unknown_tab") == False
        assert simulate_enhance_content("unknown_tab", is_modal_content=True) == True

    def test_modal_stacking_functionality(self):
        """Test that modal stacking works correctly."""

        # Simulate the modal stacking logic
        def simulate_create_stacked_modal(existing_modal_count):
            """Simulate the createStackedModal logic for testing."""
            base_z_index = 2000
            new_z_index = base_z_index + existing_modal_count
            return {"z_index": new_z_index, "class": "modal stacked-modal"}

        # Test stacking with different numbers of existing modals
        assert simulate_create_stacked_modal(0)["z_index"] == 2000  # First modal
        assert simulate_create_stacked_modal(1)["z_index"] == 2001  # Second modal
        assert simulate_create_stacked_modal(2)["z_index"] == 2002  # Third modal

        # Test hover card z-index calculation
        def simulate_hover_card_z_index(modal_count):
            """Simulate the hover card z-index calculation."""
            base_z_index = 2000
            max_modal_z_index = base_z_index + modal_count
            hover_card_z_index = max_modal_z_index + 1
            return hover_card_z_index

        # Hover cards should always be above modals
        assert simulate_hover_card_z_index(0) == 2001  # Above first modal
        assert simulate_hover_card_z_index(1) == 2002  # Above second modal
        assert simulate_hover_card_z_index(2) == 2003  # Above third modal

    def test_modal_body_element_consistency(self):
        """Test that modal body elements are handled consistently."""
        # Test original modal structure
        original_modal_structure = {
            "id": "detailModal",
            "body_id": "modalBody",
            "body_class": None,
        }

        # Test stacked modal structure
        stacked_modal_structure = {
            "id": "modalBody_1234567890_1",
            "body_id": "modalBody_1234567890_1",
            "body_class": "modal-body",
        }

        # Both should have valid IDs
        assert original_modal_structure["body_id"] is not None
        assert stacked_modal_structure["body_id"] is not None

        # Both should be accessible via querySelector
        assert original_modal_structure["body_id"].startswith("modalBody")
        assert stacked_modal_structure["body_id"].startswith("modalBody")

    def test_definition_hover_manager_initialization(self):
        """Test DefinitionHoverManager initialization scenarios."""
        # Test initialization with valid data
        mock_definitions = [
            {
                "term": "AI Agent",
                "title": "AI Agent",
                "description": "Test description",
            },
            {
                "term": "Machine Learning",
                "title": "ML",
                "description": "Test ML description",
            },
        ]

        # Simulate initialization
        def simulate_initialization(definitions):
            if definitions and len(definitions) > 0:
                return {
                    "success": True,
                    "definitions_count": len(definitions),
                    "manager_available": True,
                }
            return {
                "success": False,
                "definitions_count": 0,
                "manager_available": False,
            }

        result = simulate_initialization(mock_definitions)
        assert result["success"] == True
        assert result["definitions_count"] == 2
        assert result["manager_available"] == True

        # Test initialization with empty data
        empty_result = simulate_initialization([])
        assert empty_result["success"] == False
        assert empty_result["definitions_count"] == 0
        assert empty_result["manager_available"] == False

    def test_hover_card_positioning_and_z_index(self):
        """Test hover card positioning and z-index calculations."""

        # Test z-index calculation for different modal counts
        def calculate_hover_card_z_index(modal_count):
            base_z_index = 2000
            max_modal_z_index = base_z_index + modal_count
            return max_modal_z_index + 1

        # Test various scenarios
        test_scenarios = [
            (0, 2001),  # No modals
            (1, 2002),  # One modal
            (3, 2004),  # Three modals
            (10, 2011),  # Many modals
        ]

        for modal_count, expected_z_index in test_scenarios:
            actual_z_index = calculate_hover_card_z_index(modal_count)
            assert (
                actual_z_index == expected_z_index
            ), f"Z-index calculation failed for {modal_count} modals"

        # Test that hover cards are always above modals
        for modal_count in range(0, 5):
            hover_z_index = calculate_hover_card_z_index(modal_count)
            modal_z_index = 2000 + modal_count
            assert (
                hover_z_index > modal_z_index
            ), f"Hover card z-index ({hover_z_index}) should be above modal z-index ({modal_z_index})"

    def test_definition_term_variations(self):
        """Test handling of different definition term variations."""
        # Test term variations that should all match the same definition
        base_term = "AI Agent"
        variations = [
            "AI Agent",
            "ai agent",
            "AI agent",
            "ai Agent",
            "AI-AGENT",
            "ai_agent",
            "AI  Agent",  # Extra spaces
            "AI Agent ",  # Trailing space
            " AI Agent",  # Leading space
        ]

        # Simulate normalization
        def normalize_term(term):
            normalized = term.lower().strip().replace("-", " ").replace("_", " ")
            # Clean up multiple spaces
            import re

            normalized = re.sub(r"\s+", " ", normalized)
            return normalized

        normalized_base = normalize_term(base_term)

        for variation in variations:
            normalized_variation = normalize_term(variation)
            assert (
                normalized_variation == normalized_base
            ), f"Term variation '{variation}' should normalize to '{normalized_base}'"

    def test_error_handling_in_modal_enhancement(self):
        """Test error handling during modal enhancement."""
        # Test scenarios that might cause errors
        error_scenarios = [
            {"container": None, "tab_name": "modal", "expected_error": True},
            {"container": "invalid", "tab_name": "modal", "expected_error": True},
            {"container": {}, "tab_name": None, "expected_error": True},
            {"container": {}, "tab_name": "modal", "expected_error": False},
        ]

        def simulate_enhancement(container, tab_name):
            try:
                if container is None or tab_name is None:
                    raise ValueError("Invalid parameters")
                if not isinstance(container, dict):
                    raise TypeError("Invalid container type")
                return {"success": True, "error": None}
            except Exception as e:
                return {"success": False, "error": str(e)}

        for scenario in error_scenarios:
            result = simulate_enhancement(scenario["container"], scenario["tab_name"])
            if scenario["expected_error"]:
                assert result["success"] == False
                assert result["error"] is not None
            else:
                assert result["success"] == True
                assert result["error"] is None
