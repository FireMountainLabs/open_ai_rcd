import pandas as pd

"""
Data utility functions for the AIML data collector.

This module provides utilities for data validation, cleaning,
and transformation operations.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataUtils:
    """
    Utility class for data operations and validation.

    This class provides methods for data cleaning, validation,
    and transformation operations.
    """

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean a DataFrame by removing empty rows and standardizing data.

        Args:
            df: DataFrame to clean

        Returns:
            Cleaned DataFrame
        """
        if df.empty:
            return df

        # Create a copy to avoid modifying original
        cleaned_df = df.copy()

        # Remove completely empty rows
        cleaned_df = cleaned_df.dropna(how="all")

        # Clean string columns
        string_columns = cleaned_df.select_dtypes(include=["object"]).columns
        for col in string_columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
            # Replace 'nan' strings with empty strings
            cleaned_df[col] = cleaned_df[col].replace("nan", "")

        return cleaned_df

    @staticmethod
    def validate_required_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        Validate that a DataFrame contains all required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names

        Returns:
            True if all required columns exist, False otherwise
        """
        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False

        return True

    @staticmethod
    def remove_duplicates(df: pd.DataFrame, subset: List[str] = None) -> pd.DataFrame:
        """
        Remove duplicate rows from a DataFrame.

        Args:
            df: DataFrame to deduplicate
            subset: List of columns to consider for duplicates

        Returns:
            DataFrame with duplicates removed
        """
        if df.empty:
            return df

        if subset is None:
            subset = df.columns.tolist()

        # Remove duplicates, keeping the first occurrence
        deduplicated_df = df.drop_duplicates(subset=subset, keep="first")

        removed_count = len(df) - len(deduplicated_df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate rows")

        return deduplicated_df

    @staticmethod
    def validate_data_types(df: pd.DataFrame, expected_types: Dict[str, str]) -> bool:
        """
        Validate that DataFrame columns have expected data types.

        Args:
            df: DataFrame to validate
            expected_types: Dictionary mapping column names to expected types

        Returns:
            True if all columns have expected types, False otherwise
        """
        validation_passed = True

        for column, expected_type in expected_types.items():
            if column not in df.columns:
                logger.warning(f"Column '{column}' not found for type validation")
                continue

            actual_type = str(df[column].dtype)

            if expected_type not in actual_type:
                logger.warning(f"Column '{column}' has type '{actual_type}', " f"expected '{expected_type}'")
                validation_passed = False

        return validation_passed

    @staticmethod
    def get_data_summary(df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Generate a summary of DataFrame data.

        Args:
            df: DataFrame to summarize
            entity_type: Type of entity for context

        Returns:
            Dictionary containing data summary statistics
        """
        if df.empty:
            return {
                "total_records": 0,
                "total_columns": 0,
                "empty_records": 0,
                "data_quality_score": 0.0,
            }

        total_records = len(df)
        total_columns = len(df.columns)
        empty_records = df.isnull().all(axis=1).sum()

        # Calculate data quality score (percentage of non-null values)
        total_cells = total_records * total_columns
        non_null_cells = df.count().sum()
        data_quality_score = (non_null_cells / total_cells) * 100 if total_cells > 0 else 0.0

        return {
            "total_records": total_records,
            "total_columns": total_columns,
            "empty_records": int(empty_records),
            "data_quality_score": round(data_quality_score, 2),
        }

    @staticmethod
    def standardize_text(text: str) -> str:
        """
        Standardize text by cleaning and normalizing.

        Args:
            text: Text to standardize

        Returns:
            Standardized text
        """
        if pd.isna(text) or text is None:
            return ""

        # Convert to string and strip whitespace
        text = str(text).strip()

        # Replace multiple spaces with single space
        text = " ".join(text.split())

        return text

    @staticmethod
    def validate_id_format(id_value: str, id_type: str) -> bool:
        """
        Validate that an ID follows expected format.

        Args:
            id_value: ID value to validate
            id_type: Type of ID for context

        Returns:
            True if ID format is valid, False otherwise
        """
        if pd.isna(id_value) or not id_value:
            return False

        id_str = str(id_value).strip()

        # Basic validation - not empty and contains alphanumeric characters
        if not id_str or not any(c.isalnum() for c in id_str):
            logger.warning(f"Invalid {id_type} ID format: '{id_value}'")
            return False

        return True
