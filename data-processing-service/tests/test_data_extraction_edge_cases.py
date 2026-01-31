import pandas as pd

"""
Test cases for data extraction edge cases that could lead to undefined values.

Tests that identify gaps in our test coverage around data extraction,
validation, and edge cases that could cause undefined values in the frontend.
"""

from pathlib import Path

import pytest

from config.config_manager import ConfigManager
from extractors.question_extractor import QuestionExtractor


class TestDataExtractionEdgeCases:
    """Test cases for data extraction edge cases."""

    @pytest.fixture
    def config_manager(self):
        """Create a ConfigManager instance for testing."""
        config_path = Path(__file__).parent.parent / "config" / "default_config.yaml"
        return ConfigManager(config_path)

    def test_question_extraction_with_empty_cells(self, config_manager, temp_dir):
        """Test question extraction with empty cells that could cause undefined values."""
        excel_file = temp_dir / "test_empty_cells.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "", "2.1"],
                    "Question Text": ["Valid question?", "", "Another valid question?"],
                    "Category": ["Test", "", "Test"],
                    "Topic": ["Test", "", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should only extract valid questions
        assert len(result_df) == 2

        # Verify no undefined values
        for _, question in result_df.iterrows():
            assert question["question_text"] != "undefined"
            assert question["question_text"] is not None
            assert question["question_text"] != ""
            assert question["category"] != "undefined"
            assert question["category"] is not None
            assert question["category"] != ""

    def test_question_extraction_with_nan_values(self, config_manager, temp_dir):
        """Test question extraction with NaN values."""
        excel_file = temp_dir / "test_nan_values.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "2.1"],
                    "Question Text": ["Valid question?", None],
                    "Category": [None, "Test"],
                    "Topic": ["Test", None],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should only extract valid questions
        assert len(result_df) == 1

        # Verify no undefined values
        question = result_df.iloc[0]
        assert question["question_text"] != "undefined"
        assert question["question_text"] is not None
        assert question["question_text"] != ""
        assert question["category"] != "undefined"
        assert question["category"] is not None
        # Category can be empty string if it was NaN in the source data
        assert question["category"] == ""

    def test_question_extraction_with_whitespace_only(self, config_manager, temp_dir):
        """Test question extraction with whitespace-only values."""
        excel_file = temp_dir / "test_whitespace_only.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "2.1"],
                    "Question Text": ["Valid question?", "   \t\n   "],
                    "Category": ["   \t\n   ", "Test"],
                    "Topic": ["Test", "   \t\n   "],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should only extract valid questions
        assert len(result_df) == 1

        # Verify no undefined values
        question = result_df.iloc[0]
        assert question["question_text"] != "undefined"
        assert question["question_text"] is not None
        assert question["question_text"] != ""
        assert question["question_text"].strip() != ""

    def test_question_extraction_with_special_characters(
        self, config_manager, temp_dir
    ):
        """Test question extraction with special characters."""
        excel_file = temp_dir / "test_special_chars.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": [
                        "Question with special chars: !@#$%^&*()_+-=[]{}|;':\",./<>?`~"
                    ],
                    "Category": ["Category with émojis 🚀🎉"],
                    "Topic": ["Topic with unicode: ñáéíóú"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract the question
        assert len(result_df) == 1

        # Verify special characters are preserved
        question = result_df.iloc[0]
        assert "!@#$%^&*()_+-=[]{}|;':\",./<>?`~" in question["question_text"]
        assert "🚀🎉" in question["category"]
        assert "ñáéíóú" in question["topic"]

    def test_question_extraction_with_very_long_text(self, config_manager, temp_dir):
        """Test question extraction with very long text."""
        excel_file = temp_dir / "test_long_text.xlsx"

        long_text = "A" * 10000  # Very long text

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": [long_text],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract the question
        assert len(result_df) == 1

        # Verify long text is preserved
        question = result_df.iloc[0]
        assert len(question["question_text"]) == 10000
        assert question["question_text"] == long_text

    def test_question_extraction_with_html_content(self, config_manager, temp_dir):
        """Test question extraction with HTML content."""
        excel_file = temp_dir / "test_html_content.xlsx"

        html_content = "<script>alert('xss')</script><b>Bold text</b>"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1"],
                    "Question Text": [html_content],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract the question
        assert len(result_df) == 1

        # Verify HTML content is preserved (sanitization should happen in frontend)
        question = result_df.iloc[0]
        assert "<script>" in question["question_text"]
        assert "<b>" in question["question_text"]

    def test_question_extraction_with_duplicate_ids(self, config_manager, temp_dir):
        """Test question extraction with duplicate question IDs."""
        excel_file = temp_dir / "test_duplicate_ids.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "1.1"],  # Duplicate IDs
                    "Question Text": ["First question?", "Second question?"],
                    "Category": ["Test", "Test"],
                    "Topic": ["Test", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should handle duplicates by deduplicating based on question_id
        # Duplicate question IDs in the same sheet are a data quality issue
        assert len(result_df) == 1

        # Verify both questions are valid
        for _, question in result_df.iterrows():
            assert question["question_text"] != "undefined"
            assert question["question_text"] is not None
            assert question["question_text"] != ""

    def test_question_extraction_with_missing_columns(self, config_manager, temp_dir):
        """Test question extraction with missing columns."""
        excel_file = temp_dir / "test_missing_columns.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Missing 'Category' and 'Topic' columns
            pd.DataFrame(
                {"Question Number": ["1.1"], "Question Text": ["Valid question?"]}
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract the question with default values
        assert len(result_df) == 1

        # Verify default values are used
        question = result_df.iloc[0]
        assert question["question_text"] == "Valid question?"
        assert question["category"] == ""  # Default empty string
        assert question["topic"] == ""  # Default empty string

    def test_question_extraction_with_wrong_column_names(
        self, config_manager, temp_dir
    ):
        """Test question extraction with wrong column names."""
        excel_file = temp_dir / "test_wrong_columns.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Wrong Column": ["1.1"],  # Wrong column name
                    "Question Text": ["Valid question?"],
                    "Category": ["Test"],
                    "Topic": ["Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should handle missing question number gracefully
        assert len(result_df) == 0  # No valid questions without question number

    def test_question_extraction_with_mixed_data_types(self, config_manager, temp_dir):
        """Test question extraction with mixed data types."""
        excel_file = temp_dir / "test_mixed_types.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", 2.1, True],  # Mixed types
                    "Question Text": ["Valid question?", 123, None],  # Mixed types
                    "Category": ["Test", 456, "Test"],
                    "Topic": ["Test", "Test", 789],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract valid questions (numeric types are converted to strings)
        assert len(result_df) == 2  # First two rows are valid after type conversion

        # Verify the valid questions
        question1 = result_df.iloc[0]
        assert question1["question_text"] == "Valid question?"
        assert question1["category"] == "Test"

        question2 = result_df.iloc[1]
        assert question2["question_text"] == "123"
        assert question2["category"] == "456"
        assert question2["topic"] == "Test"

    def test_question_extraction_with_empty_sheet(self, config_manager, temp_dir):
        """Test question extraction with empty sheet."""
        excel_file = temp_dir / "test_empty_sheet.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            # Empty DataFrame
            pd.DataFrame(
                {
                    "Question Number": [],
                    "Question Text": [],
                    "Category": [],
                    "Topic": [],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should return empty DataFrame
        assert len(result_df) == 0

    def test_question_extraction_with_corrupted_data(self, config_manager, temp_dir):
        """Test question extraction with corrupted data."""
        excel_file = temp_dir / "test_corrupted_data.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "corrupted", "2.1"],
                    "Question Text": [
                        "Valid question?",
                        "corrupted",
                        "Another valid question?",
                    ],
                    "Category": ["Test", "corrupted", "Test"],
                    "Topic": ["Test", "corrupted", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract all questions (including those with "corrupted" values)
        assert len(result_df) == 3

        # Verify all questions are processed (including the "corrupted" one)
        question_ids = result_df["question_id"].tolist()
        assert "Q.CRA.1.1" in question_ids
        assert "Q.CRA.corrupted" in question_ids
        assert "Q.CRA.2.1" in question_ids

    def test_data_validation_in_extraction_process(self, config_manager, temp_dir):
        """Test data validation during extraction process."""
        excel_file = temp_dir / "test_validation.xlsx"

        with pd.ExcelWriter(excel_file) as writer:
            pd.DataFrame(
                {
                    "Question Number": ["1.1", "2.1", "3.1"],
                    "Question Text": [
                        "Valid question?",
                        "undefined",
                        "Another valid question?",
                    ],
                    "Category": ["Test", "undefined", "Test"],
                    "Topic": ["Test", "undefined", "Test"],
                }
            ).to_excel(writer, sheet_name="Cyber Risk Architecture", index=False)

        question_extractor = QuestionExtractor(config_manager)
        result_df = question_extractor.extract(excel_file)

        # Should extract all questions (including those with 'undefined' strings)
        assert len(result_df) == 3

        # Verify that 'undefined' strings are preserved as-is
        # (validation should happen in frontend)
        undefined_question = result_df[result_df["question_text"] == "undefined"].iloc[
            0
        ]
        assert undefined_question["question_text"] == "undefined"
        assert undefined_question["category"] == "undefined"
        assert undefined_question["topic"] == "undefined"

    def test_extraction_error_handling(self, config_manager, temp_dir):
        """Test extraction error handling."""
        # Test with non-existent file
        non_existent_file = temp_dir / "non_existent.xlsx"

        question_extractor = QuestionExtractor(config_manager)

        # Should handle file not found gracefully
        with pytest.raises(FileNotFoundError):
            question_extractor.extract(non_existent_file)

    def test_extraction_with_invalid_excel_format(self, config_manager, temp_dir):
        """Test extraction with invalid Excel format."""
        # Create a text file with .xlsx extension
        invalid_file = temp_dir / "invalid.xlsx"
        invalid_file.write_text("This is not an Excel file")

        question_extractor = QuestionExtractor(config_manager)

        # Should handle invalid format gracefully
        with pytest.raises(Exception):  # Should raise some kind of exception
            question_extractor.extract(invalid_file)
