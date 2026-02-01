"""
Data Processor for AI/ML Risk Management Data

Orchestrates the complete data extraction process from Excel files to SQLite database.
Handles file validation, data extraction, relationship mapping, and database population.
Supports both standard configuration-based extraction and adaptive field detection.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from config_manager import ConfigManager
from database_manager import DatabaseManager
from extractors.control_extractor import ControlExtractor
from extractors.definitions_extractor import DefinitionsExtractor
from extractors.mapping_extractor import MappingExtractor
from extractors.risk_extractor import RiskExtractor

logger = logging.getLogger(__name__)


class DataProcessor:
    """
    Main data processor for AI/ML risk management data extraction.

    Orchestrates the complete workflow from file validation through data extraction
    to database population with proper error handling and logging.
    Supports both standard configuration-based extraction and adaptive field detection.
    """

    def __init__(
        self,
        data_dir: Path,
        output_dir: Path,
        config_manager: ConfigManager,
        use_adaptive_mode: bool = False,
    ):
        """
        Initialize the data processor.

        Args:
            data_dir: Directory containing input Excel files
            output_dir: Directory for output database
            config_manager: Configuration manager instance
            use_adaptive_mode: If True, use adaptive field detection; if False, use config-based extraction
        """
        self.data_dir = data_dir
        self.output_dir = output_dir
        self.config_manager = config_manager
        self.use_adaptive_mode = use_adaptive_mode

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize database manager
        db_file = self.output_dir / self.config_manager.get_database_config()["file"]
        self.database_manager = DatabaseManager(db_file)

        # Initialize extractors
        self.risk_extractor = RiskExtractor(config_manager)
        self.control_extractor = ControlExtractor(config_manager)
        self.definitions_extractor = DefinitionsExtractor(config_manager)
        self.mapping_extractor = MappingExtractor(config_manager)

        # Data storage
        self.risks_df: Optional[pd.DataFrame] = None
        self.controls_df: Optional[pd.DataFrame] = None
        self.definitions_df: Optional[pd.DataFrame] = None
        self.risk_control_mapping_df: Optional[pd.DataFrame] = None

    def find_file_recursively(self, filename: str) -> Optional[Path]:
        """
        Find a file recursively in the project directory.

        Args:
            filename: Name of the file to find

        Returns:
            Path to the file if found, None otherwise
        """
        for file_path in self.data_dir.rglob(filename):
            if file_path.is_file():
                return file_path
        return None

    def validate_input_files(self) -> bool:
        """
        Validate that all required input files exist and are accessible.

        Returns:
            True if all files are valid

        Raises:
            FileNotFoundError: If required files are missing
        """
        logger.info("Validating input files")

        config = self.config_manager.load_config()
        data_sources = config.get("data_sources", {})

        # Check if we're in test mode
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        missing_files = []

        for source_name, source_config in data_sources.items():
            filename = source_config.get("file")
            if not filename:
                missing_files.append(f"{source_name} (no file specified)")
                logger.error(f"Missing file specification for {source_name}")
                continue

            # In test mode, look for test files instead
            if test_mode:
                test_filename = f"test_{source_name}.xlsx"
                file_path = self.data_dir / "test_data" / "basic" / test_filename
                if not file_path.exists():
                    missing_files.append(test_filename)
                    logger.error(f"Missing test {source_name} file: {test_filename}")
                    continue
            else:
                # Try direct path first
                file_path = self.data_dir / filename
                if not file_path.exists():
                    # Try recursive search
                    file_path = self.find_file_recursively(filename)
                    if file_path is None:
                        missing_files.append(filename)
                        logger.error(f"Missing {source_name} file: {filename}")
                        continue

            logger.info(f"Found {source_name} file: {file_path}")

        if missing_files:
            raise FileNotFoundError(f"Missing required files: {', '.join(missing_files)}")

        logger.info("All input files validated successfully")
        return True

    def extract_data(self) -> None:
        """
        Extract data from all Excel files using the selected extraction mode.
        """
        logger.info("Starting data extraction from Excel files")

        config = self.config_manager.load_config()
        data_sources = config.get("data_sources", {})

        # Extract each data type
        self.risks_df = self._extract_data_type(data_sources, "risks", "risk")
        self.controls_df = self._extract_data_type(data_sources, "controls", "control")
        self.definitions_df = self._extract_data_type(data_sources, "definitions", "definition")

        # Extract mappings
        self._extract_mappings()

        logger.info("Data extraction completed")

    def _extract_data_type(
        self, data_sources: Dict[str, Any], source_key: str, entity_type: str
    ) -> Optional[pd.DataFrame]:
        """
        Extract data for a specific data type.

        Args:
            data_sources: Configuration for all data sources
            source_key: Key in data_sources for this data type
            entity_type: Type of entity (risk, control, definition)

        Returns:
            DataFrame containing extracted data or None if not configured
        """
        if source_key not in data_sources:
            logger.info(f"No {source_key} configuration found, skipping {source_key} extraction")
            return None

        config = data_sources[source_key]
        filename = config.get("file")
        if not filename:
            logger.error(f"No file specified for {source_key} in configuration")
            return None

        file_path = self._resolve_file_path(filename, source_key)
        if not file_path:
            logger.error(f"{source_key.title()} file not found: {filename}")
            return None

        logger.info(f"Extracting {source_key} from {file_path}")
        if self.use_adaptive_mode:
            return self.extract_data_adaptive(file_path, entity_type)
        else:
            return self._extract_with_standard_extractor(file_path, entity_type)

    def _resolve_file_path(self, filename: str, source_key: str) -> Optional[Path]:
        """
        Resolve the file path for a given filename and source key.

        Args:
            filename: Name of the file to find
            source_key: Key identifying the data source

        Returns:
            Path to the file if found, None otherwise
        """
        test_mode = os.getenv("TEST_MODE", "false").lower() == "true"

        if test_mode:
            test_filename = f"test_{source_key}.xlsx"
            file_path = self.data_dir / "test_data" / "basic" / test_filename
            if file_path.exists():
                return file_path
        else:
            # Try direct path first
            file_path = self.data_dir / filename
            if file_path.exists():
                return file_path

            # Try recursive search
            file_path = self.find_file_recursively(filename)
            if file_path:
                return file_path

        return None

    def _extract_with_standard_extractor(self, file_path: Path, entity_type: str) -> pd.DataFrame:
        """
        Extract data using the appropriate standard extractor.

        Args:
            file_path: Path to the Excel file
            entity_type: Type of entity (risk, control, definition)

        Returns:
            DataFrame containing extracted data
        """
        if entity_type == "risk":
            return self.risk_extractor.extract(file_path)
        elif entity_type == "control":
            return self.control_extractor.extract(file_path)
        elif entity_type == "definition":
            return self.definitions_extractor.extract_definitions(file_path)
        else:
            raise ValueError(f"Unknown entity type: {entity_type}")

    def _extract_mappings(self) -> None:
        """Extract relationship mappings between data types."""
        logger.info("Extracting relationship mappings")

        # Create risk-control mappings
        if self.risks_df is not None and self.controls_df is not None:
            self.risk_control_mapping_df = self.mapping_extractor.create_risk_control_mappings(
                self.risks_df, self.controls_df
            )

    def extract_data_adaptive(self, excel_path: Path, entity_type: str) -> pd.DataFrame:
        """
        Extract data using adaptive field detection.

        Args:
            excel_path: Path to the Excel file
            entity_type: Type of entity (risk, control, definition)

        Returns:
            DataFrame containing extracted data
        """
        logger.info(f"Extracting {entity_type} data using adaptive mode from {excel_path}")

        try:
            # For now, use standard extractors but with enhanced file finding
            # This preserves the adaptive file discovery while using proven extraction logic
            if entity_type == "risk":
                return self.risk_extractor.extract(excel_path)
            elif entity_type == "control":
                return self.control_extractor.extract(excel_path)
            elif entity_type == "definition":
                return self.definitions_extractor.extract_definitions(excel_path)
            else:
                raise ValueError(f"Unknown entity type: {entity_type}")

        except Exception as e:
            logger.error(f"Error extracting {entity_type} data from {excel_path}: {e}")
            raise

    def populate_database(self) -> None:
        """
        Populate the SQLite database with extracted data.
        """
        logger.info("Populating database with extracted data")

        # Create database schema
        self.database_manager.create_tables()
        self.database_manager.migrate_database()

        # Get file modification times for timestamps
        config = self.config_manager.load_config()
        data_sources = config.get("data_sources", {})

        risk_timestamp = self._get_file_timestamp(self.data_dir / data_sources["risks"]["file"])

        # Insert data with timestamps
        self.database_manager.insert_data("risks", self.risks_df, risk_timestamp)

        # Insert controls data if available
        if "controls" in data_sources and self.controls_df is not None:
            control_timestamp = self._get_file_timestamp(self.data_dir / data_sources["controls"]["file"])
            self.database_manager.insert_data("controls", self.controls_df, control_timestamp)

        # Insert definitions data if available
        if "definitions" in data_sources and self.definitions_df is not None:
            definition_timestamp = self._get_file_timestamp(self.data_dir / data_sources["definitions"]["file"])
            self.database_manager.insert_data("definitions", self.definitions_df, definition_timestamp)

        # Insert mappings data if available
        if self.risk_control_mapping_df is not None:
            self.database_manager.insert_data("risk_control_mapping", self.risk_control_mapping_df)

        # Store file metadata if enabled
        output_config = self.config_manager.get_output_config()
        if output_config.get("collect_metadata", True):
            self._store_file_metadata(data_sources)

        logger.info("Database population completed")

    def _get_file_timestamp(self, file_path: Path) -> str:
        """
        Get file modification timestamp as formatted string.

        Args:
            file_path: Path to the file

        Returns:
            Formatted timestamp string
        """
        try:
            mtime = os.path.getmtime(file_path)
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Could not get timestamp for {file_path}: {e}")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _store_file_metadata(self, data_sources: Dict[str, Any]) -> None:
        """
        Store file metadata in the database.

        Args:
            data_sources: Data sources configuration
        """
        logger.info("Storing file metadata")

        for source_name, source_config in data_sources.items():
            file_path = self.data_dir / source_config["file"]
            metadata = self._collect_file_metadata(file_path, source_name)
            self.database_manager.insert_file_metadata(**metadata)

    def _collect_file_metadata(self, file_path: Path, data_type: str) -> Dict[str, Any]:
        """
        Collect comprehensive file metadata.

        Args:
            file_path: Path to the file
            data_type: Type of data (risks, controls, definitions)

        Returns:
            Dictionary containing file metadata
        """
        import re

        metadata = {
            "data_type": data_type,
            "filename": file_path.name,
            "file_exists": file_path.exists(),
            "file_size": None,
            "file_modified_time": None,
            "version": "unknown",
        }

        if file_path.exists():
            try:
                # Get file size
                metadata["file_size"] = file_path.stat().st_size

                # Get modification time
                mtime = os.path.getmtime(file_path)
                dt = datetime.fromtimestamp(mtime)
                metadata["file_modified_time"] = dt.strftime("%Y-%m-%d %H:%M:%S")

                # Extract version from filename
                version_match = re.search(
                    r"_V(\d+(?:[._]\d+)*)\.xlsx$|_v(\d+(?:[._]\d+)*)\.xlsx$",
                    file_path.name,
                    re.IGNORECASE,
                )
                if version_match:
                    version_num = version_match.group(1) or version_match.group(2)
                    version_num = version_num.replace("_", ".")
                    metadata["version"] = f"v{version_num}"

            except Exception as e:
                logger.warning(f"Could not collect metadata for {file_path}: {e}")
        else:
            logger.warning(f"File not found: {file_path}")

        return metadata

    def process_data(self) -> None:
        """
        Run the complete data processing workflow.

        Orchestrates file validation, data extraction, and database population.
        """
        logger.info("Starting complete data processing workflow")

        try:
            # Validate input files
            self.validate_input_files()

            # Extract data from Excel files
            self.extract_data()

            # Populate database
            self.populate_database()

            # Print summary if enabled
            output_config = self.config_manager.get_output_config()
            if output_config.get("print_summary", True):
                self._print_summary()

            logger.info("Data processing workflow completed successfully")

        except Exception as e:
            logger.error(f"Data processing failed: {e}")
            raise

    def _print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "=" * 50)
        print("DATA PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Processing mode: {'Adaptive' if self.use_adaptive_mode else 'Standard'}")

        if self.risks_df is not None:
            print(f"Risks extracted: {len(self.risks_df)}")
        if self.controls_df is not None:
            print(f"Controls extracted: {len(self.controls_df)}")
        if self.risk_control_mapping_df is not None:
            print(f"Risk-Control mappings: {len(self.risk_control_mapping_df)}")

        print(f"\nDatabase created at: {self.database_manager.db_path}")
        print("=" * 50)

    def get_field_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Get detected field mappings (adaptive mode only).

        Returns:
            Dictionary of field mappings by entity type
        """
        if not self.use_adaptive_mode:
            logger.warning("Field mappings only available in adaptive mode")
            return {}

        return getattr(self, "field_mappings", {}).copy()

    def switch_processing_mode(self, use_adaptive_mode: bool) -> None:
        """
        Switch between adaptive and standard processing modes.

        Args:
            use_adaptive_mode: If True, use adaptive mode; if False, use standard mode
        """
        self.use_adaptive_mode = use_adaptive_mode
        logger.info(f"Switched to {'adaptive' if use_adaptive_mode else 'standard'} processing mode")
