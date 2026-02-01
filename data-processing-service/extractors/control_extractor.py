import pandas as pd

"""
Control Data Extractor

Extracts control data from AI Control Framework Excel files across multiple sheets.
Handles complex multi-sheet extraction with validation and relationship mapping.
"""

import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


class ControlExtractor:
    """
    Extracts control data from AI Control Framework Excel files.

    Handles multi-sheet Excel files and extracts control data with proper
    validation and relationship mapping capabilities.
    """

    def __init__(self, config_manager):
        """
        Initialize the control extractor.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    def extract(self, excel_path: Path) -> pd.DataFrame:
        """
        Extract controls from the AI Control Framework Excel file (all sheets).

        Args:
            excel_path: Path to the Excel file containing controls

        Returns:
            DataFrame containing extracted control data

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file format is invalid
        """
        if not excel_path.exists():
            raise FileNotFoundError(f"Control Excel file not found: {excel_path}")

        logger.info(f"Extracting controls from {excel_path}")

        try:
            # Read all sheets from the Excel file
            xl = pd.ExcelFile(excel_path)
            all_controls = []

            # Get column mappings from config
            col_map = self.config_manager.get_data_source_config("controls")["columns"]

            # Check if "Risks" or "Mapped Risks" column exists in any sheet
            if not self._has_risks_column(excel_path, xl.sheet_names):
                logger.warning("'Risks' or 'Mapped Risks' column not found in Control Framework Excel file")
                return pd.DataFrame()

            for sheet_name in xl.sheet_names:
                try:
                    logger.info(f"Processing sheet: {sheet_name}")
                    df = pd.read_excel(excel_path, sheet_name=sheet_name)

                    # Handle empty sheets gracefully
                    if df.empty or len(df.columns) == 0:
                        logger.warning(f"Sheet '{sheet_name}' is empty or has no columns, skipping")
                        continue

                    df.columns = df.columns.str.strip()

                    # Skip sheets that don't have the required Risks column
                    if "Risks" not in df.columns and "Mapped Risks" not in df.columns:
                        logger.warning(f"Sheet '{sheet_name}' missing 'Risks' or 'Mapped Risks' column, " "skipping")
                        continue

                    # Extract controls from this sheet
                    sheet_controls = self._extract_controls_from_sheet(df, col_map, sheet_name)
                    all_controls.extend(sheet_controls)

                    logger.info(f"Extracted {len(sheet_controls)} controls from sheet " f"'{sheet_name}'")

                except Exception as e:
                    logger.warning(f"Error reading sheet {sheet_name}: {e}")
                    continue

            result_df = pd.DataFrame(all_controls)

            # Remove duplicates based on control_id
            initial_count = len(result_df)
            result_df = result_df.drop_duplicates(subset=["control_id"], keep="first")
            final_count = len(result_df)

            if initial_count != final_count:
                logger.info(f"Removed {initial_count - final_count} duplicate controls")

            logger.info(f"Extracted {len(result_df)} unique controls")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting controls from {excel_path}: {e}")
            raise

    def _extract_controls_from_sheet(self, df: pd.DataFrame, col_map: dict, sheet_name: str) -> List[dict]:
        """
        Extract controls from a single sheet.

        Args:
            df: DataFrame containing sheet data
            col_map: Column mapping configuration
            sheet_name: Name of the sheet being processed

        Returns:
            List of control dictionaries
        """
        controls = []

        for _, row in df.iterrows():
            # Handle different column structures - detect format based on available columns
            if "Code" in row.index and "Purpose" in row.index:
                # Domains-style format: Code -> Purpose
                raw_control_id = self._clean_value(row.get("Code", ""))
                control_title = self._clean_value(row.get("Purpose", ""))
                control_description = self._clean_value(row.get("Purpose", ""))
            elif "Sub-Control" in row.index or "Sub-Control ID" in row.index:
                # Individual sheets format: Sub-Control or Sub-Control ID -> Control Title
                raw_control_id = self._clean_value(row.get("Sub-Control", "") or row.get("Sub-Control ID", ""))
                control_title = self._clean_value(row.get("Control Title", ""))
                control_description = self._clean_value(row.get("Control Description", ""))
            else:
                # Fallback: try to find any ID-like column and title-like column
                raw_control_id = ""
                control_title = ""
                control_description = ""

                # Look for ID-like columns
                for col in row.index:
                    if any(keyword in col.lower() for keyword in ["id", "code", "control"]):
                        if not raw_control_id:  # Take the first one found
                            raw_control_id = self._clean_value(row.get(col, ""))

                # Look for title-like columns
                for col in row.index:
                    if any(keyword in col.lower() for keyword in ["title", "purpose", "name"]):
                        if not control_title:  # Take the first one found
                            control_title = self._clean_value(row.get(col, ""))
                            control_description = self._clean_value(row.get(col, ""))

            # Only include rows with valid ID and title
            if raw_control_id and control_title:
                # Prepend C. to make control IDs easily identifiable
                if sheet_name == "Domains":
                    control_id = f"C.{raw_control_id}"
                else:
                    control_id = f"C.{raw_control_id}"  # Sub-Control already has the prefix (e.g., AIIM.1)

                controls.append(
                    {
                        "control_id": control_id,
                        "control_title": control_title,
                        "control_description": control_description,
                        "mapped_risks": self._clean_value(row.get("Risks", "") or row.get("Mapped Risks", "")),
                        "asset_type": self._clean_value(row.get("Asset Type", "")),
                        "control_type": self._clean_value(row.get("Control Type", "")),
                        "security_function": self._clean_value(row.get("Security Function", "")),
                        "maturity_level": self._clean_value(row.get("Maturity", "")),
                    }
                )
            else:
                logger.warning(f"Skipping row with missing ID or title in sheet " f"'{sheet_name}': {row.to_dict()}")

        return controls

    def _has_risks_column(self, excel_path: Path, sheet_names: List[str]) -> bool:
        """
        Check if any sheet has the required 'Risks' or 'Mapped Risks' column.

        Args:
            excel_path: Path to the Excel file
            sheet_names: List of sheet names to check

        Returns:
            True if any sheet has the 'Risks' or 'Mapped Risks' column
        """
        for sheet_name in sheet_names:
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                if "Risks" in df.columns or "Mapped Risks" in df.columns:
                    return True
            except Exception:
                continue
        return False

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
        Validate extracted control data.

        Args:
            df: DataFrame containing control data

        Returns:
            True if data is valid

        Raises:
            ValueError: If data validation fails
        """
        if df.empty:
            raise ValueError("No control data found")

        # Check required columns
        required_columns = ["control_id", "control_title"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check for empty required fields
        empty_ids = df[df["control_id"].str.strip() == ""]
        if not empty_ids.empty:
            raise ValueError(f"Found {len(empty_ids)} rows with empty control_id")

        empty_titles = df[df["control_title"].str.strip() == ""]
        if not empty_titles.empty:
            raise ValueError(f"Found {len(empty_titles)} rows with empty control_title")

        # Check for duplicate IDs
        duplicate_ids = df[df.duplicated(subset=["control_id"], keep=False)]
        if not duplicate_ids.empty:
            raise ValueError(f"Found {len(duplicate_ids)} rows with duplicate control_id")

        logger.info("Control data validation passed")
        return True
