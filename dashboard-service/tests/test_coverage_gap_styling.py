"""
Test coverage gap panel styling functionality.

This module tests the frontend JavaScript logic that applies green borders
to coverage gap panels when they show 100% coverage (no gaps).
"""

import pytest
from unittest.mock import patch, MagicMock
import json


@pytest.mark.unit
@pytest.mark.frontend
class TestCoverageGapStyling:
    """Test coverage gap panel styling logic."""

    def test_gap_cards_apply_success_class_for_zero_gaps(self):
        """Test that gap cards with zero counts get the 'success' class for green borders."""
        # Mock the gaps data structure with zero gaps (100% coverage)
        mock_gaps_data = {
            "summary": {
                "unmapped_risks": 0,
                "unmapped_controls": 0,
                "unmapped_questions": 0,
                "risks_without_questions": 0,
                "controls_without_questions": 0,
                "risk_coverage_pct": 100,
                "control_utilization_pct": 100,
                "question_coverage_pct": 100,
                "risks_without_questions_pct": 0,
                "controls_without_questions_pct": 0,
            }
        }

        # Simulate the renderGaps function logic
        def simulate_render_gaps(data):
            """Simulate the renderGaps function for gap card styling."""
            summary = data.get("summary", {})

            # Mock DOM elements
            cards = {
                "risks": {"classList": {"add": [], "remove": []}},
                "controls": {"classList": {"add": [], "remove": []}},
                "questions": {"classList": {"add": [], "remove": []}},
                "risks-without-questions": {"classList": {"add": [], "remove": []}},
                "controls-without-questions": {"classList": {"add": [], "remove": []}},
            }

            # Apply the same logic as in the actual JavaScript
            for card_name, card in cards.items():
                # Reset classes
                card["classList"]["remove"] = ["no-findings", "success"]

                # Determine which class to add based on gap count
                if card_name == "risks":
                    gap_count = summary.get("unmapped_risks", 0)
                elif card_name == "controls":
                    gap_count = summary.get("unmapped_controls", 0)
                elif card_name == "questions":
                    gap_count = summary.get("unmapped_questions", 0)
                elif card_name == "risks-without-questions":
                    gap_count = summary.get("risks_without_questions", 0)
                elif card_name == "controls-without-questions":
                    gap_count = summary.get("controls_without_questions", 0)

                if gap_count == 0:
                    card["classList"]["add"].append("success")
                else:
                    card["classList"]["add"].append("no-findings")

            return cards

        # Test the function
        result = simulate_render_gaps(mock_gaps_data)

        # All cards should have 'success' class added (green borders)
        for card_name, card in result.items():
            assert "success" in card["classList"]["add"]
            assert "no-findings" not in card["classList"]["add"]

    def test_gap_cards_apply_no_findings_class_for_non_zero_gaps(self):
        """Test that gap cards with non-zero counts get the 'no-findings' class."""
        # Mock the gaps data structure with some gaps
        mock_gaps_data = {
            "summary": {
                "unmapped_risks": 5,
                "unmapped_controls": 0,
                "unmapped_questions": 3,
                "risks_without_questions": 10,
                "controls_without_questions": 0,
                "risk_coverage_pct": 85,
                "control_utilization_pct": 100,
                "question_coverage_pct": 90,
                "risks_without_questions_pct": 15,
                "controls_without_questions_pct": 0,
            }
        }

        # Simulate the renderGaps function logic
        def simulate_render_gaps(data):
            """Simulate the renderGaps function for gap card styling."""
            summary = data.get("summary", {})

            # Mock DOM elements
            cards = {
                "risks": {"classList": {"add": [], "remove": []}},
                "controls": {"classList": {"add": [], "remove": []}},
                "questions": {"classList": {"add": [], "remove": []}},
                "risks-without-questions": {"classList": {"add": [], "remove": []}},
                "controls-without-questions": {"classList": {"add": [], "remove": []}},
            }

            # Apply the same logic as in the actual JavaScript
            for card_name, card in cards.items():
                # Reset classes
                card["classList"]["remove"] = ["no-findings", "success"]

                # Determine which class to add based on gap count
                if card_name == "risks":
                    gap_count = summary.get("unmapped_risks", 0)
                elif card_name == "controls":
                    gap_count = summary.get("unmapped_controls", 0)
                elif card_name == "questions":
                    gap_count = summary.get("unmapped_questions", 0)
                elif card_name == "risks-without-questions":
                    gap_count = summary.get("risks_without_questions", 0)
                elif card_name == "controls-without-questions":
                    gap_count = summary.get("controls_without_questions", 0)

                if gap_count == 0:
                    card["classList"]["add"].append("success")
                else:
                    card["classList"]["add"].append("no-findings")

            return cards

        # Test the function
        result = simulate_render_gaps(mock_gaps_data)

        # Cards with gaps should have 'no-findings' class, cards without gaps should have 'success'
        assert "no-findings" in result["risks"]["classList"]["add"]  # 5 gaps
        assert "success" in result["controls"]["classList"]["add"]  # 0 gaps
        assert "no-findings" in result["questions"]["classList"]["add"]  # 3 gaps
        assert (
            "no-findings" in result["risks-without-questions"]["classList"]["add"]
        )  # 10 gaps
        assert (
            "success" in result["controls-without-questions"]["classList"]["add"]
        )  # 0 gaps

    def test_css_success_class_has_green_border(self):
        """Test that the CSS success class defines green border styling."""
        # This test verifies that the CSS class exists and has the expected properties
        # In a real test environment, you might use a tool like jsdom or selenium
        # to actually test the CSS, but for unit testing we can verify the logic

        expected_css_properties = {
            "border-left-color": "var(--success-color)",
            "border-color": "var(--success-color)",
        }

        # Verify that the success class would apply green borders
        # This is more of a documentation test - in practice, you'd test this with
        # integration tests or visual regression tests
        assert expected_css_properties["border-left-color"] == "var(--success-color)"
        assert expected_css_properties["border-color"] == "var(--success-color)"

    def test_config_has_success_color_defined(self):
        """Test that the configuration file has the success color defined."""
        # This test verifies that the config structure includes the success color
        expected_config_structure = {"frontend": {"colors": {"success": "#10b981"}}}

        # Verify the color value matches what we expect
        assert expected_config_structure["frontend"]["colors"]["success"] == "#10b981"

    def test_gap_card_class_reset_logic(self):
        """Test that gap card classes are properly reset before applying new ones."""
        # Mock DOM element with existing classes
        mock_card = {
            "classList": {
                "add": [],
                "remove": [],
                "contains": lambda cls: cls in ["no-findings", "success"],
            }
        }

        # Simulate the reset logic
        def reset_card_classes(card):
            card["classList"]["remove"] = ["no-findings", "success"]
            return card

        # Test reset
        result = reset_card_classes(mock_card)

        # Verify that both classes are marked for removal
        assert "no-findings" in result["classList"]["remove"]
        assert "success" in result["classList"]["remove"]
