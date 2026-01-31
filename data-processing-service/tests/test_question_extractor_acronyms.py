import pandas as pd

"""
Test cases for question extractor with acronym functionality.

Tests that the question extractor correctly generates question IDs using
service acronyms instead of full service names.
"""

import pytest

from extractors.question_extractor import QuestionExtractor
from utils.service_acronyms import normalize_service_name_for_id


class TestQuestionExtractorAcronyms:
    """Test cases for question extractor with acronym functionality."""

    @pytest.fixture
    def question_extractor(self, config_manager):
        """Create a QuestionExtractor instance for testing."""
        return QuestionExtractor(config_manager)

    def test_question_id_generation_with_acronyms(self, question_extractor, temp_dir):
        """Test that question IDs are generated using acronyms."""
        excel_file = temp_dir / "test_questions_acronyms.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test with Cyber Risk Architecture (should become CRA)
            pd.DataFrame(
                {
                    "Question Number": ["6.1", "6.2"],
                    "Question Text": ["Question 6.1?", "Question 6.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

            # Test with Operational Assurance (should become OA)
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["Question 1.1?", "Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify results
        assert len(result_df) == 4

        # Check that question IDs use acronyms
        question_ids = result_df["question_id"].tolist()

        # Should have CRA acronym for Cyber Risk Architecture
        cra_ids = [qid for qid in question_ids if qid.startswith("Q.CRA.")]
        assert len(cra_ids) == 2, f"Expected 2 CRA question IDs, got {cra_ids}"

        # Should have OA acronym for Operational Assurance
        oa_ids = [qid for qid in question_ids if qid.startswith("Q.OA.")]
        assert len(oa_ids) == 2, f"Expected 2 OA question IDs, got {oa_ids}"

        # Verify specific IDs
        expected_ids = ["Q.CRA.6.1", "Q.CRA.6.2", "Q.OA.1.1", "Q.OA.1.2"]
        for expected_id in expected_ids:
            assert (
                expected_id in question_ids
            ), f"Expected question ID {expected_id} not found"

    def test_all_service_acronyms_used(self, question_extractor, temp_dir):
        """Test that all service acronyms are properly used."""
        excel_file = temp_dir / "test_all_acronyms.xlsx"

        # Create sheets for all services
        services = [
            "Operational Assurance",
            "Cyber Risk Architecture",
            "CREM Platform & Automation",
            "IAM Engineering",
            "Security Threat Testing",
            "Technical Security Solutions",
            "Risk Engineering",
            "CREM Incident Response",
            "Security Risk Management",
            "IAM Operations",
        ]

        with pd.ExcelWriter(excel_file) as writer:
            for i, service in enumerate(services):
                pd.DataFrame(
                    {
                        "Question Number": [f"{i + 1}.1"],
                        "Question Text": [f"Question for {service}?"],
                        "Category": ["Test"],
                        "Topic": ["Test"],
                    }
                ).to_excel(writer, sheet_name=service, index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify all services are processed
        assert len(result_df) == len(services)

        # Check that each service uses its correct acronym
        for service in services:
            expected_acronym = normalize_service_name_for_id(service)
            service_questions = result_df[result_df["managing_role"] == service]

            assert len(service_questions) == 1, f"Expected 1 question for {service}"

            question_id = service_questions.iloc[0]["question_id"]
            assert question_id.startswith(
                f"Q.{expected_acronym}."
            ), f"Question ID {question_id} should start with Q.{expected_acronym}."

    def test_acronym_consistency_across_sheets(self, question_extractor, temp_dir):
        """Test that acronyms are consistent across different sheets."""
        excel_file = temp_dir / "test_acronym_consistency.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Multiple sheets with same question numbers but different services
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["CRA Question 1.1?", "CRA Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["OA Question 1.1?", "OA Question 1.2?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Should have 4 questions total (no deduplication due to different acronyms)
        assert len(result_df) == 4

        # Verify all question IDs are unique
        question_ids = result_df["question_id"].tolist()
        assert len(question_ids) == len(
            set(question_ids)
        ), "All question IDs should be unique"

        # Verify acronyms are used correctly
        cra_ids = [qid for qid in question_ids if qid.startswith("Q.CRA.")]
        oa_ids = [qid for qid in question_ids if qid.startswith("Q.OA.")]

        assert len(cra_ids) == 2, f"Expected 2 CRA IDs, got {cra_ids}"
        assert len(oa_ids) == 2, f"Expected 2 OA IDs, got {oa_ids}"

    def test_special_characters_in_service_names(self, question_extractor, temp_dir):
        """Test handling of special characters in service names."""
        excel_file = temp_dir / "test_special_chars.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test service with ampersand
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["CPA Question?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="CREM Platform & Automation", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify acronym is used correctly
        assert len(result_df) == 1
        question_id = result_df.iloc[0]["question_id"]
        assert question_id == "Q.CPA.1.1", f"Expected Q.CPA.1.1, got {question_id}"

    def test_question_extraction_with_mixed_acronyms(
        self, question_extractor, temp_dir
    ):
        """Test extraction with mixed service names and acronyms."""
        excel_file = temp_dir / "test_mixed_acronyms.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Mix of different services
            services_data = [
                ("Cyber Risk Architecture", "CRA", "6.1"),
                ("Operational Assurance", "OA", "1.1"),
                ("CREM Platform & Automation", "CPA", "2.1"),
                ("IAM Engineering", "IAM", "3.1"),
                ("Security Threat Testing", "STT", "4.1"),
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
                    }
                ).to_excel(writer, sheet_name=service_name, index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify all questions extracted
        assert len(result_df) == len(services_data)

        # Verify each service uses correct acronym
        for service_name, expected_acronym, question_num in services_data:
            service_questions = result_df[result_df["managing_role"] == service_name]
            assert len(service_questions) == 1

            question_id = service_questions.iloc[0]["question_id"]
            expected_id = f"Q.{expected_acronym}.{question_num}"
            assert (
                question_id == expected_id
            ), f"Expected {expected_id}, got {question_id}"

    def test_acronym_generation_edge_cases(self, question_extractor, temp_dir):
        """Test edge cases in acronym generation."""
        excel_file = temp_dir / "test_acronym_edge_cases.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Test with service that might have edge cases
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "2.1", "10.1"],
                    "Question Text": [
                        "Question 1.1?",
                        "Question 2.1?",
                        "Question 10.1?",
                    ],
                    "Category": ["Test", "Test", "Test"],
                    "Topic": ["Test", "Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Technical Security Solutions", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify TSS acronym is used
        assert len(result_df) == 3

        question_ids = result_df["question_id"].tolist()
        tss_ids = [qid for qid in question_ids if qid.startswith("Q.TSS.")]
        assert len(tss_ids) == 3, f"Expected 3 TSS IDs, got {tss_ids}"

        # Verify specific IDs
        expected_ids = ["Q.TSS.1.1", "Q.TSS.2.1", "Q.TSS.10.1"]
        for expected_id in expected_ids:
            assert expected_id in question_ids, f"Expected {expected_id} not found"

    def test_backwards_compatibility_with_acronyms(self, question_extractor, temp_dir):
        """Test that the acronym system maintains backwards compatibility."""
        excel_file = temp_dir / "test_backwards_compatibility.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["Test question?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify basic functionality still works
        assert len(result_df) == 1

        question = result_df.iloc[0]
        assert question["question_id"].startswith("Q.")
        assert question["question_text"] == "Test question?"
        assert question["managing_role"] == "Operational Assurance"

        # Verify acronym is used
        assert question["question_id"] == "Q.OA.1.1"

    def test_question_id_format_validation(self, question_extractor, temp_dir):
        """Test that generated question IDs follow the correct format."""
        excel_file = temp_dir / "test_id_format.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
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
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify ID format: Q.{ACRONYM}.{NUMBER}
        for _, question in result_df.iterrows():
            question_id = question["question_id"]
            parts = question_id.split(".")

            # Question number "1.1" contains a dot, so split will have 4 parts: Q, CRA, 1, 1
            assert (
                len(parts) == 4
            ), f"Question ID {question_id} should have 4 parts (Q.CRA.1.1)"
            assert parts[0] == "Q", f"Question ID {question_id} should start with 'Q'"
            assert (
                parts[1] == "CRA"
            ), f"Question ID {question_id} should use CRA acronym"
            # Reconstruct the question number from parts 2 and 3
            question_number = f"{parts[2]}.{parts[3]}"
            assert question_number in [
                "1.1",
                "2.3",
                "10.5",
            ], f"Question ID {question_id} should have correct number"
