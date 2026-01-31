import pandas as pd
import re
from pathlib import Path
import logging

"""
Capability Data Extractor

Extracts capability data from AI_ML_Security_Capabilities Excel files with validation and cleaning.
Handles both Technical and Non-Technical capabilities with proper control mapping.
"""

logger = logging.getLogger(__name__)


class CapabilityExtractor:
    """
    Extracts capability data from AI/ML Security Capabilities Excel files.

    Provides specialized extraction logic for capability data with validation,
    cleaning, and normalization capabilities. Handles both technical and
    non-technical capabilities with graceful handling of incomplete control mappings.
    """

    def __init__(self, config_manager):
        """
        Initialize the capability extractor.

        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager

    def extract(self, excel_path: Path) -> pd.DataFrame:
        """
        Extract capabilities from the AI/ML Security Capabilities Excel file.

        Args:
            excel_path: Path to the Excel file containing capabilities

        Returns:
            DataFrame containing extracted capability data

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file format is invalid
        """
        if not excel_path.exists():
            raise FileNotFoundError(f"Capability Excel file not found: {excel_path}")

        logger.info(f"Extracting capabilities from {excel_path}")

        try:
            # Read both sheets
            technical_df = pd.read_excel(excel_path, sheet_name="Technical Capabilities")
            non_technical_df = pd.read_excel(excel_path, sheet_name="Non-Technical Capabilities")

            # Process technical capabilities
            technical_capabilities = self._extract_technical_capabilities(technical_df)

            # Process non-technical capabilities
            non_technical_capabilities = self._extract_non_technical_capabilities(non_technical_df)

            # Combine both types
            all_capabilities = technical_capabilities + non_technical_capabilities

            result_df = pd.DataFrame(all_capabilities)

            # Remove duplicates based on capability_id
            initial_count = len(result_df)
            result_df = result_df.drop_duplicates(subset=["capability_id"], keep="first")
            final_count = len(result_df)

            if initial_count != final_count:
                logger.info(f"Removed {initial_count - final_count} duplicate capabilities")

            logger.info(f"Extracted {len(result_df)} unique capabilities")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting capabilities from {excel_path}: {e}")
            raise

    def _extract_technical_capabilities(self, df: pd.DataFrame) -> list:
        """
        Extract technical capabilities from the Technical Security Capabilities sheet.

        Args:
            df: DataFrame containing technical capabilities

        Returns:
            List of capability dictionaries
        """
        capabilities = []

        # Clean column names
        df.columns = df.columns.str.strip()

        # Map column names (handle variations)
        capability_col = self._find_column(df, ["Technical Capability", "Capability"])
        domain_col = self._find_column(df, ["Capability Domain", "Domain"])
        definition_col = self._find_column(df, ["Capability Definition", "Definition"])
        controls_col = self._find_column(df, ["Controls", "Control IDs"])
        products_col = self._find_column(
            df,
            [
                "Candidate Products (modern, AI-defense)",
                "Products",
                "Candidate Products",
            ],
        )
        notes_col = self._find_column(df, ["Notes", "Note"])

        for idx, row in df.iterrows():
            capability_name = self._clean_value(row.get(capability_col, ""))
            domain = self._clean_value(row.get(domain_col, ""))
            definition = self._clean_value(row.get(definition_col, ""))
            controls = self._clean_value(row.get(controls_col, ""))
            products = self._clean_value(row.get(products_col, ""))
            notes = self._clean_value(row.get(notes_col, ""))

            # Only include rows with valid capability name
            if capability_name:
                capability_id = f"CAP.TECH.{idx + 1:03d}"
                capabilities.append(
                    {
                        "capability_id": capability_id,
                        "capability_name": capability_name,
                        "capability_type": "technical",
                        "capability_domain": domain,
                        "capability_definition": definition,
                        "controls": controls,
                        "candidate_products": products,
                        "notes": notes,
                    }
                )
            else:
                logger.warning(f"Skipping technical capability row with missing name: {row.to_dict()}")

        return capabilities

    def _extract_non_technical_capabilities(self, df: pd.DataFrame) -> list:
        """
        Extract non-technical capabilities from the Non-Technical Capabilities sheet.

        Args:
            df: DataFrame containing non-technical capabilities

        Returns:
            List of capability dictionaries
        """
        capabilities = []

        # Clean column names
        df.columns = df.columns.str.strip()

        # Map column names (handle variations)
        capability_col = self._find_column(df, ["Capability", "Non-Technical Capability"])
        definition_col = self._find_column(df, ["Capability Definition", "Definition"])
        controls_col = self._find_column(df, ["Controls", "Control IDs", "Control Mappings"])
        notes_col = self._find_column(df, ["Notes", "Note"])

        for idx, row in df.iterrows():
            capability_name = self._clean_value(row.get(capability_col, ""))
            definition = self._clean_value(row.get(definition_col, ""))
            controls = self._clean_value(row.get(controls_col, "")) if controls_col else ""
            notes = self._clean_value(row.get(notes_col, "")) if notes_col else ""

            # Only include rows with valid capability name
            if capability_name:
                capability_id = f"CAP.NONTECH.{idx + 1:03d}"
                capabilities.append(
                    {
                        "capability_id": capability_id,
                        "capability_name": capability_name,
                        "capability_type": "non-technical",
                        "capability_domain": "",  # Non-technical capabilities don't have domains
                        "capability_definition": definition,
                        "controls": controls,  # Extract controls from the sheet if present
                        "candidate_products": "",  # Non-technical capabilities don't have products
                        "notes": notes,
                    }
                )
            else:
                logger.warning(f"Skipping non-technical capability row with missing name: {row.to_dict()}")

        return capabilities

    def _find_column(self, df: pd.DataFrame, possible_names: list) -> str:
        """
        Find a column by trying multiple possible names.

        Args:
            df: DataFrame to search
            possible_names: List of possible column names

        Returns:
            First matching column name or empty string if none found
        """
        for name in possible_names:
            if name in df.columns:
                return name
        return ""

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
        cleaned = re.sub(r"\s+", " ", cleaned)

        return cleaned

    def extract_capability_control_mappings(self, capabilities_df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract capability-control mappings from the capabilities data.

        Args:
            capabilities_df: DataFrame containing capabilities with controls column

        Returns:
            DataFrame containing capability-control mappings
        """
        mappings = []

        for _, row in capabilities_df.iterrows():
            capability_id = row["capability_id"]
            controls_str = row.get("controls", "")

            if controls_str and controls_str.strip():
                # Parse comma-separated control IDs
                control_ids = [ctrl.strip() for ctrl in controls_str.split(",") if ctrl.strip()]

                for control_id in control_ids:
                    # Clean and normalize control ID
                    clean_control_id = self._normalize_control_id(control_id)
                    if clean_control_id:
                        mappings.append(
                            {
                                "capability_id": capability_id,
                                "control_id": clean_control_id,
                            }
                        )

        return pd.DataFrame(mappings)

    def _normalize_control_id(self, control_id: str) -> str:
        """
        Normalize control ID to match the format used in controls table.

        Args:
            control_id: Raw control ID from capabilities

        Returns:
            Normalized control ID
        """
        if not control_id or not control_id.strip():
            return ""

        # Clean the control ID
        clean_id = control_id.strip()

        # If it doesn't start with a prefix, assume it's a control code
        if not clean_id.startswith(("C.", "CTRL.", "CONTROL.")):
            # Add C. prefix if it looks like a control code
            if re.match(r"^[A-Z]{2,6}\.\d+", clean_id):
                clean_id = f"C.{clean_id}"

        return clean_id

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        Validate extracted capability data.

        Args:
            df: DataFrame containing capability data

        Returns:
            True if data is valid

        Raises:
            ValueError: If data validation fails
        """
        if df.empty:
            raise ValueError("No capability data found")

        # Check required columns
        required_columns = ["capability_id", "capability_name", "capability_type"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        # Check for empty required fields
        empty_ids = df[df["capability_id"].str.strip() == ""]
        if not empty_ids.empty:
            raise ValueError(f"Found {len(empty_ids)} rows with empty capability_id")

        empty_names = df[df["capability_name"].str.strip() == ""]
        if not empty_names.empty:
            raise ValueError(f"Found {len(empty_names)} rows with empty capability_name")

        # Check for duplicate IDs
        duplicate_ids = df[df.duplicated(subset=["capability_id"], keep=False)]
        if not duplicate_ids.empty:
            raise ValueError(f"Found {len(duplicate_ids)} rows with duplicate capability_id")

        # Validate capability types
        valid_types = {"technical", "non-technical"}
        invalid_types = df[~df["capability_type"].isin(valid_types)]
        if not invalid_types.empty:
            raise ValueError(f"Found {len(invalid_types)} rows with invalid capability_type")

        logger.info("Capability data validation passed")
        return True
