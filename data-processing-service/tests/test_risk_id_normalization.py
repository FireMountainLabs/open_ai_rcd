import pandas as pd

"""
Test for risk ID normalization in mappings.

This test would have caught the bug where risk IDs in controls data
(AIR.1, AIR.2) didn't match the format in risks data (AIR.001, AIR.002).
"""

import pytest

from extractors.mapping_extractor import MappingExtractor


class TestRiskIdNormalization:
    """Test cases for risk ID normalization in mappings."""

    @pytest.fixture
    def mapping_extractor(self, config_manager):
        """Create a MappingExtractor instance for testing."""
        return MappingExtractor(config_manager)

    def test_risk_id_normalization_short_to_padded(self, mapping_extractor):
        """Test normalization of short risk IDs to padded format."""
        # Test various short formats
        test_cases = [
            ("AIR.1", "AIR.001"),
            ("AIR.2", "AIR.002"),
            ("AIR.10", "AIR.010"),
            ("AIR.100", "AIR.100"),
            ("AIR.999", "AIR.999"),
        ]

        for input_id, expected_output in test_cases:
            result = mapping_extractor._normalize_risk_id_for_mapping(input_id)
            assert (
                result == expected_output
            ), f"Expected {expected_output}, got {result} for input {input_id}"

    def test_risk_id_normalization_already_padded(self, mapping_extractor):
        """Test that already padded risk IDs are unchanged."""
        # Test various padded formats
        test_cases = [
            "AIR.001",
            "AIR.002",
            "AIR.010",
            "AIR.100",
            "AIR.999",
        ]

        for input_id in test_cases:
            result = mapping_extractor._normalize_risk_id_for_mapping(input_id)
            assert (
                result == input_id
            ), f"Padded ID {input_id} should remain unchanged, got {result}"

    def test_risk_id_normalization_edge_cases(self, mapping_extractor):
        """Test edge cases for risk ID normalization."""
        # Test empty string
        assert mapping_extractor._normalize_risk_id_for_mapping("") == ""

        # Test None
        assert mapping_extractor._normalize_risk_id_for_mapping(None) == ""

        # Test invalid format (no dot)
        assert mapping_extractor._normalize_risk_id_for_mapping("AIR1") == "AIR1"

        # Test invalid number format
        assert mapping_extractor._normalize_risk_id_for_mapping("AIR.abc") == "AIR.abc"

        # Test zero
        assert mapping_extractor._normalize_risk_id_for_mapping("AIR.0") == "AIR.000"

    def test_risk_control_mapping_with_normalization(self, mapping_extractor, temp_dir):
        """Test risk-control mapping creation with ID normalization."""
        # Create sample risks data with padded IDs
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_description": ["Description 1", "Description 2", "Description 3"],
            }
        )

        # Create sample controls data with short risk IDs
        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1", "C.AISDL.3"],
                "control_title": ["Control 1", "Control 3"],
                "mapped_risks": ["AIR.1, AIR.2", "AIR.1, AIR.2, AIR.3"],
            }
        )

        # Create mappings
        result_df = mapping_extractor.create_risk_control_mappings(
            risks_df, controls_df
        )

        # Verify mappings were created
        assert len(result_df) == 5  # 2 + 3 = 5 total mappings

        # Verify all risk IDs are in padded format
        risk_ids = result_df["risk_id"].unique()
        for risk_id in risk_ids:
            assert risk_id.startswith(
                "R.AIR.00"
            ), f"Risk ID {risk_id} should be in padded format"

        # Verify specific mappings exist
        expected_mappings = [
            ("R.AIR.001", "C.AIIM.1"),
            ("R.AIR.002", "C.AIIM.1"),
            ("R.AIR.001", "C.AISDL.3"),
            ("R.AIR.002", "C.AISDL.3"),
            ("R.AIR.003", "C.AISDL.3"),
        ]

        for risk_id, control_id in expected_mappings:
            mapping_exists = (
                (result_df["risk_id"] == risk_id)
                & (result_df["control_id"] == control_id)
            ).any()
            assert mapping_exists, f"Mapping {risk_id} -> {control_id} should exist"

    def test_risk_control_mapping_without_normalization(
        self, mapping_extractor, temp_dir
    ):
        """Test risk-control mapping creation without normalization (should fail)."""
        # Create sample risks data with padded IDs
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_description": ["Description 1", "Description 2", "Description 3"],
            }
        )

        # Create sample controls data with short risk IDs
        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1"],
                "control_title": ["Control 1"],
                "mapped_risks": ["AIR.1, AIR.2"],  # Short format
            }
        )

        # Temporarily disable normalization to test the old behavior
        original_method = mapping_extractor._normalize_risk_id_for_mapping

        def no_normalization(risk_id):
            return risk_id

        mapping_extractor._normalize_risk_id_for_mapping = no_normalization

        try:
            # Create mappings without normalization
            result_df = mapping_extractor.create_risk_control_mappings(
                risks_df, controls_df
            )

            # Should have no mappings because AIR.1, AIR.2 don't match AIR.001, AIR.002
            assert (
                len(result_df) == 0
            ), "Without normalization, no mappings should be created"

        finally:
            # Restore original method
            mapping_extractor._normalize_risk_id_for_mapping = original_method

    def test_risk_control_mapping_mixed_formats(self, mapping_extractor, temp_dir):
        """Test risk-control mapping with mixed ID formats."""
        # Create sample risks data with padded IDs
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003", "R.AIR.010"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3", "Risk 10"],
                "risk_description": [
                    "Description 1",
                    "Description 2",
                    "Description 3",
                    "Description 10",
                ],
            }
        )

        # Create sample controls data with mixed formats
        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1", "C.AISDL.3"],
                "control_title": ["Control 1", "Control 3"],
                "mapped_risks": ["AIR.1, AIR.002", "AIR.3, AIR.10"],  # Mixed formats
            }
        )

        # Create mappings
        result_df = mapping_extractor.create_risk_control_mappings(
            risks_df, controls_df
        )

        # Verify mappings were created
        assert len(result_df) == 4  # 2 + 2 = 4 total mappings

        # Verify all risk IDs are in padded format
        risk_ids = result_df["risk_id"].unique()
        expected_risk_ids = {"R.AIR.001", "R.AIR.002", "R.AIR.003", "R.AIR.010"}
        assert set(risk_ids) == expected_risk_ids

    def test_risk_control_mapping_nonexistent_risks(self, mapping_extractor, temp_dir):
        """Test risk-control mapping with non-existent risk IDs."""
        # Create sample risks data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002"],
                "risk_title": ["Risk 1", "Risk 2"],
                "risk_description": ["Description 1", "Description 2"],
            }
        )

        # Create sample controls data with some non-existent risks
        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIIM.1"],
                "control_title": ["Control 1"],
                "mapped_risks": ["AIR.1, AIR.2, AIR.999"],  # AIR.999 doesn't exist
            }
        )

        # Create mappings
        result_df = mapping_extractor.create_risk_control_mappings(
            risks_df, controls_df
        )

        # Should only have mappings for existing risks
        assert len(result_df) == 2  # Only AIR.1 and AIR.2

        # Verify only existing risks are mapped
        risk_ids = set(result_df["risk_id"].unique())
        expected_risk_ids = {"R.AIR.001", "R.AIR.002"}
        assert risk_ids == expected_risk_ids
