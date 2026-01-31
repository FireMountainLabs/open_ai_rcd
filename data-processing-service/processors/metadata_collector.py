"""
Metadata Collector

Handles collection and management of file and processing metadata.
"""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class MetadataCollector:
    """
    Collects and manages metadata for files and processing operations.

    Provides comprehensive metadata collection including file information,
    version tracking, and processing statistics.
    """

    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize the metadata collector.

        Args:
            database_manager: Database manager instance
        """
        self.database_manager = database_manager

    def collect_file_metadata(self, file_path: Path, data_type: str) -> Dict[str, Any]:
        """
        Collect comprehensive file metadata.

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
            "file_path": str(file_path),
            "directory": str(file_path.parent),
            "extension": file_path.suffix,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
                version_info = self._extract_version_from_filename(file_path.name)
                metadata.update(version_info)

                # Get additional file properties
                metadata.update(self._get_additional_file_properties(file_path))

            except Exception as e:
                logger.warning(f"Could not collect metadata for {file_path}: {e}")
                metadata["error"] = str(e)
        else:
            logger.warning(f"File not found: {file_path}")
            metadata["error"] = "File not found"

        return metadata

    def _extract_version_from_filename(self, filename: str) -> Dict[str, Any]:
        """
        Extract version information from filename.

        Args:
            filename: Name of the file

        Returns:
            Dictionary containing version information
        """
        version_info = {
            "version": "unknown",
            "version_number": None,
            "version_major": None,
            "version_minor": None,
            "version_patch": None,
        }

        # Try different version patterns
        patterns = [
            r"_V(\d+(?:[._]\d+)*)\.xlsx$",  # _V1.0.xlsx, _V1_0.xlsx
            r"_v(\d+(?:[._]\d+)*)\.xlsx$",  # _v1.0.xlsx, _v1_0.xlsx
            r"_(\d+(?:[._]\d+)*)\.xlsx$",  # _1.0.xlsx, _1_0.xlsx
            r"V(\d+(?:[._]\d+)*)\.xlsx$",  # V1.0.xlsx, V1_0.xlsx
            r"v(\d+(?:[._]\d+)*)\.xlsx$",  # v1.0.xlsx, v1_0.xlsx
        ]

        for pattern in patterns:
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                version_str = match.group(1)
                version_str = version_str.replace("_", ".")
                version_info["version"] = f"v{version_str}"
                version_info["version_number"] = version_str

                # Parse version components
                version_parts = version_str.split(".")
                if len(version_parts) >= 1:
                    version_info["version_major"] = int(version_parts[0])
                if len(version_parts) >= 2:
                    version_info["version_minor"] = int(version_parts[1])
                if len(version_parts) >= 3:
                    version_info["version_patch"] = int(version_parts[2])

                break

        return version_info

    def _get_additional_file_properties(self, file_path: Path) -> Dict[str, Any]:
        """
        Get additional file properties.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing additional file properties
        """
        properties = {}

        try:
            stat = file_path.stat()
            properties.update(
                {
                    "file_created_time": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                    "file_accessed_time": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
                    "file_permissions": oct(stat.st_mode)[-3:],
                    "file_owner_id": stat.st_uid,
                    "file_group_id": stat.st_gid,
                }
            )
        except Exception as e:
            logger.warning(f"Could not get additional properties for {file_path}: {e}")
            properties["properties_error"] = str(e)

        return properties

    def collect_processing_metadata(
        self,
        risks_count: int,
        controls_count: int,
        questions_count: int,
        mappings_count: int,
    ) -> Dict[str, Any]:
        """
        Collect processing operation metadata.

        Args:
            risks_count: Number of risks processed
            controls_count: Number of controls processed
            questions_count: Number of questions processed
            mappings_count: Number of mappings created

        Returns:
            Dictionary containing processing metadata
        """
        metadata = {
            "processing_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "processing_timestamp": datetime.now().isoformat(),
            "total_risks": risks_count,
            "total_controls": controls_count,
            "total_questions": questions_count,
            "total_mappings": mappings_count,
            "total_records": risks_count + controls_count + questions_count,
            "processing_status": "completed",
            "processing_duration": None,  # Would be set by caller
            "processing_mode": "unknown",  # Would be set by caller
        }

        return metadata

    def store_file_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Store file metadata in the database.

        Args:
            metadata: File metadata dictionary
        """
        try:
            self.database_manager.insert_file_metadata(
                data_type=metadata["data_type"],
                filename=metadata["filename"],
                file_exists=metadata["file_exists"],
                file_size=metadata.get("file_size"),
                file_modified_time=metadata.get("file_modified_time"),
                version=metadata.get("version", "unknown"),
            )
            logger.info(f"File metadata stored for {metadata['filename']}")
        except Exception as e:
            logger.error(f"Error storing file metadata: {e}")
            raise

    def store_processing_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Store processing metadata in the database.

        Args:
            metadata: Processing metadata dictionary
        """
        try:
            self.database_manager.insert_processing_metadata(
                data_version=metadata.get("data_version", "unknown"),
                total_risks=metadata["total_risks"],
                total_controls=metadata["total_controls"],
                total_questions=metadata["total_questions"],
                total_risk_control_mappings=metadata.get("total_risk_control_mappings", 0),
                total_question_risk_mappings=metadata.get("total_question_risk_mappings", 0),
                total_question_control_mappings=metadata.get("total_question_control_mappings", 0),
                processing_status=metadata.get("processing_status", "completed"),
            )
            logger.info("Processing metadata stored successfully")
        except Exception as e:
            logger.error(f"Error storing processing metadata: {e}")
            raise

    def get_metadata_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all stored metadata.

        Returns:
            Dictionary containing metadata summary
        """
        try:
            conn = self.database_manager._get_connection()
            cursor = conn.cursor()

            # Get file metadata summary
            cursor.execute("SELECT COUNT(*) FROM file_metadata")
            file_count = cursor.fetchone()[0]

            cursor.execute("SELECT data_type, COUNT(*) FROM file_metadata GROUP BY data_type")
            file_types = dict(cursor.fetchall())

            # Get processing metadata summary
            cursor.execute("SELECT COUNT(*) FROM processing_metadata")
            processing_count = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT processing_date, total_records, processing_status
                FROM processing_metadata
                ORDER BY processing_date DESC
                LIMIT 1
            """
            )
            latest_processing = cursor.fetchone()

            return {
                "file_metadata": {
                    "total_files": file_count,
                    "files_by_type": file_types,
                },
                "processing_metadata": {
                    "total_processing_runs": processing_count,
                    "latest_processing": {
                        "date": latest_processing[0] if latest_processing else None,
                        "total_records": (latest_processing[1] if latest_processing else None),
                        "status": latest_processing[2] if latest_processing else None,
                    },
                },
            }

        except Exception as e:
            logger.error(f"Error getting metadata summary: {e}")
            return {"error": str(e)}

    def cleanup_old_metadata(self, days_to_keep: int = 30) -> int:
        """
        Clean up old metadata records.

        Args:
            days_to_keep: Number of days of metadata to keep

        Returns:
            Number of records deleted
        """
        try:
            conn = self.database_manager._get_connection()
            cursor = conn.cursor()

            # Delete old file metadata
            cursor.execute(
                """
                DELETE FROM file_metadata
                WHERE created_at < datetime('now', '-{} days')
            """.format(
                    days_to_keep
                )
            )
            file_deleted = cursor.rowcount

            # Delete old processing metadata
            cursor.execute(
                """
                DELETE FROM processing_metadata
                WHERE processing_date < datetime('now', '-{} days')
            """.format(
                    days_to_keep
                )
            )
            processing_deleted = cursor.rowcount

            conn.commit()

            total_deleted = file_deleted + processing_deleted
            logger.info(f"Cleaned up {total_deleted} old metadata records")
            return total_deleted

        except Exception as e:
            logger.error(f"Error cleaning up metadata: {e}")
            return 0
