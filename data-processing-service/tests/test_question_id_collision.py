import pandas as pd

"""
Test for question ID collision across sheets.

This test would have caught the bug where question IDs were duplicated across
different managing roles, causing only the first occurrence to be kept.
"""

import pytest

from extractors.question_extractor import QuestionExtractor


class TestQuestionIdCollision:
    """Test cases for question ID collision prevention."""

    @pytest.fixture
    def question_extractor(self, config_manager):
        """Create a QuestionExtractor instance for testing."""
        return QuestionExtractor(config_manager)

    def test_question_id_collision_across_sheets(self, question_extractor, temp_dir):
        """Test that question IDs are unique across different sheets."""
        # Create Excel file with multiple sheets that have overlapping question numbers
        excel_file = temp_dir / "test_questions_collision.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Sheet 1: Operational Assurance
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2", "2.1"],
                    "Question Text": [
                        "Question 1.1?",
                        "Question 1.2?",
                        "Question 2.1?",
                    ],
                    "Category": ["Category 1", "Category 1", "Category 2"],
                    "Topic": ["Topic 1", "Topic 1", "Topic 2"],
                }
            ).to_excel(writer, sheet_name="Operational Assurance", index=False)

            # Sheet 2: IAM Engineering (same question numbers)
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2", "2.1"],
                    "Question Text": [
                        "Different Question 1.1?",
                        "Different Question 1.2?",
                        "Different Question 2.1?",
                    ],
                    "Category": ["Category 3", "Category 3", "Category 4"],
                    "Topic": ["Topic 3", "Topic 3", "Topic 4"],
                }
            ).to_excel(writer, sheet_name="IAM Engineering", index=False)

            # Sheet 3: Security Threat Testing (same question numbers)
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.2"],
                    "Question Text": ["Another Question 1.1?", "Another Question 1.2?"],
                    "Category": ["Category 5", "Category 5"],
                    "Topic": ["Topic 5", "Topic 5"],
                }
            ).to_excel(writer, sheet_name="Security Threat Testing", index=False)

        # Extract data
        result_df = question_extractor.extract(excel_file)

        # Verify all questions were extracted (no deduplication due to unique IDs)
        assert len(result_df) == 8  # 3 + 3 + 2 = 8, all questions should be extracted

        # Verify question IDs are unique
        question_ids = result_df["question_id"].tolist()
        assert len(question_ids) == len(
            set(question_ids)
        ), "Question IDs should be unique"

        # Verify question IDs include sheet name to prevent collision
        expected_ids = [
            "Q.Operational_Assurance.1.1",
            "Q.Operational_Assurance.1.2",
            "Q.Operational_Assurance.2.1",
            "Q.IAM_Engineering.1.1",
            "Q.IAM_Engineering.1.2",
            "Q.IAM_Engineering.2.1",
            "Q.Security_Threat_Testing.1.1",
            "Q.Security_Threat_Testing.1.2",
        ]

        # Check that we have unique IDs for each sheet
        for expected_id in expected_ids:
            if expected_id in question_ids:
                # Verify the question text matches the expected sheet
                question_row = result_df[result_df["question_id"] == expected_id].iloc[
                    0
                ]
                if "Operational_Assurance" in expected_id:
                    assert "Question" in question_row["question_text"]
                elif "IAM_Engineering" in expected_id:
                    assert "Different Question" in question_row["question_text"]
                elif "Security_Threat_Testing" in expected_id:
                    assert "Another Question" in question_row["question_text"]

    def test_question_id_format_with_special_characters(
        self, question_extractor, temp_dir
    ):
        """Test question ID format with special characters in sheet names."""
        excel_file = temp_dir / "test_questions_special_chars.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Sheet with special characters
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["Test question?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="CREM Platform & Automation", index=False)

        result_df = question_extractor.extract(excel_file)

        # Verify special characters are handled properly
        assert len(result_df) == 1
        question_id = result_df.iloc[0]["question_id"]
        assert question_id == "Q.CPA.1.1"
        assert "&" not in question_id  # Ampersand should be replaced
        assert " " not in question_id  # Spaces should be replaced

    def test_all_sheets_processed(self, question_extractor, temp_dir):
        """Test that all sheets in the Excel file are processed."""
        excel_file = temp_dir / "test_all_sheets.xlsx"

        # Create file with multiple sheets
        sheet_names = ["Sheet1", "Sheet2", "Sheet3", "Sheet4", "Sheet5"]

        with pd.ExcelWriter(excel_file) as writer:
            for i, sheet_name in enumerate(sheet_names):
                pd.DataFrame(
                    {
                        "Question Number": [f"{i + 1}.1", f"{i + 1}.2"],
                        "Question Text": [
                            f"Question {i + 1}.1?",
                            f"Question {i + 1}.2?",
                        ],
                        "Category": [f"Category {i + 1}", f"Category {i + 1}"],
                        "Topic": [f"Topic {i + 1}", f"Topic {i + 1}"],
                    }
                ).to_excel(writer, sheet_name=sheet_name, index=False)

        result_df = question_extractor.extract(excel_file)

        # Verify all sheets were processed
        assert len(result_df) == 10  # 5 sheets * 2 questions each

        # Verify all sheet names are represented
        managing_roles = set(result_df["managing_role"].unique())
        expected_roles = set(sheet_names)
        assert (
            managing_roles == expected_roles
        ), f"Expected {expected_roles}, got {managing_roles}"

        # Verify each sheet contributed questions
        for sheet_name in sheet_names:
            sheet_questions = result_df[result_df["managing_role"] == sheet_name]
            assert (
                len(sheet_questions) == 2
            ), f"Sheet {sheet_name} should have 2 questions"

    def test_question_extraction_with_empty_sheets(self, question_extractor, temp_dir):
        """Test extraction with some empty sheets."""
        excel_file = temp_dir / "test_empty_sheets.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Sheet with data
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": ["Valid question?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="Valid Sheet", index=False)

            # Empty sheet
            pd.DataFrame().to_excel(writer, sheet_name="Empty Sheet", index=False)

            # Sheet with no columns
            pd.DataFrame({}).to_excel(
                writer, sheet_name="No Columns Sheet", index=False
            )

        result_df = question_extractor.extract(excel_file)

        # Should only have questions from the valid sheet
        assert len(result_df) == 1
        assert result_df.iloc[0]["managing_role"] == "Valid Sheet"
        assert result_df.iloc[0]["question_id"] == "Q.VALIDSHEET.1.1"

    def test_question_extraction_with_invalid_rows(self, question_extractor, temp_dir):
        """Test extraction with some invalid rows (missing ID or text)."""
        excel_file = temp_dir / "test_invalid_rows.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "", "2.1"],  # Empty ID in middle
                    "Question Text": [
                        "Valid question?",
                        "Valid text?",
                        "",
                    ],  # Empty text at end
                    "Category": ["Test", "Test", "Test"],
                    "Topic": ["Test", "Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Mixed Sheet", index=False)

        result_df = question_extractor.extract(excel_file)

        # Should only have the valid row
        assert len(result_df) == 1
        assert result_df.iloc[0]["question_id"] == "Q.MIXEDSHEET.1.1"
        assert result_df.iloc[0]["question_text"] == "Valid question?"
