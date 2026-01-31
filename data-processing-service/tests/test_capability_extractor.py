"""
Tests for CapabilityExtractor

Tests the extraction of capability data from AI_ML_Security_Capabilities.xlsx
including both technical and non-technical capabilities.
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import os
from unittest.mock import Mock

from extractors.capability_extractor import CapabilityExtractor


class TestCapabilityExtractor:
    """Test cases for CapabilityExtractor class."""

    @pytest.fixture
    def config_manager(self):
        """Create a mock config manager."""
        config_manager = Mock()
        return config_manager

    @pytest.fixture
    def extractor(self, config_manager):
        """Create a CapabilityExtractor instance."""
        return CapabilityExtractor(config_manager)

    @pytest.fixture
    def sample_technical_data(self):
        """Sample technical capabilities data."""
        return pd.DataFrame(
            {
                "Technical Capability": [
                    "Data provenance attestation",
                    "Dataset lineage graphing",
                    "Poisoning anomaly screening",
                ],
                "Capability Domain": [
                    "Data Provenance & Assurance",
                    "Data Provenance & Assurance",
                    "Data Provenance & Assurance",
                ],
                "Capability Definition": [
                    "Cryptographically sign and hash dataset manifests",
                    "Maintain a machine‑readable chain of custody",
                    "Detect anomalous or outlier records",
                ],
                "Controls": [
                    "AIIM.3, AIIM.4, AIIM.8, AICICD.4",
                    "AIIM.3, AIIM.4, AISDL.6, AICTDM.5",
                    "AISDL.3, AISDL.11, AIMDV.7",
                ],
                "Candidate Products (modern, AI-defense)": [
                    "Cranium Detect AI; Protect AI Guardian",
                    "Aim Security; CalypsoAI",
                    "Adversa AI; Mindgard",
                ],
                "Notes": [
                    "Authenticity and provenance verification",
                    "General coverage across runtime",
                    "Backdoor/poison detection",
                ],
            }
        )

    @pytest.fixture
    def sample_non_technical_data(self):
        """Sample non-technical capabilities data."""
        return pd.DataFrame(
            {
                "Capability": [
                    "AI Governance Board and Accountability",
                    "AI Usage Policies and Enforcement",
                    "Regulatory and Legal Compliance Oversight",
                ],
                "Capability Definition": [
                    "Establish a cross-functional AI governance committee",
                    "Develop and enforce clear internal policies",
                    "Implement dedicated review processes",
                ],
            }
        )

    def test_extract_technical_capabilities(self, extractor, sample_technical_data):
        """Test extraction of technical capabilities."""
        capabilities = extractor._extract_technical_capabilities(sample_technical_data)

        assert len(capabilities) == 3

        # Check first capability
        first_cap = capabilities[0]
        assert first_cap["capability_id"] == "CAP.TECH.001"
        assert first_cap["capability_name"] == "Data provenance attestation"
        assert first_cap["capability_type"] == "technical"
        assert first_cap["capability_domain"] == "Data Provenance & Assurance"
        assert "Cryptographically sign" in first_cap["capability_definition"]
        assert "AIIM.3, AIIM.4, AIIM.8, AICICD.4" in first_cap["controls"]
        assert "Cranium Detect AI" in first_cap["candidate_products"]

    def test_extract_non_technical_capabilities(
        self, extractor, sample_non_technical_data
    ):
        """Test extraction of non-technical capabilities."""
        capabilities = extractor._extract_non_technical_capabilities(
            sample_non_technical_data
        )

        assert len(capabilities) == 3

        # Check first capability
        first_cap = capabilities[0]
        assert first_cap["capability_id"] == "CAP.NONTECH.001"
        assert first_cap["capability_name"] == "AI Governance Board and Accountability"
        assert first_cap["capability_type"] == "non-technical"
        assert first_cap["capability_domain"] == ""  # Non-technical don't have domains
        assert "cross-functional AI governance" in first_cap["capability_definition"]
        assert first_cap["controls"] == ""  # Non-technical often lack direct controls

    def test_clean_value(self, extractor):
        """Test value cleaning functionality."""
        assert extractor._clean_value("  Test Value  ") == "Test Value"
        assert (
            extractor._clean_value("Test   Multiple   Spaces") == "Test Multiple Spaces"
        )
        assert extractor._clean_value(None) == ""
        assert extractor._clean_value(pd.NA) == ""
        assert extractor._clean_value("") == ""

    def test_find_column(self, extractor):
        """Test column finding functionality."""
        df = pd.DataFrame(
            {"Technical Capability": [1, 2, 3], "Some Other Column": [4, 5, 6]}
        )

        # Should find exact match
        assert (
            extractor._find_column(df, ["Technical Capability"])
            == "Technical Capability"
        )

        # Should find first match from list
        assert (
            extractor._find_column(df, ["Technical Capability", "Capability"])
            == "Technical Capability"
        )

        # Should return empty string if no match
        assert extractor._find_column(df, ["Non-existent Column"]) == ""

    def test_normalize_control_id(self, extractor):
        """Test control ID normalization."""
        # Test adding C. prefix
        assert extractor._normalize_control_id("AIIM.3") == "C.AIIM.3"
        assert extractor._normalize_control_id("AICICD.4") == "C.AICICD.4"

        # Test already prefixed
        assert extractor._normalize_control_id("C.AIIM.3") == "C.AIIM.3"

        # Test empty/invalid
        assert extractor._normalize_control_id("") == ""
        assert extractor._normalize_control_id("   ") == ""

        # Test non-matching format
        assert extractor._normalize_control_id("SOME_TEXT") == "SOME_TEXT"

    def test_extract_capability_control_mappings(self, extractor):
        """Test extraction of capability-control mappings."""
        capabilities_df = pd.DataFrame(
            {
                "capability_id": ["CAP.TECH.001", "CAP.TECH.002", "CAP.NONTECH.001"],
                "controls": [
                    "AIIM.3, AIIM.4, AIIM.8",
                    "AISDL.6, AICTDM.5",
                    "",  # Non-technical capability with no controls
                ],
            }
        )

        mappings = extractor.extract_capability_control_mappings(capabilities_df)

        assert len(mappings) == 5  # 3 + 2 controls, non-technical has no controls

        # Check first mapping
        first_mapping = mappings.iloc[0]
        assert first_mapping["capability_id"] == "CAP.TECH.001"
        assert first_mapping["control_id"] == "C.AIIM.3"

        # Check that non-technical capability produces no mappings
        non_tech_mappings = mappings[mappings["capability_id"] == "CAP.NONTECH.001"]
        assert len(non_tech_mappings) == 0

    def test_validate_data_success(self, extractor):
        """Test successful data validation."""
        valid_df = pd.DataFrame(
            {
                "capability_id": ["CAP.TECH.001", "CAP.NONTECH.001"],
                "capability_name": ["Test Capability 1", "Test Capability 2"],
                "capability_type": ["technical", "non-technical"],
                "capability_domain": ["Test Domain", ""],
                "capability_definition": ["Test Definition 1", "Test Definition 2"],
                "controls": ["C.AIIM.3", ""],
                "candidate_products": ["Product 1", ""],
                "notes": ["Note 1", ""],
            }
        )

        # Should not raise any exception
        assert extractor.validate_data(valid_df) is True

    def test_validate_data_empty(self, extractor):
        """Test validation with empty DataFrame."""
        empty_df = pd.DataFrame()

        with pytest.raises(ValueError, match="No capability data found"):
            extractor.validate_data(empty_df)

    def test_validate_data_missing_columns(self, extractor):
        """Test validation with missing required columns."""
        invalid_df = pd.DataFrame(
            {
                "capability_id": ["CAP.TECH.001"],
                "capability_name": ["Test Capability"],
                # Missing capability_type
            }
        )

        with pytest.raises(ValueError, match="Missing required columns"):
            extractor.validate_data(invalid_df)

    def test_validate_data_empty_required_fields(self, extractor):
        """Test validation with empty required fields."""
        invalid_df = pd.DataFrame(
            {
                "capability_id": ["", "CAP.TECH.002"],
                "capability_name": ["Test Capability 1", ""],
                "capability_type": ["technical", "technical"],
            }
        )

        with pytest.raises(ValueError, match="Found .* rows with empty capability_id"):
            extractor.validate_data(invalid_df)

    def test_validate_data_duplicate_ids(self, extractor):
        """Test validation with duplicate capability IDs."""
        invalid_df = pd.DataFrame(
            {
                "capability_id": ["CAP.TECH.001", "CAP.TECH.001"],
                "capability_name": ["Test Capability 1", "Test Capability 2"],
                "capability_type": ["technical", "technical"],
            }
        )

        with pytest.raises(
            ValueError, match="Found .* rows with duplicate capability_id"
        ):
            extractor.validate_data(invalid_df)

    def test_validate_data_invalid_types(self, extractor):
        """Test validation with invalid capability types."""
        invalid_df = pd.DataFrame(
            {
                "capability_id": ["CAP.TECH.001"],
                "capability_name": ["Test Capability"],
                "capability_type": ["invalid-type"],
            }
        )

        with pytest.raises(
            ValueError, match="Found .* rows with invalid capability_type"
        ):
            extractor.validate_data(invalid_df)

    def test_extract_with_real_excel_file(self, extractor):
        """Test extraction with the actual Excel file if available."""
        excel_path = Path("../../source_docs/AI_ML_Security_Capabilities.xlsx")

        if excel_path.exists():
            result_df = extractor.extract(excel_path)

            # Should have both technical and non-technical capabilities
            assert len(result_df) > 0

            # Check that we have both types
            technical_count = len(
                result_df[result_df["capability_type"] == "technical"]
            )
            non_technical_count = len(
                result_df[result_df["capability_type"] == "non-technical"]
            )

            assert technical_count > 0
            assert non_technical_count > 0

            # Validate the data
            assert extractor.validate_data(result_df) is True

            # Test capability-control mappings
            mappings = extractor.extract_capability_control_mappings(result_df)
            assert len(mappings) > 0

            # Technical capabilities should have control mappings
            technical_caps = result_df[result_df["capability_type"] == "technical"]
            tech_mappings = mappings[
                mappings["capability_id"].isin(technical_caps["capability_id"])
            ]
            assert len(tech_mappings) > 0
        else:
            pytest.skip(
                "AI_ML_Security_Capabilities.xlsx not found, skipping real file test"
            )
