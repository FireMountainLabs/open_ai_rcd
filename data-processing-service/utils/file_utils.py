"""
File utility functions for the AIML data collector.

This module provides utilities for file operations, metadata collection,
and file validation.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class FileUtils:
    """
    Utility class for file operations and metadata collection.

    This class provides methods for file validation, metadata extraction,
    and file modification time tracking.
    """

    @staticmethod
    def get_file_modification_time(file_path: Path) -> str:
        """
        Get the modification time of a file as a formatted string.

        Args:
            file_path: Path to the file

        Returns:
            Formatted timestamp string (YYYY-MM-DD HH:MM:SS)
        """
        try:
            # Get file modification time
            mtime = os.path.getmtime(file_path)
            # Convert to datetime and format
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception as e:
            logger.warning(f"Could not get modification time for {file_path}: {e}")
            # Return current time as fallback
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def collect_file_metadata(file_path: Path, data_type: str) -> Dict[str, Any]:
        """
        Collect comprehensive file metadata for storage in database.

        Args:
            file_path: Path to the file
            data_type: Type of data (risks, controls, questions)

        Returns:
            Dictionary containing file metadata
        """
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
                version = FileUtils.extract_version_from_filename(file_path.name)
                if version:
                    metadata["version"] = version

            except Exception as e:
                logger.warning(f"Could not collect metadata for {file_path}: {e}")
        else:
            logger.warning(f"File not found: {file_path}")

        return metadata

    @staticmethod
    def extract_version_from_filename(filename: str) -> Optional[str]:
        """
        Extract version number from filename using regex patterns.

        Args:
            filename: Name of the file to extract version from

        Returns:
            Version string (e.g., "v6.1") or None if not found
        """
        # Common version patterns in filenames
        version_patterns = [
            # _V6.1.xlsx, _V6_1.xlsx, _V6_1_2.xlsx, _V4.xlsx
            r"_V(\d+(?:[._]\d+)*)\.xlsx$",
            r"_v(\d+(?:[._]\d+)*)\.xlsx$",  # _v0.xlsx, _v0_1.xlsx, _v0_1_2.xlsx
            # _version_6.1.xlsx, _version_6_1.xlsx, _version_6_1_2.xlsx
            r"_version_(\d+(?:[._]\d+)*)\.xlsx$",
            r"v(\d+(?:[._]\d+)*)\.xlsx$",  # v6.1.xlsx, v6_1.xlsx, v6_1_2.xlsx
        ]

        for pattern in version_patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                version_num = match.group(1)
                # Normalize underscores to dots for consistency
                version_num = version_num.replace("_", ".")
                return f"v{version_num}"

        return None

    @staticmethod
    def validate_file_exists(file_path: Path, file_type: str) -> bool:
        """
        Validate that a file exists and log appropriate messages.

        Args:
            file_path: Path to the file to validate
            file_type: Type of file for logging purposes

        Returns:
            True if file exists, False otherwise
        """
        if file_path.exists():
            logger.info(f"{file_type} file found: {file_path}")
            return True
        else:
            logger.error(f"{file_type} file not found: {file_path}")
            return False

    @staticmethod
    def get_file_size_mb(file_path: Path) -> float:
        """
        Get file size in megabytes.

        Args:
            file_path: Path to the file

        Returns:
            File size in megabytes, or 0.0 if file doesn't exist
        """
        try:
            if file_path.exists():
                size_bytes = file_path.stat().st_size
                return round(size_bytes / (1024 * 1024), 2)
            return 0.0
        except Exception as e:
            logger.warning(f"Could not get file size for {file_path}: {e}")
            return 0.0

    @staticmethod
    def is_excel_file(file_path: Path) -> bool:
        """
        Check if a file is an Excel file based on extension.

        Args:
            file_path: Path to the file to check

        Returns:
            True if file has Excel extension, False otherwise
        """
        excel_extensions = [".xlsx", ".xls", ".xlsm"]
        return file_path.suffix.lower() in excel_extensions
