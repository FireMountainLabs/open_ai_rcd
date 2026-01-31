import pandas as pd

"""
Resilient Data Extractor

Handles data extraction with dynamic field detection and schema adaptation.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)


class ResilientExtractor(BaseProcessor):
    """
    Resilient data extractor that handles schema changes and ID format variations.

    Uses dynamic field detection to adapt to changes in Excel file structure.
    """

    def __init__(self, config_manager, database_manager):
        """
        Initialize the resilient extractor.

        Args:
            config_manager: Configuration manager instance
            database_manager: Database manager instance
        """
        super().__init__(config_manager, database_manager)
        self.field_mappings = {}

    def extract_data(self, file_path: Path, entity_type: str) -> pd.DataFrame:
        """
        Extract data using resilient field detection.

        Args:
            file_path: Path to the Excel file
            entity_type: Type of entity (risk, control, question)

        Returns:
            DataFrame containing extracted data
        """
        logger.info(f"Extracting {entity_type} data using resilient mode from {file_path}")

        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()

            # Detect fields dynamically
            field_mapping = self.field_detector.detect_fields(df, entity_type)
            self.field_mappings[entity_type] = field_mapping

            logger.info(f"Detected field mappings for {entity_type}: {field_mapping}")

            # Extract data based on detected fields
            extracted_data = []
            for _, row in df.iterrows():
                record = self._extract_record_resilient(row, field_mapping, entity_type)
                if record:
                    extracted_data.append(record)

            result_df = pd.DataFrame(extracted_data)

            # Normalize data
            result_df = self.normalize_data(result_df, entity_type)

            # Remove duplicates
            if not result_df.empty:
                id_column = self._get_id_column(entity_type)
                if id_column in result_df.columns:
                    initial_count = len(result_df)
                    result_df = result_df.drop_duplicates(subset=[id_column], keep="first")
                    final_count = len(result_df)
                    if initial_count != final_count:
                        logger.info(f"Removed {initial_count - final_count} duplicate " f"{entity_type} records")

            logger.info(f"Extracted {len(result_df)} {entity_type} records using resilient mode")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting {entity_type} data from {file_path}: {e}")
            raise

    def _extract_record_resilient(
        self, row: pd.Series, field_mapping: Dict[str, str], entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Extract a single record using resilient field detection.

        Args:
            row: DataFrame row
            field_mapping: Field mapping dictionary
            entity_type: Type of entity

        Returns:
            Dictionary containing extracted record data
        """
        record = {}

        # Extract ID and title (required fields)
        if "id" not in field_mapping or "title" not in field_mapping:
            logger.warning(f"Missing required fields (id, title) for {entity_type}")
            return None

        record["id"] = self._clean_value(row.get(field_mapping["id"], ""))
        record["title"] = self._clean_value(row.get(field_mapping["title"], ""))

        # Skip records without ID or title
        if not record["id"] or not record["title"]:
            return None

        # Extract optional fields
        optional_fields = ["description", "category", "topic", "domain", "type"]
        for field in optional_fields:
            if field in field_mapping:
                record[field] = self._clean_value(row.get(field_mapping[field], ""))

        # Add entity-specific fields
        if entity_type == "risk":
            record["risk_id"] = record["id"]
            record["risk_title"] = record["title"]
            record["risk_description"] = record.get("description", "")
        elif entity_type == "control":
            record["control_id"] = record["id"]
            record["control_title"] = record["title"]
            record["control_description"] = record.get("description", "")
        elif entity_type == "question":
            record["question_id"] = record["id"]
            record["question_text"] = record["title"]
            record["category"] = record.get("category", "")
            record["topic"] = record.get("topic", "")

        return record

    def get_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Get detected field mappings.

        Returns:
            Dictionary of field mappings by entity type
        """
        return self.field_mappings.copy()

    def detect_schema_changes(self, old_file: Path, new_file: Path, entity_type: str) -> Dict[str, Any]:
        """
        Detect schema changes between two files.

        Args:
            old_file: Path to the old file
            new_file: Path to the new file
            entity_type: Type of entity

        Returns:
            Dictionary containing schema change information
        """
        try:
            old_df = pd.read_excel(old_file)
            new_df = pd.read_excel(new_file)

            return self.field_detector.detect_schema_changes(old_df, new_df, entity_type)
        except Exception as e:
            logger.error(f"Error detecting schema changes: {e}")
            return {"error": str(e)}
