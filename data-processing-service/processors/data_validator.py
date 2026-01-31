import pandas as pd

"""
Data Validator

Handles comprehensive data validation and quality checks.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DataValidator:
    """
    Comprehensive data validator for extracted data.

    Provides validation for data quality, consistency, and business rules.
    """

    def __init__(self):
        """Initialize the data validator."""
        self.validation_rules = {
            "risk": {
                "required_fields": ["risk_id", "risk_title"],
                "id_pattern": r"^AIR\.\d{3}$",
                "min_title_length": 5,
                "max_title_length": 255,
            },
            "control": {
                "required_fields": ["control_id", "control_title"],
                "id_pattern": r"^AI[A-Z]{2,4}\.\d+$",
                "min_title_length": 5,
                "max_title_length": 255,
            },
            "question": {
                "required_fields": ["question_id", "question_text"],
                "id_pattern": r"^[A-Z]{2,6}\d+\.\d+$|^Q\d+$",
                "min_title_length": 10,
                "max_title_length": 1000,
            },
        }

    def validate_entity_data(self, df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Validate data for a specific entity type.

        Args:
            df: DataFrame containing data to validate
            entity_type: Type of entity (risk, control, question)

        Returns:
            Dictionary containing validation results
        """
        if entity_type not in self.validation_rules:
            raise ValueError(f"Unknown entity type: {entity_type}")

        rules = self.validation_rules[entity_type]
        results = {
            "entity_type": entity_type,
            "total_records": len(df),
            "valid_records": 0,
            "invalid_records": 0,
            "errors": [],
            "warnings": [],
            "validation_passed": True,
        }

        if df.empty:
            results["errors"].append("No data found")
            results["validation_passed"] = False
            return results

        # Check required fields
        missing_fields = [field for field in rules["required_fields"] if field not in df.columns]
        if missing_fields:
            results["errors"].append(f"Missing required fields: {missing_fields}")
            results["validation_passed"] = False
            return results

        # Validate each record
        for idx, row in df.iterrows():
            record_errors = self._validate_record(row, rules, entity_type)
            if record_errors:
                results["invalid_records"] += 1
                results["errors"].extend([f"Row {idx}: {error}" for error in record_errors])
            else:
                results["valid_records"] += 1

        # Check for duplicates
        id_field = rules["required_fields"][0]  # First required field is usually the ID
        if id_field in df.columns:
            duplicates = df[df.duplicated(subset=[id_field], keep=False)]
            if not duplicates.empty:
                results["warnings"].append(f"Found {len(duplicates)} duplicate records")

        # Overall validation result
        if results["invalid_records"] > 0:
            results["validation_passed"] = False

        return results

    def _validate_record(self, row: pd.Series, rules: Dict[str, Any], entity_type: str) -> List[str]:
        """
        Validate a single record.

        Args:
            row: DataFrame row to validate
            rules: Validation rules for the entity type
            entity_type: Type of entity

        Returns:
            List of validation errors
        """
        errors = []

        # Check required fields are not empty
        for field in rules["required_fields"]:
            if field in row.index and (pd.isna(row[field]) or str(row[field]).strip() == ""):
                errors.append(f"Empty required field: {field}")

        # Validate ID format
        id_field = rules["required_fields"][0]
        if id_field in row.index and not pd.isna(row[id_field]):
            id_value = str(row[id_field]).strip()
            if not re.match(rules["id_pattern"], id_value):
                errors.append(f"Invalid ID format: {id_value}")

        # Validate title length
        title_field = rules["required_fields"][1]
        if title_field in row.index and not pd.isna(row[title_field]):
            title_value = str(row[title_field]).strip()
            if len(title_value) < rules["min_title_length"]:
                errors.append(f"Title too short: {len(title_value)} < {rules['min_title_length']}")
            if len(title_value) > rules["max_title_length"]:
                errors.append(f"Title too long: {len(title_value)} > {rules['max_title_length']}")

        return errors

    def validate_data_consistency(
        self,
        risks_df: pd.DataFrame,
        controls_df: pd.DataFrame,
        questions_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Validate consistency across different entity types.

        Args:
            risks_df: Risks DataFrame
            controls_df: Controls DataFrame
            questions_df: Questions DataFrame

        Returns:
            Dictionary containing consistency validation results
        """
        results = {
            "consistency_passed": True,
            "errors": [],
            "warnings": [],
            "statistics": {},
        }

        # Check for orphaned references
        if not risks_df.empty and not controls_df.empty:
            orphaned_controls = self._find_orphaned_references(risks_df, controls_df, "risk_id", "control_id")
            if orphaned_controls:
                results["warnings"].append(
                    f"Found {len(orphaned_controls)} potentially orphaned " f"control references"
                )

        # Check for data quality issues
        results["statistics"]["risks"] = self._get_data_quality_stats(risks_df, "risk")
        results["statistics"]["controls"] = self._get_data_quality_stats(controls_df, "control")
        results["statistics"]["questions"] = self._get_data_quality_stats(questions_df, "question")

        return results

    def _find_orphaned_references(
        self,
        parent_df: pd.DataFrame,
        child_df: pd.DataFrame,
        parent_id_field: str,
        child_id_field: str,
    ) -> List[str]:
        """
        Find orphaned references between DataFrames.

        Args:
            parent_df: Parent DataFrame
            child_df: Child DataFrame
            parent_id_field: Parent ID field name
            child_id_field: Child ID field name

        Returns:
            List of orphaned IDs
        """
        if parent_df.empty or child_df.empty:
            return []

        parent_ids = set(parent_df[parent_id_field].dropna().astype(str))
        child_ids = set(child_df[child_id_field].dropna().astype(str))

        # Find child IDs that don't have corresponding parent IDs
        orphaned = child_ids - parent_ids
        return list(orphaned)

    def _get_data_quality_stats(self, df: pd.DataFrame, entity_type: str) -> Dict[str, Any]:
        """
        Get data quality statistics for a DataFrame.

        Args:
            df: DataFrame to analyze
            entity_type: Type of entity

        Returns:
            Dictionary containing quality statistics
        """
        if df.empty:
            return {"total_records": 0, "completeness": 0}

        stats = {
            "total_records": len(df),
            "columns": len(df.columns),
            "completeness": {},
        }

        # Calculate completeness for each column
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            stats["completeness"][col] = non_null_count / len(df)

        return stats

    def validate_file_structure(self, file_path: Path, entity_type: str) -> Dict[str, Any]:
        """
        Validate Excel file structure.

        Args:
            file_path: Path to the Excel file
            entity_type: Type of entity

        Returns:
            Dictionary containing file validation results
        """
        results = {
            "file_path": str(file_path),
            "entity_type": entity_type,
            "validation_passed": True,
            "errors": [],
            "warnings": [],
            "file_info": {},
        }

        try:
            # Check if file exists
            if not file_path.exists():
                results["errors"].append("File does not exist")
                results["validation_passed"] = False
                return results

            # Get file info
            stat = file_path.stat()
            results["file_info"] = {
                "size_bytes": stat.st_size,
                "modified_time": stat.st_mtime,
                "extension": file_path.suffix,
            }

            # Check file extension
            if file_path.suffix.lower() not in [".xlsx", ".xls"]:
                results["errors"].append(f"Invalid file extension: {file_path.suffix}")
                results["validation_passed"] = False

            # Try to read the file
            try:
                df = pd.read_excel(file_path)
                results["file_info"]["sheets"] = len(df.columns)
                results["file_info"]["rows"] = len(df)
            except Exception as e:
                results["errors"].append(f"Error reading Excel file: {str(e)}")
                results["validation_passed"] = False

        except Exception as e:
            results["errors"].append(f"File validation error: {str(e)}")
            results["validation_passed"] = False

        return results

    def generate_validation_report(self, validation_results: List[Dict[str, Any]]) -> str:
        """
        Generate a human-readable validation report.

        Args:
            validation_results: List of validation result dictionaries

        Returns:
            Formatted validation report string
        """
        report = []
        report.append("=" * 60)
        report.append("DATA VALIDATION REPORT")
        report.append("=" * 60)

        total_entities = len(validation_results)
        passed_entities = sum(1 for result in validation_results if result.get("validation_passed", False))

        report.append(f"Total entities validated: {total_entities}")
        report.append(f"Entities passed validation: {passed_entities}")
        report.append(f"Entities failed validation: {total_entities - passed_entities}")
        report.append("")

        for result in validation_results:
            entity_type = result.get("entity_type", "unknown")
            status = "PASSED" if result.get("validation_passed", False) else "FAILED"

            report.append(f"{entity_type.upper()} VALIDATION: {status}")
            report.append(f"  Total records: {result.get('total_records', 0)}")
            report.append(f"  Valid records: {result.get('valid_records', 0)}")
            report.append(f"  Invalid records: {result.get('invalid_records', 0)}")

            if result.get("errors"):
                report.append("  Errors:")
                for error in result["errors"][:5]:  # Show first 5 errors
                    report.append(f"    - {error}")
                if len(result["errors"]) > 5:
                    report.append(f"    ... and {len(result['errors']) - 5} more errors")

            if result.get("warnings"):
                report.append("  Warnings:")
                for warning in result["warnings"][:3]:  # Show first 3 warnings
                    report.append(f"    - {warning}")
                if len(result["warnings"]) > 3:
                    report.append(f"    ... and {len(result['warnings']) - 3} more warnings")

            report.append("")

        report.append("=" * 60)
        return "\n".join(report)
