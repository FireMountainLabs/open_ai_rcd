import pandas as pd

"""
Mapping Data Extractor

Creates relationship mappings between different entities (risks, controls, questions).
Handles complex relationship extraction and validation.
"""

import logging
from pathlib import Path
from typing import List, Tuple

from utils.id_normalizer import IDNormalizer
from utils.service_acronyms import normalize_service_name_for_id

logger = logging.getLogger(__name__)


class MappingExtractor:
    """
    Extracts and creates relationship mappings between entities.

    Handles mapping extraction from questions data and creates risk-control
    mappings from control data with proper validation.
    """

    def __init__(self, config_manager):
        """
        Initialize the mapping extractor.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.id_normalizer = IDNormalizer()

    def extract_question_mappings(
        self,
        excel_path: Path,
        risks_df: pd.DataFrame = None,
        controls_df: pd.DataFrame = None,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extract risk and control mappings from questions data (all sheets).

        Args:
            excel_path: Path to the Excel file containing mappings
            risks_df: DataFrame containing risks data for validation (optional)
            controls_df: DataFrame containing controls data for validation (optional)

        Returns:
            Tuple of (question_risk_mappings, question_control_mappings) DataFrames
        """
        logger.info(f"Extracting mappings from {excel_path}")

        try:
            # Read all sheets from the questions Excel file
            xl = pd.ExcelFile(excel_path)

            # Get column mappings from config
            col_map = self.config_manager.get_data_source_config("questions")["columns"]

            question_risk_mappings = []
            question_control_mappings = []

            for sheet_name in xl.sheet_names:
                try:
                    logger.info(f"Processing mappings from sheet: {sheet_name}")
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)

                    # Handle empty sheets gracefully
                    if df.empty or len(df.columns) == 0:
                        logger.warning(f"Sheet '{sheet_name}' is empty or has no columns, skipping")
                        continue

                    df.columns = df.columns.str.strip()

                    # Extract mappings from this sheet
                    sheet_risk_mappings, sheet_control_mappings = self._extract_mappings_from_sheet(
                        df, col_map, sheet_name, risks_df, controls_df
                    )

                    question_risk_mappings.extend(sheet_risk_mappings)
                    question_control_mappings.extend(sheet_control_mappings)

                    logger.info(
                        f"Extracted {len(sheet_risk_mappings)} risk mappings and "
                        f"{len(sheet_control_mappings)} control mappings from sheet "
                        f"'{sheet_name}'"
                    )

                except Exception as e:
                    logger.warning(f"Error reading mappings from sheet {sheet_name}: {e}")
                    continue

            # Create DataFrames and remove duplicates
            question_risk_df = pd.DataFrame(question_risk_mappings)
            question_control_df = pd.DataFrame(question_control_mappings)

            if not question_risk_df.empty:
                question_risk_df = question_risk_df.drop_duplicates(subset=["question_id", "risk_id"], keep="first")

            if not question_control_df.empty:
                question_control_df = question_control_df.drop_duplicates(
                    subset=["question_id", "control_id"], keep="first"
                )

            logger.info(
                f"Extracted {len(question_risk_df)} unique question-risk mappings "
                f"and {len(question_control_df)} unique question-control mappings"
            )
            return question_risk_df, question_control_df

        except Exception as e:
            logger.error(f"Error extracting mappings from questions: {e}")
            return pd.DataFrame(), pd.DataFrame()

    def _extract_mappings_from_sheet(
        self,
        df: pd.DataFrame,
        col_map: dict,
        sheet_name: str,
        risks_df: pd.DataFrame = None,
        controls_df: pd.DataFrame = None,
    ) -> Tuple[List[dict], List[dict]]:
        """
        Extract mappings from a single sheet.

        Args:
            df: DataFrame containing sheet data
            col_map: Column mapping configuration
            sheet_name: Name of the sheet being processed
            risks_df: DataFrame containing risks data for validation (optional)
            controls_df: DataFrame containing controls data for validation (optional)

        Returns:
            Tuple of (risk_mappings, control_mappings) lists
        """
        risk_mappings = []
        control_mappings = []

        for _, row in df.iterrows():
            raw_question_id = self._clean_value(row.get(col_map["id"], ""))
            raw_risk_id = self._clean_value(row.get(col_map["risk_mapping"], ""))
            raw_control_id = self._clean_value(row.get(col_map["control_mapping"], ""))

            # Normalize IDs first, then add prefixes to match question extraction logic
            # Note: Don't normalize question IDs to match question extractor behavior
            normalized_risk_id = self.id_normalizer.normalize_risk_id(raw_risk_id) if raw_risk_id else ""
            normalized_control_id = self.id_normalizer.normalize_control_id(raw_control_id) if raw_control_id else ""

            # Create unique question ID using service acronym (matching question extraction logic)
            # Use raw question ID directly to match question extractor behavior
            service_acronym = normalize_service_name_for_id(sheet_name)
            question_id = f"Q.{service_acronym}.{raw_question_id}" if raw_question_id else ""
            risk_id = f"R.{normalized_risk_id}" if normalized_risk_id else ""
            control_id = f"C.{normalized_control_id}" if normalized_control_id else ""

            # Create question-risk mapping if valid and risk exists
            if question_id and risk_id and risk_id != "R.TBD":
                # Validate that the risk exists if risks_df is provided
                if risks_df is not None and not risks_df.empty:
                    if risk_id in risks_df["risk_id"].values:
                        risk_mappings.append({"question_id": question_id, "risk_id": risk_id})
                    else:
                        logger.warning(f"Risk ID '{risk_id}' not found in risks data for question '{question_id}'")
                else:
                    # If no risks data available, still create the mapping
                    risk_mappings.append({"question_id": question_id, "risk_id": risk_id})

            # Create question-control mapping if valid and control exists
            if question_id and control_id and control_id != "C.TBD":
                # Validate that the control exists if controls_df is provided
                if controls_df is not None and not controls_df.empty:
                    if control_id in controls_df["control_id"].values:
                        control_mappings.append({"question_id": question_id, "control_id": control_id})
                    else:
                        logger.warning(
                            f"Control ID '{control_id}' not found in controls data for question '{question_id}'"
                        )
                else:
                    # If no controls data available, still create the mapping
                    control_mappings.append({"question_id": question_id, "control_id": control_id})

        return risk_mappings, control_mappings

    def create_risk_control_mappings(self, risks_df: pd.DataFrame, controls_df: pd.DataFrame) -> pd.DataFrame:
        """
        Create risk-control mappings from the Mapped Risks column in controls data.

        Args:
            risks_df: DataFrame containing risks data
            controls_df: DataFrame containing controls data

        Returns:
            DataFrame containing risk-control mappings
        """
        if controls_df is None or controls_df.empty:
            logger.info("No controls data available for mapping")
            return pd.DataFrame()

        if "mapped_risks" not in controls_df.columns:
            logger.warning("No 'mapped_risks' column found in controls data")
            return pd.DataFrame()

        logger.info("Creating risk-control mappings")

        mappings = []

        for _, control_row in controls_df.iterrows():
            control_id = control_row["control_id"]
            mapped_risks_str = control_row.get("mapped_risks", "")

            if not mapped_risks_str or pd.isna(mapped_risks_str):
                continue

            # Parse the mapped risks string (comma-separated risk IDs)
            raw_risk_ids = [risk_id.strip() for risk_id in str(mapped_risks_str).split(",") if risk_id.strip()]

            for raw_risk_id in raw_risk_ids:
                # Normalize risk ID to match the format in risks data
                # Handle both short format (AIR.1) and padded format (AIR.001)
                normalized_risk_id = self._normalize_risk_id_for_mapping(raw_risk_id)
                risk_id = f"R.{normalized_risk_id}"

                # Verify the risk exists in our risks data
                if risks_df is not None and not risks_df.empty:
                    if risk_id in risks_df["risk_id"].values:
                        mappings.append({"risk_id": risk_id, "control_id": control_id})
                    else:
                        logger.warning(f"Risk ID '{risk_id}' not found in risks data for control " f"'{control_id}'")
                else:
                    # If no risks data available, still create the mapping
                    mappings.append({"risk_id": risk_id, "control_id": control_id})

        result_df = pd.DataFrame(mappings)
        logger.info(f"Created {len(result_df)} risk-control mappings")
        return result_df

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

    def _normalize_risk_id_for_mapping(self, raw_risk_id: str) -> str:
        """
        Normalize risk ID to match the format in risks data.

        Handles conversion from short format (AIR.1) to padded format (AIR.001).

        Args:
            raw_risk_id: Raw risk ID from controls data

        Returns:
            Normalized risk ID
        """
        if not raw_risk_id or raw_risk_id is None:
            return ""

        # Check if it's already in padded format (AIR.001)
        if "." in raw_risk_id and len(raw_risk_id.split(".")[1]) == 3:
            return raw_risk_id

        # Convert short format (AIR.1) to padded format (AIR.001)
        if "." in raw_risk_id:
            prefix, number = raw_risk_id.split(".", 1)
            try:
                padded_number = f"{int(number):03d}"
                return f"{prefix}.{padded_number}"
            except ValueError:
                # If number conversion fails, return as-is
                return raw_risk_id

        return raw_risk_id

    def validate_mappings(self, mappings_df: pd.DataFrame, mapping_type: str) -> bool:
        """
        Validate relationship mappings.

        Args:
            mappings_df: DataFrame containing mappings
            mapping_type: Type of mapping (risk_control, question_risk,
                          question_control)

        Returns:
            True if mappings are valid

        Raises:
            ValueError: If mapping validation fails
        """
        if mappings_df.empty:
            logger.warning(f"No {mapping_type} mappings found")
            return True

        # Check required columns based on mapping type
        if mapping_type == "risk_control":
            required_columns = ["risk_id", "control_id"]
        elif mapping_type in ["question_risk", "question_control"]:
            required_columns = ["question_id", f"{mapping_type.split('_')[1]}_id"]
        else:
            raise ValueError(f"Unknown mapping type: {mapping_type}")

        missing_columns = [col for col in required_columns if col not in mappings_df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns for {mapping_type}: {missing_columns}")

        # Check for empty required fields
        for col in required_columns:
            empty_values = mappings_df[mappings_df[col].str.strip() == ""]
            if not empty_values.empty:
                raise ValueError(f"Found {len(empty_values)} rows with empty {col} in {mapping_type}")

        # Check for duplicate mappings
        duplicate_mappings = mappings_df[mappings_df.duplicated(subset=required_columns, keep=False)]
        if not duplicate_mappings.empty:
            raise ValueError(f"Found {len(duplicate_mappings)} duplicate {mapping_type} mappings")

        logger.info(f"{mapping_type} mappings validation passed")
        return True
