import pandas as pd

"""
Standard Data Extractor

Handles data extraction using configuration-based field mapping.
"""

import logging
from pathlib import Path
from typing import Dict

from extractors.control_extractor import ControlExtractor
from extractors.question_extractor import QuestionExtractor
from extractors.risk_extractor import RiskExtractor

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class StandardExtractor(BaseProcessor):
    """
    Standard data extractor that uses configuration-based field mapping.

    Uses predefined extractors and configuration to extract data from Excel files.
    """

    def __init__(self, config_manager, database_manager):
        """
        Initialize the standard extractor.

        Args:
            config_manager: Configuration manager instance
            database_manager: Database manager instance
        """
        super().__init__(config_manager, database_manager)

        # Initialize standard extractors
        self.risk_extractor = RiskExtractor(config_manager)
        self.control_extractor = ControlExtractor(config_manager)
        self.question_extractor = QuestionExtractor(config_manager)

    def extract_data(self, file_path: Path, entity_type: str) -> pd.DataFrame:
        """
        Extract data using standard configuration-based approach.

        Args:
            file_path: Path to the Excel file
            entity_type: Type of entity (risk, control, question)

        Returns:
            DataFrame containing extracted data
        """
        logger.info(f"Extracting {entity_type} data using standard mode from {file_path}")

        try:
            # Use appropriate extractor based on entity type
            if entity_type == "risk":
                result_df = self.risk_extractor.extract(file_path)
            elif entity_type == "control":
                result_df = self.control_extractor.extract(file_path)
            elif entity_type == "question":
                result_df = self.question_extractor.extract(file_path)
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")

            # Normalize data
            result_df = self.normalize_data(result_df, entity_type)

            logger.info(f"Extracted {len(result_df)} {entity_type} records using standard mode")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting {entity_type} data from {file_path}: {e}")
            raise

    def validate_extraction_config(self, entity_type: str) -> bool:
        """
        Validate that extraction configuration is available for entity type.

        Args:
            entity_type: Type of entity

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        try:
            config = self.config_manager.get_data_source_config(entity_type)

            # Check required fields
            required_fields = ["file", "columns"]
            for field in required_fields:
                if field not in config:
                    raise ValueError(f"Missing '{field}' configuration for {entity_type}")

            # Check column mappings
            columns = config["columns"]
            required_columns = ["id", "title"]
            for col in required_columns:
                if col not in columns:
                    raise ValueError(f"Missing '{col}' column mapping for {entity_type}")

            logger.info(f"Extraction configuration validated for {entity_type}")
            return True

        except Exception as e:
            logger.error(f"Configuration validation failed for {entity_type}: {e}")
            raise

    def get_column_mappings(self, entity_type: str) -> Dict[str, str]:
        """
        Get column mappings for an entity type.

        Args:
            entity_type: Type of entity

        Returns:
            Dictionary mapping field names to column names
        """
        try:
            config = self.config_manager.get_data_source_config(entity_type)
            return config.get("columns", {})
        except Exception as e:
            logger.error(f"Error getting column mappings for {entity_type}: {e}")
            return {}

    def update_column_mappings(self, entity_type: str, mappings: Dict[str, str]) -> None:
        """
        Update column mappings for an entity type.

        Args:
            entity_type: Type of entity
            mappings: New column mappings
        """
        try:
            config = self.config_manager.load_config()
            if "data_sources" not in config:
                config["data_sources"] = {}
            if entity_type not in config["data_sources"]:
                config["data_sources"][entity_type] = {}

            config["data_sources"][entity_type]["columns"] = mappings

            # Note: This would need to be implemented in ConfigManager to persist
            # changes
            logger.info(f"Updated column mappings for {entity_type}: {mappings}")

        except Exception as e:
            logger.error(f"Error updating column mappings for {entity_type}: {e}")
            raise
