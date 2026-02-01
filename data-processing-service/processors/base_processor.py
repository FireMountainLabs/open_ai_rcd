import pandas as pd

"""
Base Processor for Data Processing Components

Provides common functionality and interfaces for all data processing components.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from config_manager import ConfigManager
from database_manager import DatabaseManager
from utils.field_detector import FieldDetector
from utils.id_normalizer import IDNormalizer

logger = logging.getLogger(__name__)


class BaseProcessor(ABC):
    """
    Base class for all data processing components.

    Provides common functionality and defines the interface that all
    processors must implement.
    """

    def __init__(self, config_manager: ConfigManager, database_manager: DatabaseManager):
        """
        Initialize the base processor.

        Args:
            config_manager: Configuration manager instance
            database_manager: Database manager instance
        """
        self.config_manager = config_manager
        self.database_manager = database_manager
        self.id_normalizer = IDNormalizer(enforce_strict_format=False)
        self.field_detector = FieldDetector(fuzzy_matching=True, case_sensitive=False)

    @abstractmethod
    def extract_data(self, file_path: Path, entity_type: str) -> pd.DataFrame:
        """
        Extract data from a file.

        Args:
            file_path: Path to the input file
            entity_type: Type of entity being extracted

        Returns:
            DataFrame containing extracted data
        """
        pass

    def validate_data(self, df: pd.DataFrame, entity_type: str) -> bool:
        """
        Validate extracted data.

        Args:
            df: DataFrame containing data to validate
            entity_type: Type of entity

        Returns:
            True if data is valid

        Raises:
            ValueError: If data validation fails
        """
        if df.empty:
            raise ValueError(f"No {entity_type} data found")

        # Check required columns based on entity type
        required_columns = self._get_required_columns(entity_type)
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns for {entity_type}: {missing_columns}")

        # Check for empty required fields
        for col in required_columns:
            if col in df.columns:
                empty_count = df[df[col].str.strip() == ""].shape[0]
                if empty_count > 0:
                    logger.warning(f"Found {empty_count} rows with empty {col} in " f"{entity_type} data")

        # Check for duplicate IDs
        id_column = self._get_id_column(entity_type)
        if id_column in df.columns:
            duplicate_count = df[df.duplicated(subset=[id_column], keep=False)].shape[0]
            if duplicate_count > 0:
                logger.warning(f"Found {duplicate_count} rows with duplicate {id_column} in " f"{entity_type} data")

        logger.info(f"{entity_type} data validation passed")
        return True

    def normalize_data(self, df: pd.DataFrame, entity_type: str) -> pd.DataFrame:
        """
        Normalize data by cleaning values and normalizing IDs.

        Args:
            df: DataFrame to normalize
            entity_type: Type of entity

        Returns:
            Normalized DataFrame
        """
        if df.empty:
            return df

        # Clean all string columns
        for col in df.columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(self._clean_value)

        # Normalize IDs
        id_column = self._get_id_column(entity_type)
        if id_column in df.columns:
            df[id_column] = df[id_column].apply(lambda x: self._normalize_id(x, entity_type))
            # Remove rows with invalid IDs
            df = df.dropna(subset=[id_column])

        return df

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

    def _normalize_id(self, entity_id: str, entity_type: str) -> Optional[str]:
        """
        Normalize entity ID based on type.

        Args:
            entity_id: Raw entity ID
            entity_type: Type of entity

        Returns:
            Normalized ID or None if invalid
        """
        if entity_type == "risk":
            return self.id_normalizer.normalize_risk_id(entity_id)
        elif entity_type == "control":
            return self.id_normalizer.normalize_control_id(entity_id)
        elif entity_type == "question":
            return self.id_normalizer.normalize_question_id(entity_id)
        else:
            return entity_id

    def _get_required_columns(self, entity_type: str) -> List[str]:
        """
        Get required columns for an entity type.

        Args:
            entity_type: Type of entity

        Returns:
            List of required column names
        """
        base_columns = {
            "risk": ["risk_id", "risk_title"],
            "control": ["control_id", "control_title"],
            "question": ["question_id", "question_text"],
        }
        return base_columns.get(entity_type, [])

    def _get_id_column(self, entity_type: str) -> str:
        """
        Get the ID column name for an entity type.

        Args:
            entity_type: Type of entity

        Returns:
            ID column name
        """
        id_columns = {
            "risk": "risk_id",
            "control": "control_id",
            "question": "question_id",
        }
        return id_columns.get(entity_type, "id")

    def get_processing_stats(self, df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Get processing statistics for extracted data.

        Args:
            df: DataFrame containing processed data
            entity_type: Type of entity

        Returns:
            Dictionary containing processing statistics
        """
        stats = {
            "entity_type": entity_type,
            "total_records": len(df),
            "columns": list(df.columns),
            "column_count": len(df.columns),
        }

        # Add completeness statistics
        if not df.empty:
            for col in df.columns:
                non_null_count = df[col].notna().sum()
                stats[f"{col}_completeness"] = non_null_count / len(df)

        return stats
