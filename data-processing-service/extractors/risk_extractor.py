import pandas as pd

"""
Risk Data Extractor

Extracts risk data from AI Risk Taxonomy Excel files with validation and cleaning.
Handles data normalization and ensures data integrity.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RiskExtractor:
    """
    Extracts risk data from AI Risk Taxonomy Excel files.

    Provides specialized extraction logic for risk data with validation,
    cleaning, and normalization capabilities.
    """

    def __init__(self, config_manager):
        """
        Initialize the risk extractor.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    def extract(self, excel_path: Path) -> pd.DataFrame:
        """
        Extract risks from the AI Risk Taxonomy Excel file.

        Args:
            excel_path: Path to the Excel file containing risks

        Returns:
            DataFrame containing extracted risk data

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file format is invalid
        """
        if not excel_path.exists():
            raise FileNotFoundError(f"Risk Excel file not found: {excel_path}")

        logger.info(f"Extracting risks from {excel_path}")

        try:
            # Read the Excel file
            df = pd.read_excel(excel_path)

            # Handle empty files gracefully
            if df.empty or len(df.columns) == 0:
                logger.warning(f"Risk file {excel_path} is empty or has no columns")
                return pd.DataFrame()

            df.columns = df.columns.str.strip()

            # Get column mappings from config
            col_map = self.config_manager.get_data_source_config("risks")["columns"]

            # Validate required columns exist
            required_columns = [col_map["id"], col_map["title"]]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in risk file: {missing_columns}")

            # Extract risks data
            risks_data = []
            for _, row in df.iterrows():
                raw_risk_id = self._clean_value(row.get(col_map["id"], ""))
                risk_title = self._clean_value(row.get(col_map["title"], ""))
                risk_description = self._clean_value(row.get(col_map["description"], ""))

                # Only include rows with valid ID and title
                if raw_risk_id and risk_title:
                    # Prepend R. to make risk IDs easily identifiable
                    risk_id = f"R.{raw_risk_id}"
                    risks_data.append(
                        {
                            "risk_id": risk_id,
                            "risk_title": risk_title,
                            "risk_description": risk_description,
                        }
                    )
                else:
                    logger.warning(f"Skipping row with missing ID or title: {row.to_dict()}")

            result_df = pd.DataFrame(risks_data)

            # Remove duplicates based on risk_id
            initial_count = len(result_df)
            result_df = result_df.drop_duplicates(subset=["risk_id"], keep="first")
            final_count = len(result_df)

            if initial_count != final_count:
                logger.info(f"Removed {initial_count - final_count} duplicate risks")

            logger.info(f"Extracted {len(result_df)} unique risks")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting risks from {excel_path}: {e}")
            raise

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
        Validate extracted risk data.

        Args:
            df: DataFrame containing risk data

        Returns:
            True if data is valid

        Raises:
            ValueError: If data validation fails
        """
        if df.empty:
            raise ValueError("No risk data found")

        # Check required columns
        required_columns = ["risk_id", "risk_title"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check for empty required fields
        empty_ids = df[df["risk_id"].str.strip() == ""]
        if not empty_ids.empty:
            raise ValueError(f"Found {len(empty_ids)} rows with empty risk_id")

        empty_titles = df[df["risk_title"].str.strip() == ""]
        if not empty_titles.empty:
            raise ValueError(f"Found {len(empty_titles)} rows with empty risk_title")

        # Check for duplicate IDs
        duplicate_ids = df[df.duplicated(subset=["risk_id"], keep=False)]
        if not duplicate_ids.empty:
            raise ValueError(f"Found {len(duplicate_ids)} rows with duplicate risk_id")

        logger.info("Risk data validation passed")
        return True
