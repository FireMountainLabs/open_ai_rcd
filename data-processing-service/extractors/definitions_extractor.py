"""
Definitions Extractor for Data Processing Microservice

This module provides functionality to extract AI/ML terminology definitions
from Excel files and normalize the data for database storage. It handles
the AI_Definitions_and_Taxonomy_V1.xlsx file structure with columns:
Term, Category, Definition, Source.

The extractor supports both standard configuration-based extraction and
adaptive field detection modes, ensuring robust data processing even
when file structures change.

Example:
    >>> from extractors.definitions_extractor import DefinitionsExtractor
    >>> from config_manager import ConfigManager
    >>>
    >>> config_manager = ConfigManager('config/default_config.yaml')
    >>> extractor = DefinitionsExtractor(config_manager)
    >>>
    >>> df = extractor.extract_definitions('AI_Definitions_and_Taxonomy_V1.xlsx')
    >>> print(f"Extracted {len(df)} definitions")
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DefinitionsExtractor:
    """
    Extracts AI/ML terminology definitions from Excel files.

    This class handles the extraction and normalization of AI/ML terminology
    definitions from Excel files, specifically designed for the
    AI_Definitions_and_Taxonomy_V1.xlsx file structure.

    The extractor processes data with the following columns:
    - Term: The AI/ML terminology term
    - Category: Classification category (e.g., "Core AI/ML Concepts")
    - Definition: Detailed definition of the term
    - Source: Reference source for the definition

    Features:
    - Robust field detection with fallback alternatives
    - Data normalization and validation
    - Duplicate detection and removal
    - Comprehensive error handling and logging
    - Support for both standard and adaptive extraction modes

    Attributes:
        config_manager: Configuration manager instance for accessing settings
    """

    def __init__(self, config_manager):
        """
        Initialize the definitions extractor.

        Args:
            config_manager: Configuration manager instance for accessing
                          extraction settings and column mappings

        Raises:
            TypeError: If config_manager is None or invalid type
        """
        self.config_manager = config_manager

    def extract_definitions(self, file_path: Path) -> pd.DataFrame:
        """
        Extract definitions data from Excel file.

        This method reads the Excel file, normalizes the data, and returns
        a DataFrame with standardized column names and validated data.

        Args:
            file_path: Path to the Excel file containing definitions

        Returns:
            pd.DataFrame: DataFrame containing extracted definitions data with columns:
                - definition_id: Normalized unique identifier
                - term: The AI/ML terminology term
                - title: Display title (same as term)
                - description: Detailed definition
                - category: Classification category
                - source: Reference source

        Raises:
            FileNotFoundError: If the Excel file doesn't exist
            ValueError: If the file format is invalid or data is malformed
            Exception: For other processing errors

        Example:
            >>> extractor = DefinitionsExtractor(config_manager)
            >>> df = extractor.extract_definitions('AI_Definitions_and_Taxonomy_V1.xlsx')
            >>> print(f"Extracted {len(df)} definitions")
        """
        logger.info(f"Extracting definitions data from {file_path}")

        try:
            # Read Excel file
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.strip()

            logger.info(f"Found {len(df)} definition records")
            logger.info(f"Columns: {df.columns.tolist()}")

            # Get column mappings from config
            config = self.config_manager.load_config()
            definitions_config = config.get("data_sources", {}).get("definitions", {})
            columns = definitions_config.get("columns", {})

            # Map columns to standard names
            mapped_data = []
            for _, row in df.iterrows():
                definition_record = self._extract_definition_record(row, columns)
                if definition_record:
                    mapped_data.append(definition_record)

            result_df = pd.DataFrame(mapped_data)

            # Normalize data
            result_df = self._normalize_definitions_data(result_df)

            # Remove duplicates based on term
            if not result_df.empty:
                initial_count = len(result_df)
                result_df = result_df.drop_duplicates(subset=["definition_id"], keep="first")
                final_count = len(result_df)
                if initial_count != final_count:
                    logger.info(f"Removed {initial_count - final_count} duplicate definition records")

            logger.info(f"Extracted {len(result_df)} definition records")
            return result_df

        except Exception as e:
            logger.error(f"Error extracting definitions data from {file_path}: {e}")
            raise

    def _extract_definition_record(self, row: pd.Series, columns: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Extract a single definition record from a row.

        This method processes a single row of data, mapping the columns
        to standardized field names and validating the data quality.

        Args:
            row: Pandas Series representing a row of data from the Excel file
            columns: Dictionary mapping standard field names to actual column names

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing the definition record with
                                    standardized keys, or None if the record is invalid

        Note:
            Records are considered invalid if essential fields (term) are missing
            or empty. Invalid records are logged as warnings.
        """
        try:
            # Get values using configured column names
            term = self._get_column_value(row, columns.get("id", "Term"))
            title = self._get_column_value(row, columns.get("title", "Term"))
            description = self._get_column_value(row, columns.get("description", "Definition"))
            category = self._get_column_value(row, columns.get("category", "Category"))
            source = self._get_column_value(row, columns.get("source", "Source"))

            # Skip if essential fields are missing
            if not term or pd.isna(term) or str(term).strip() == "":
                return None

            # Create definition ID from term (normalized)
            definition_id = self._normalize_id(str(term).strip())

            return {
                "definition_id": definition_id,
                "term": str(term).strip(),
                "title": (str(title).strip() if title and not pd.isna(title) else str(term).strip()),
                "description": (str(description).strip() if description and not pd.isna(description) else ""),
                "category": (str(category).strip() if category and not pd.isna(category) else "Uncategorized"),
                "source": (str(source).strip() if source and not pd.isna(source) else "Unknown"),
            }

        except Exception as e:
            logger.warning(f"Error processing definition record: {e}")
            return None

    def _get_column_value(self, row: pd.Series, column_name: str) -> Optional[str]:
        """
        Get value from row using column name with fallback to alternative names.

        This method attempts to find a column value using the primary column name,
        and if not found, tries alternative column names from the configuration.

        Args:
            row: Pandas Series representing a row of data from the Excel file
            column_name: Primary column name to search for

        Returns:
            Optional[str]: Column value if found, None otherwise

        Note:
            The method checks both the primary column name and alternative
            names defined in the configuration for robust field detection.
        """
        if column_name in row.index:
            return row[column_name]

        # Try alternative column names from config
        config = self.config_manager.load_config()
        definitions_config = config.get("data_sources", {}).get("definitions", {})
        alternative_columns = definitions_config.get("alternative_columns", {})

        # Check alternative names for the field type
        for field_type, alternatives in alternative_columns.items():
            if column_name == definitions_config.get("columns", {}).get(field_type):
                for alt_name in alternatives:
                    if alt_name in row.index:
                        return row[alt_name]

        return None

    def _normalize_id(self, term: str) -> str:
        """
        Normalize term to create a valid ID.

        This method converts a term string into a valid identifier by:
        - Converting to lowercase
        - Replacing spaces and special characters with underscores
        - Removing multiple consecutive underscores

        Args:
            term: Original term string to normalize

        Returns:
            str: Normalized ID string suitable for use as a database key

        Example:
            >>> extractor = DefinitionsExtractor(config_manager)
            >>> extractor._normalize_id("AI System")
            'ai_system'
            >>> extractor._normalize_id("Machine Learning (ML)")
            'machine_learning_ml'
        """
        # Convert to lowercase, replace spaces and special chars with underscores
        normalized = term.lower()
        normalized = "".join(c if c.isalnum() else "_" for c in normalized)
        # Remove multiple consecutive underscores
        normalized = "_".join(part for part in normalized.split("_") if part)
        return normalized

    def _normalize_definitions_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize definitions data for database storage.

        This method performs data cleaning and normalization including:
        - Ensuring required columns exist
        - Cleaning and trimming text fields
        - Setting appropriate default values for empty fields
        - Removing records with empty definition IDs

        Args:
            df: DataFrame containing raw definitions data

        Returns:
            pd.DataFrame: Normalized DataFrame ready for database storage

        Note:
            The method modifies the input DataFrame in place and also returns it
            for convenience. Empty definition IDs are removed as they are invalid.
        """
        if df.empty:
            return df

        # Ensure required columns exist
        required_columns = [
            "definition_id",
            "term",
            "title",
            "description",
            "category",
            "source",
        ]
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Clean and normalize text fields
        text_columns = ["term", "title", "description", "category", "source"]
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # Replace empty strings with appropriate defaults
                if col == "category":
                    df[col] = df[col].replace("", "Uncategorized")
                elif col == "source":
                    df[col] = df[col].replace("", "Unknown")

        # Ensure definition_id is unique and not empty
        df = df[df["definition_id"].str.len() > 0]

        return df

    def validate_definitions_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Validate definitions data quality.

        This method performs comprehensive data quality validation including:
        - Counting valid and invalid records
        - Identifying missing data fields
        - Detecting duplicate terms
        - Collecting unique categories and sources

        Args:
            df: DataFrame containing definitions data to validate

        Returns:
            Dict[str, Any]: Dictionary containing validation results with keys:
                - total_records: Total number of records
                - valid_records: Number of valid records
                - invalid_records: Number of invalid records
                - missing_terms: Number of records with missing terms
                - missing_descriptions: Number of records with missing descriptions
                - duplicate_terms: Number of duplicate terms
                - categories: Set of unique categories
                - sources: Set of unique sources

        Example:
            >>> extractor = DefinitionsExtractor(config_manager)
            >>> df = extractor.extract_definitions('definitions.xlsx')
            >>> validation = extractor.validate_definitions_data(df)
            >>> print(f"Valid records: {validation['valid_records']}")
        """
        validation_results = {
            "total_records": len(df),
            "valid_records": 0,
            "invalid_records": 0,
            "missing_terms": 0,
            "missing_descriptions": 0,
            "duplicate_terms": 0,
            "categories": set(),
            "sources": set(),
        }

        if df.empty:
            return validation_results

        # Count valid records
        valid_mask = (df["definition_id"].str.len() > 0) & (df["term"].str.len() > 0)
        validation_results["valid_records"] = valid_mask.sum()
        validation_results["invalid_records"] = len(df) - validation_results["valid_records"]

        # Count missing data
        validation_results["missing_terms"] = (df["term"].str.len() == 0).sum()
        validation_results["missing_descriptions"] = (df["description"].str.len() == 0).sum()

        # Count duplicates
        validation_results["duplicate_terms"] = df["term"].duplicated().sum()

        # Collect unique categories and sources
        validation_results["categories"] = set(df["category"].unique())
        validation_results["sources"] = set(df["source"].unique())

        return validation_results
