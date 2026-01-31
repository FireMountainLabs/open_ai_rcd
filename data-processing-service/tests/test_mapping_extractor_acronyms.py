import pandas as pd

"""
Test cases for mapping extractor with acronym functionality.

Tests that the mapping extractor correctly generates question IDs using
service acronyms to match the question extractor behavior.
"""

import pytest

from extractors.mapping_extractor import MappingExtractor


class TestMappingExtractorAcronyms:
    """Test cases for mapping extractor with acronym functionality."""

    @pytest.fixture
    def mapping_extractor(self, config_manager):
        """Create a MappingExtractor instance for testing."""
        return MappingExtractor(config_manager)

    def test_question_risk_mapping_with_acronyms(self, mapping_extractor, temp_dir):
        """Test that question-risk mappings use acronyms."""
        excel_file = temp_dir / "test_question_mappings_acronyms.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Cyber Risk Architecture sheet
            pd.DataFrame(
                {
                    "Question Number": ["6.1", "6.2"],
                    "Question Text": ["CRA Question 6.1?", "CRA Question 6.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

            # Operational Assurance sheet
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["OA Question 1.1?", "OA Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.003", "AIR.004"],
                    "AIML_CONTROL": ["AIGPC.3", "AIGPC.4"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

        # Create sample risks data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003", "R.AIR.004"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3", "Risk 4"],
                "risk_description": ["Desc 1", "Desc 2", "Desc 3", "Desc 4"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(excel_file, risks_df, None)
        )

        # Verify question-risk mappings use acronyms
        assert len(question_risk_mappings) == 4

        # Check that question IDs use acronyms
        question_ids = question_risk_mappings["question_id"].tolist()

        # Should have CRA acronym for Cyber Risk Architecture
        cra_ids = [qid for qid in question_ids if qid.startswith("Q.CRA.")]
        assert len(cra_ids) == 2, f"Expected 2 CRA question IDs, got {cra_ids}"

        # Should have OA acronym for Operational Assurance
        oa_ids = [qid for qid in question_ids if qid.startswith("Q.OA.")]
        assert len(oa_ids) == 2, f"Expected 2 OA question IDs, got {oa_ids}"

        # Verify specific mappings
        expected_mappings = [
            ("Q.CRA.6.1", "R.AIR.001"),
            ("Q.CRA.6.2", "R.AIR.002"),
            ("Q.OA.1.1", "R.AIR.003"),
            ("Q.OA.1.2", "R.AIR.004"),
        ]

        for question_id, risk_id in expected_mappings:
            mapping_exists = (
                (question_risk_mappings["question_id"] == question_id)
                & (question_risk_mappings["risk_id"] == risk_id)
            ).any()
            assert mapping_exists, f"Mapping {question_id} -> {risk_id} should exist"

    def test_question_control_mapping_with_acronyms(self, mapping_extractor, temp_dir):
        """Test that question-control mappings use acronyms."""
        excel_file = temp_dir / "test_question_control_mappings_acronyms.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["CPA Question 1.1?", "CPA Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="CREM Platform & Automation", index=False)

        # Create sample controls data
        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1", "C.AIGPC.2"],
                "control_title": ["Control 1", "Control 2"],
                "control_description": ["Desc 1", "Desc 2"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(excel_file, None, controls_df)
        )

        # Verify question-control mappings use acronyms
        assert len(question_control_mappings) == 2

        # Check that question IDs use CPA acronym
        question_ids = question_control_mappings["question_id"].tolist()
        cpa_ids = [qid for qid in question_ids if qid.startswith("Q.CPA.")]
        assert len(cpa_ids) == 2, f"Expected 2 CPA question IDs, got {cpa_ids}"

        # Verify specific mappings
        expected_mappings = [
            ("Q.CPA.1.1", "C.AIGPC.1"),
            ("Q.CPA.1.2", "C.AIGPC.2"),
        ]

        for question_id, control_id in expected_mappings:
            mapping_exists = (
                (question_control_mappings["question_id"] == question_id)
                & (question_control_mappings["control_id"] == control_id)
            ).any()
            assert mapping_exists, f"Mapping {question_id} -> {control_id} should exist"

    def test_mapping_consistency_with_question_extractor(
        self, mapping_extractor, temp_dir
    ):
        """Test that mappings use same acronym format as question extractor."""
        excel_file = temp_dir / "test_mapping_consistency.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test multiple services
            services_data = [
                ("Cyber Risk Architecture", "CRA", "6.1"),
                ("Operational Assurance", "OA", "1.1"),
                ("CREM Platform & Automation", "CPA", "2.1"),
                ("IAM Engineering", "IAM", "3.1"),
            ]

            for service_name, expected_acronym, question_num in services_data:
                pd.DataFrame(
                    {
                        "Question Number": [question_num],
                        "Question Text": [
                            f"{expected_acronym} Question {question_num}?"
                        ],
                        "Category": ["Test"],
                        "Topic": ["Test"],
                        "AIML_RISK_TAXONOMY": ["AIR.001"],
                        "AIML_CONTROL": ["AIGPC.1"],
                    }
                ).to_excel(writer, sheet_name=service_name, index=False)

        # Create sample data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"],
                "risk_title": ["Risk 1"],
                "risk_description": ["Desc 1"],
            }
        )

        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1"],
                "control_title": ["Control 1"],
                "control_description": ["Desc 1"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(
                excel_file, risks_df, controls_df
            )
        )

        # Verify all services use correct acronyms
        for service_name, expected_acronym, question_num in services_data:
            expected_question_id = f"Q.{expected_acronym}.{question_num}"

            # Check question-risk mappings
            risk_mapping_exists = (
                question_risk_mappings["question_id"] == expected_question_id
            ).any()
            assert (
                risk_mapping_exists
            ), f"Question-risk mapping for {expected_question_id} should exist"

            # Check question-control mappings
            control_mapping_exists = (
                question_control_mappings["question_id"] == expected_question_id
            ).any()
            assert (
                control_mapping_exists
            ), f"Question-control mapping for {expected_question_id} should exist"

    def test_mapping_extraction_with_special_characters(
        self, mapping_extractor, temp_dir
    ):
        """Test mapping extraction with special characters in service names."""
        excel_file = temp_dir / "test_mapping_special_chars.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test service with ampersand
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["CPA Question 1.1?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001"],
                    "AIML_CONTROL": ["AIGPC.1"],
                }
            ).to_excel(writer, sheet_name="CREM Platform & Automation", index=False)

        # Create sample data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001"],
                "risk_title": ["Risk 1"],
                "risk_description": ["Desc 1"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(excel_file, risks_df, None)
        )

        # Verify CPA acronym is used
        assert len(question_risk_mappings) == 1

        question_id = question_risk_mappings.iloc[0]["question_id"]
        assert question_id == "Q.CPA.1.1", f"Expected Q.CPA.1.1, got {question_id}"

    def test_mapping_extraction_with_multiple_sheets(self, mapping_extractor, temp_dir):
        """Test mapping extraction from multiple sheets with acronyms."""
        excel_file = temp_dir / "test_mapping_multiple_sheets.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Sheet 1: Cyber Risk Architecture
            pd.DataFrame(
                {
                    "Question Number": ["6.1"],
                    "Question Text": ["CRA Question 6.1?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001"],
                    "AIML_CONTROL": ["AIGPC.1"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

            # Sheet 2: Operational Assurance
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["OA Question 1.1?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.002"],
                    "AIML_CONTROL": ["AIGPC.2"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

        # Create sample data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002"],
                "risk_title": ["Risk 1", "Risk 2"],
                "risk_description": ["Desc 1", "Desc 2"],
            }
        )

        controls_df = pd.DataFrame(
            {
                "control_id": ["C.AIGPC.1", "C.AIGPC.2"],
                "control_title": ["Control 1", "Control 2"],
                "control_description": ["Desc 1", "Desc 2"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(
                excel_file, risks_df, controls_df
            )
        )

        # Verify both sheets are processed
        assert len(question_risk_mappings) == 2
        assert len(question_control_mappings) == 2

        # Verify acronyms are used correctly
        question_ids = question_risk_mappings["question_id"].tolist()
        assert "Q.CRA.6.1" in question_ids
        assert "Q.OA.1.1" in question_ids

        # Verify mappings are correct
        cra_mapping = question_risk_mappings[
            question_risk_mappings["question_id"] == "Q.CRA.6.1"
        ]
        assert cra_mapping.iloc[0]["risk_id"] == "R.AIR.001"

        oa_mapping = question_risk_mappings[
            question_risk_mappings["question_id"] == "Q.OA.1.1"
        ]
        assert oa_mapping.iloc[0]["risk_id"] == "R.AIR.002"

    def test_mapping_extraction_with_invalid_data(self, mapping_extractor, temp_dir):
        """Test mapping extraction with invalid data and acronyms."""
        excel_file = temp_dir / "test_mapping_invalid_data.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "", "2.1"],
                    "Question Text": ["Valid Question?", "Valid Text?", ""],
                    "Category": ["Test", "Test", "Test"],
                    "Topic": ["Test", "Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        # Create sample data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_description": ["Desc 1", "Desc 2", "Desc 3"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(excel_file, risks_df, None)
        )

        # Should have mappings for valid questions (1.1 and 2.1)
        # Note: Empty question number ("") is skipped, but "2.1" with valid text is processed
        assert len(question_risk_mappings) == 2

        question_ids = question_risk_mappings["question_id"].tolist()
        assert "Q.CRA.1.1" in question_ids, f"Expected Q.CRA.1.1 in {question_ids}"
        assert "Q.CRA.2.1" in question_ids, f"Expected Q.CRA.2.1 in {question_ids}"

    def test_mapping_extraction_edge_cases(self, mapping_extractor, temp_dir):
        """Test edge cases in mapping extraction with acronyms."""
        excel_file = temp_dir / "test_mapping_edge_cases.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test with various question number formats
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "2.3", "10.5"],
                    "Question Text": [
                        "Question 1.1?",
                        "Question 2.3?",
                        "Question 10.5?",
                    ],
                    "Category": ["Test", "Test", "Test"],
                    "Topic": ["Test", "Test", "Test"],
                    "AIML_RISK_TAXONOMY": ["AIR.001", "AIR.002", "AIR.003"],
                    "AIML_CONTROL": ["AIGPC.1", "AIGPC.2", "AIGPC.3"],
                }
            ).to_excel(writer, sheet_name="Technical Security Solutions", index=False)

        # Create sample data
        risks_df = pd.DataFrame(
            {
                "risk_id": ["R.AIR.001", "R.AIR.002", "R.AIR.003"],
                "risk_title": ["Risk 1", "Risk 2", "Risk 3"],
                "risk_description": ["Desc 1", "Desc 2", "Desc 3"],
            }
        )

        # Extract mappings
        question_risk_mappings, question_control_mappings = (
            mapping_extractor.extract_question_mappings(excel_file, risks_df, None)
        )

        # Verify TSS acronym is used for all questions
        assert len(question_risk_mappings) == 3

        question_ids = question_risk_mappings["question_id"].tolist()
        tss_ids = [qid for qid in question_ids if qid.startswith("Q.TSS.")]
        assert len(tss_ids) == 3, f"Expected 3 TSS IDs, got {tss_ids}"

        # Verify specific IDs
        expected_ids = ["Q.TSS.1.1", "Q.TSS.2.3", "Q.TSS.10.5"]
        for expected_id in expected_ids:
            assert expected_id in question_ids, f"Expected {expected_id} not found"
