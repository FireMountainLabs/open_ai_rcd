"""
Reporting utility functions for the AIML data collector.

This module provides utilities for generating reports, summaries,
and formatted output for the data extraction process.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ReportingUtils:
    """
    Utility class for generating reports and summaries.

    This class provides methods for creating formatted output,
    progress reports, and extraction summaries.
    """

    @staticmethod
    def print_section_header(title: str, width: int = 60) -> None:
        """
        Print a formatted section header.

        Args:
            title: Title of the section
            width: Width of the header line
        """
        print("\n" + "=" * width)
        print(title.upper())
        print("=" * width)

    @staticmethod
    def print_data_sources_config(config: Dict[str, Any]) -> None:
        """
        Print data sources configuration in a formatted way.

        Args:
            config: Configuration dictionary containing data sources
        """
        ReportingUtils.print_section_header("DATA SOURCES CONFIGURATION")

        data_sources = config.get("data_sources", {})

        for source_name, source_config in data_sources.items():
            print(f"\n{source_name.upper()}:")
            print(f"  File: {source_config.get('file', 'N/A')}")
            print(f"  Description: {source_config.get('description', 'N/A')}")

            # Print column mappings
            columns = source_config.get("columns", {})
            if columns:
                print("  Column Mappings:")
                for col_key, col_value in columns.items():
                    print(f"    {col_key}: {col_value}")

            # Print sheets info if available
            if "sheets" in source_config:
                print(f"  Sheets: {source_config['sheets']}")

        # Print database configuration
        database_config = config.get("database", {})
        if database_config:
            print("\nDATABASE:")
            print(f"  File: {database_config.get('file', 'N/A')}")
            print(f"  Description: {database_config.get('description', 'N/A')}")

        print("=" * 60)

    @staticmethod
    def print_extraction_summary(extraction_results: Dict[str, Any]) -> None:
        """
        Print extraction summary in a formatted way.

        Args:
            extraction_results: Dictionary containing extraction results
        """
        ReportingUtils.print_section_header("DATA EXTRACTION SUMMARY")

        # Print record counts
        if "risks" in extraction_results:
            print(f"Risks extracted: {extraction_results['risks']}")
        if "controls" in extraction_results:
            print(f"Controls extracted: {extraction_results['controls']}")
        if "questions" in extraction_results:
            print(f"Questions extracted: {extraction_results['questions']}")
        if "risk_control_mappings" in extraction_results:
            print(f"Risk-Control mappings: {extraction_results['risk_control_mappings']}")
        if "question_risk_mappings" in extraction_results:
            print(f"Question-Risk mappings: " f"{extraction_results['question_risk_mappings']}")
        if "question_control_mappings" in extraction_results:
            print(f"Question-Control mappings: " f"{extraction_results['question_control_mappings']}")

        # Print database info
        if "database_path" in extraction_results:
            print(f"\nDatabase created at: {extraction_results['database_path']}")

        print("=" * 50)

    @staticmethod
    def print_progress_update(step: str, status: str = "INFO") -> None:
        """
        Print a progress update message.

        Args:
            step: Description of the current step
            status: Status level (INFO, SUCCESS, WARNING, ERROR)
        """
        status_symbols = {"INFO": "🔄", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌"}

        symbol = status_symbols.get(status, "🔄")
        print(f"{symbol} {step}")

    @staticmethod
    def print_validation_results(validation_results: Dict[str, Any]) -> None:
        """
        Print data validation results in a formatted way.

        Args:
            validation_results: Dictionary containing validation results
        """
        ReportingUtils.print_section_header("DATA VALIDATION RESULTS")

        for entity_type, results in validation_results.items():
            print(f"\n{entity_type.upper()}:")

            if "validation_passed" in results:
                status = "✅ PASSED" if results["validation_passed"] else "❌ FAILED"
                print(f"  Validation: {status}")

            if "total_records" in results:
                print(f"  Total Records: {results['total_records']}")

            if "valid_records" in results:
                print(f"  Valid Records: {results['valid_records']}")

            if "invalid_records" in results:
                print(f"  Invalid Records: {results['invalid_records']}")

            if "data_quality_score" in results:
                print(f"  Data Quality Score: {results['data_quality_score']}%")

        print("=" * 50)

    @staticmethod
    def print_file_metadata(metadata_list: List[Dict[str, Any]]) -> None:
        """
        Print file metadata in a formatted way.

        Args:
            metadata_list: List of file metadata dictionaries
        """
        ReportingUtils.print_section_header("FILE METADATA")

        for metadata in metadata_list:
            print(f"\n{metadata['data_type'].upper()}:")
            print(f"  Filename: {metadata['filename']}")
            print(f"  Exists: {metadata['file_exists']}")

            if metadata["file_size"] is not None:
                size_mb = metadata["file_size"] / (1024 * 1024)
                print(f"  Size: {size_mb:.2f} MB")

            if metadata["file_modified_time"]:
                print(f"  Modified: {metadata['file_modified_time']}")

            if metadata["version"] != "unknown":
                print(f"  Version: {metadata['version']}")

        print("=" * 50)

    @staticmethod
    def create_summary_report(extraction_results: Dict[str, Any]) -> str:
        """
        Create a text summary report of the extraction process.

        Args:
            extraction_results: Dictionary containing extraction results

        Returns:
            Formatted text report
        """
        report_lines = []
        report_lines.append("AIML Data Extraction Summary Report")
        report_lines.append("=" * 50)
        report_lines.append("")

        # Add extraction statistics
        if "risks" in extraction_results:
            report_lines.append(f"Risks extracted: {extraction_results['risks']}")
        if "controls" in extraction_results:
            report_lines.append(f"Controls extracted: {extraction_results['controls']}")
        if "questions" in extraction_results:
            report_lines.append(f"Questions extracted: {extraction_results['questions']}")

        # Add mapping statistics
        if "risk_control_mappings" in extraction_results:
            report_lines.append(f"Risk-Control mappings: {extraction_results['risk_control_mappings']}")
        if "question_risk_mappings" in extraction_results:
            report_lines.append(f"Question-Risk mappings: " f"{extraction_results['question_risk_mappings']}")
        if "question_control_mappings" in extraction_results:
            report_lines.append(f"Question-Control mappings: " f"{extraction_results['question_control_mappings']}")

        report_lines.append("")
        report_lines.append("Extraction completed successfully!")

        return "\n".join(report_lines)
