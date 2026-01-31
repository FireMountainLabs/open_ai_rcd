import pandas as pd

"""
Dynamic field detection utilities for AIML risk management framework.

This module provides intelligent field detection and mapping capabilities
to handle schema changes in Excel files automatically.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FieldDetector:
    """
    Detects and maps fields dynamically from Excel files.

    This class provides intelligent field detection capabilities to handle
    schema changes and different column naming conventions automatically.
    """

    # Field patterns for different entity types
    FIELD_PATTERNS = {
        "risk": {
            "id": [r"^id$", r"^risk.?id$", r"^air\.?\d*$"],
            "title": [r"^title$", r"^risk$", r"^risk.?title$", r"^name$"],
            "description": [
                r"^description$",
                r"^risk.?description$",
                r"^details$",
                r"^summary$",
            ],
            "category": [
                r"^category$",
                r"^mit.*risk.*category$",
                r"^mit.*ai.*risk.*category$",
                r"^type$",
                r"^class$",
            ],
            "subdomain": [
                r"^subdomain$",
                r"^mit.*risk.*subdomain$",
                r"^mit.*ai.*risk.*subdomain$",
                r"^sub.?category$",
            ],
            "tactic": [
                r"^tactic$",
                r"^mitre.*atlas.*tactic$",
                r"^mitre.*atlas.*tactic$",
                r"^attack.?tactic$",
            ],
            "technique": [
                r"^technique$",
                r"^mitre.*atlas.*technique$",
                r"^mitre.*atlas.*technique$",
                r"^attack.?technique$",
            ],
            "likelihood": [
                r"^likelihood$",
                r"^possible.*plausible$",
                r"^possible.*vs.*plausible$",
                r"^risk.?level$",
                r"^probability$",
            ],
        },
        "control": {
            "id": [
                r"^id$",
                r"^control.?id$",
                r"^sub.?control$",
                r"^control.?number$",
                r"^code$",
                r"^#",
            ],
            "title": [
                r"^title$",
                r"^control.?title$",
                r"^name$",
                r"^control.?name$",
                r"^purpose$",
            ],
            "description": [
                r"^description$",
                r"^control.?description$",
                r"^details$",
                r"^summary$",
                r"^purpose$",
            ],
            "domain": [r"^domain$", r"^control.?domain$", r"^category$", r"^type$"],
            "mapped_risks": [
                r"^mapped.?risks$",
                r"^risk.?mapping$",
                r"^related.?risks$",
            ],
            "asset_type": [r"^asset.?type$", r"^asset$", r"^resource.?type$"],
            "control_type": [r"^control.?type$", r"^type$", r"^category$", r"^class$"],
            "security_function": [r"^security.?function$", r"^function$", r"^purpose$"],
            "maturity": [r"^maturity$", r"^maturity.?level$", r"^level$", r"^stage$"],
        },
        "question": {
            "id": [r"^id$", r"^question.?id$", r"^question.?number$", r"^q\d*$"],
            "text": [r"^text$", r"^question.?text$", r"^question$", r"^content$"],
            "category": [r"^category$", r"^type$", r"^class$", r"^domain$"],
            "topic": [r"^topic$", r"^subject$", r"^theme$", r"^area$"],
            "risk_mapping": [
                r"^risk.?mapping$",
                r"^aiml.*risk.*taxonomy$",
                r"^aiml_risk_taxonomy$",
                r"^related.?risks$",
            ],
            "control_mapping": [
                r"^control.?mapping$",
                r"^aiml.*control$",
                r"^aiml_control$",
                r"^related.?controls$",
            ],
        },
    }

    def __init__(self, fuzzy_matching: bool = True, case_sensitive: bool = False):
        """
        Initialize the field detector.

        Args:
            fuzzy_matching: If True, enables fuzzy matching for field names
            case_sensitive: If True, field matching is case sensitive
        """
        self.fuzzy_matching = fuzzy_matching
        self.case_sensitive = case_sensitive

    def detect_fields(self, df: pd.DataFrame, entity_type: str) -> Dict[str, str]:
        """
        Detect and map fields in a DataFrame for a specific entity type.

        Args:
            df: DataFrame to analyze
            entity_type: Type of entity (risk, control, question)

        Returns:
            Dictionary mapping field names to detected column names
        """
        if entity_type not in self.FIELD_PATTERNS:
            logger.warning(f"Unknown entity type: {entity_type}")
            return {}

        field_mapping = {}
        columns = df.columns.tolist()

        # Clean column names
        clean_columns = [self._clean_column_name(col) for col in columns]

        for field_name, patterns in self.FIELD_PATTERNS[entity_type].items():
            detected_column = self._find_matching_column(clean_columns, patterns, columns)
            if detected_column:
                field_mapping[field_name] = detected_column
                logger.debug(f"Detected {field_name} -> {detected_column}")

        return field_mapping

    def _clean_column_name(self, column_name: str) -> str:
        """
        Clean a column name for pattern matching.

        Args:
            column_name: Raw column name

        Returns:
            Cleaned column name
        """
        if not isinstance(column_name, str):
            return str(column_name)

        # Strip whitespace
        cleaned = column_name.strip()

        # Convert to lowercase if not case sensitive
        if not self.case_sensitive:
            cleaned = cleaned.lower()

        # Replace common separators with spaces
        cleaned = re.sub(r"[_\-\.,;:]", " ", cleaned)

        # Normalize whitespace
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned.strip()

    def _find_matching_column(
        self, clean_columns: List[str], patterns: List[str], original_columns: List[str]
    ) -> Optional[str]:
        """
        Find a column that matches any of the given patterns.

        Args:
            clean_columns: List of cleaned column names
            patterns: List of regex patterns to match
            original_columns: List of original column names

        Returns:
            Original column name if match found, None otherwise
        """
        for i, clean_col in enumerate(clean_columns):
            for pattern in patterns:
                if re.match(pattern, clean_col, re.IGNORECASE):
                    return original_columns[i]

        return None

    def detect_schema_changes(self, old_df: pd.DataFrame, new_df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Detect schema changes between two DataFrames.

        Args:
            old_df: Original DataFrame
            new_df: New DataFrame
            entity_type: Type of entity (risk, control, question)

        Returns:
            Dictionary containing schema change information
        """
        old_fields = self.detect_fields(old_df, entity_type)
        new_fields = self.detect_fields(new_df, entity_type)

        # Find changes
        added_fields = set(new_fields.keys()) - set(old_fields.keys())
        removed_fields = set(old_fields.keys()) - set(new_fields.keys())
        changed_fields = set()

        # Check for field mapping changes
        for field in set(old_fields.keys()) & set(new_fields.keys()):
            if old_fields[field] != new_fields[field]:
                changed_fields.add(field)

        return {
            "added_fields": list(added_fields),
            "removed_fields": list(removed_fields),
            "changed_fields": list(changed_fields),
            "old_field_mapping": old_fields,
            "new_field_mapping": new_fields,
            "schema_stability": len(changed_fields) == 0 and len(removed_fields) == 0,
        }

    def suggest_field_mappings(
        self, df: pd.DataFrame, entity_type: str, required_fields: List[str]
    ) -> Dict[str, List[str]]:
        """
        Suggest possible field mappings for required fields.

        Args:
            df: DataFrame to analyze
            entity_type: Type of entity (risk, control, question)
            required_fields: List of required field names

        Returns:
            Dictionary mapping required fields to suggested column names
        """
        suggestions = {}
        columns = df.columns.tolist()
        clean_columns = [self._clean_column_name(col) for col in columns]

        for field in required_fields:
            if field in self.FIELD_PATTERNS.get(entity_type, {}):
                patterns = self.FIELD_PATTERNS[entity_type][field]
                matches = []

                for i, clean_col in enumerate(clean_columns):
                    for pattern in patterns:
                        if re.match(pattern, clean_col, re.IGNORECASE):
                            matches.append(columns[i])
                            break

                suggestions[field] = matches

        return suggestions

    def validate_required_fields(
        self, df: pd.DataFrame, entity_type: str, required_fields: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields are present in the DataFrame.

        Args:
            df: DataFrame to validate
            entity_type: Type of entity (risk, control, question)
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, missing_fields)
        """
        detected_fields = self.detect_fields(df, entity_type)
        missing_fields = [field for field in required_fields if field not in detected_fields]

        return len(missing_fields) == 0, missing_fields

    def get_field_statistics(self, df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Get statistics about fields in a DataFrame.

        Args:
            df: DataFrame to analyze
            entity_type: Type of entity (risk, control, question)

        Returns:
            Dictionary containing field statistics
        """
        detected_fields = self.detect_fields(df, entity_type)

        # Count non-null values for each detected field
        field_stats = {}
        for field_name, column_name in detected_fields.items():
            if column_name in df.columns:
                non_null_count = df[column_name].notna().sum()
                total_count = len(df)
                field_stats[field_name] = {
                    "column_name": column_name,
                    "non_null_count": int(non_null_count),
                    "total_count": total_count,
                    "completeness": (non_null_count / total_count if total_count > 0 else 0),
                }

        return {
            "detected_fields": detected_fields,
            "field_statistics": field_stats,
            "total_columns": len(df.columns),
            "mapped_columns": len(detected_fields),
        }

    def create_field_mapping_config(self, df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Create a configuration dictionary for field mappings.

        Args:
            df: DataFrame to analyze
            entity_type: Type of entity (risk, control, question)

        Returns:
            Configuration dictionary for field mappings
        """
        detected_fields = self.detect_fields(df, entity_type)

        return {
            "entity_type": entity_type,
            "field_mappings": detected_fields,
            "detection_timestamp": pd.Timestamp.now().isoformat(),
            "total_columns": len(df.columns),
            "mapped_columns": len(detected_fields),
        }
