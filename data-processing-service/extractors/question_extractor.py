import pandas as pd

"""
Question Data Extractor

Extracts question data from AI Interview Questions Excel files across multiple sheets.
Handles complex multi-sheet extraction with validation and deduplication.
"""

import logging
from pathlib import Path
from typing import List

from utils.service_acronyms import normalize_service_name_for_id

logger = logging.getLogger(__name__)


class QuestionExtractor:
    """
    Extracts question data from AI Interview Questions Excel files.

    Handles multi-sheet Excel files and extracts question data with proper
    validation, cleaning, and deduplication capabilities.
    """

    def __init__(self, config_manager):
        """
        Initialize the question extractor.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    def extract(self, excel_path: Path) -> pd.DataFrame:
        """
        Extract questions from the AI Interview Questions Excel file (all sheets).

        Args:
            excel_path: Path to the Excel file containing questions

        Returns:
            DataFrame containing extracted question data

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file format is invalid
        """
        if not excel_path.exists():
            raise FileNotFoundError(f"Question Excel file not found: {excel_path}")

        logger.info(f"Extracting questions from {excel_path}")

        try:
            # Read all sheets from the Excel file
            xl = pd.ExcelFile(excel_path)
            all_questions = []

            # Get column mappings from config
            col_map = self.config_manager.get_data_source_config("questions")["columns"]

            for sheet_name in xl.sheet_names:
                try:
                    logger.info(f"Processing sheet: {sheet_name}")
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)

                    # Handle empty sheets gracefully
                    if df.empty or len(df.columns) == 0:
                        logger.warning(f"Sheet '{sheet_name}' is empty or has no columns, skipping")
                        continue

                    df.columns = df.columns.str.strip()

                    # Extract questions from this sheet
                    sheet_questions = self._extract_questions_from_sheet(df, col_map, sheet_name)
                    all_questions.extend(sheet_questions)

                    logger.info(f"Extracted {len(sheet_questions)} questions from sheet " f"'{sheet_name}'")

                except Exception as e:
                    logger.warning(f"Error reading sheet {sheet_name}: {e}")
                    continue

            # Create DataFrame and remove duplicates
            result_df = pd.DataFrame(all_questions)

            if not result_df.empty:
                # Remove duplicates based on question_id, keeping the first occurrence
                initial_count = len(result_df)
                result_df = result_df.drop_duplicates(subset=["question_id"], keep="first")
                final_count = len(result_df)

                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate questions")

            logger.info(f"Extracted {len(result_df)} unique questions")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting questions from {excel_path}: {e}")
            raise

    def _extract_questions_from_sheet(self, df: pd.DataFrame, col_map: dict, sheet_name: str) -> List[dict]:
        """
        Extract questions from a single sheet.

        Args:
            df: DataFrame containing sheet data
            col_map: Column mapping configuration
            sheet_name: Name of the sheet being processed

        Returns:
            List of question dictionaries
        """
        questions = []

        for _, row in df.iterrows():
            raw_question_id = self._clean_value(row.get(col_map["id"], ""))
            question_text = self._clean_value(row.get(col_map["text"], ""))
            category = self._clean_value(row.get(col_map["category"], ""))
            topic = self._clean_value(row.get(col_map["topic"], ""))

            # Only include rows with valid ID and text
            if raw_question_id and question_text:
                # Create unique question ID using service acronym
                # This prevents ID collisions across different managing roles
                service_acronym = normalize_service_name_for_id(sheet_name)
                question_id = f"Q.{service_acronym}.{raw_question_id}"
                questions.append(
                    {
                        "question_id": question_id,
                        "question_text": question_text,
                        "category": category,
                        "topic": topic,
                        "managing_role": sheet_name,
                    }
                )
            else:
                logger.warning(f"Skipping row with missing ID or text in sheet " f"'{sheet_name}': {row.to_dict()}")

        return questions

    def _clean_value(self, value) -> str:
        """
        Clean and normalize a data value.

        Args:
            value: Raw value from Excel

        Returns:
            Cleaned string value
        """
        if pd.isna(value) or value is None:
            return ""

        # Convert to string and strip whitespace
        cleaned = str(value).strip()

        # Replace multiple whitespace with single space
        import re

        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate extracted question data.

        Args:
            df: DataFrame containing question data

        Returns:
            True if data is valid

        Raises:
            ValueError: If data validation fails
        """
        if df.empty:
            raise ValueError("No question data found")

        # Check required columns
        required_columns = ["question_id", "question_text"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check for empty required fields
        empty_ids = df[df["question_id"].str.strip() == ""]
        if not empty_ids.empty:
            raise ValueError(f"Found {len(empty_ids)} rows with empty question_id")

        empty_texts = df[df["question_text"].str.strip() == ""]
        if not empty_texts.empty:
            raise ValueError(f"Found {len(empty_texts)} rows with empty question_text")

        # Check for duplicate IDs
        duplicate_ids = df[df.duplicated(subset=["question_id"], keep=False)]
        if not duplicate_ids.empty:
            raise ValueError(f"Found {len(duplicate_ids)} rows with duplicate question_id")

        logger.info("Question data validation passed")
        return True
