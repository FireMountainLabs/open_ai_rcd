"""
Data Processing Microservice

A containerized microservice for extracting AI/ML risk management data from Excel
files and generating a normalized SQLite database. This service is designed for
CI/CD pipelines and local development environments.
Updated: Fresh build trigger

Key Features:
- Extracts data from Excel files (risks, controls, questions)
- Generates normalized SQLite database
- Parameterized configuration via environment variables
- Comprehensive logging and error handling
- Data validation and integrity checks
- File metadata collection and versioning
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Dict

# Add the service directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

from config_manager import ConfigManager  # noqa: E402
from data_processor import DataProcessor  # noqa: E402


def setup_logging(log_level: str = "INFO") -> None:
    """
    Set up logging configuration for the microservice.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("data_processing.log"),
        ],
    )


def validate_environment() -> Dict[str, str]:
    """
    Validate required environment variables and return configuration.

    Returns:
        Dictionary containing validated configuration values

    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        "DATA_DIR": "Path to directory containing Excel files",
        "OUTPUT_DIR": "Path to directory for output database",
        "CONFIG_FILE": "Path to configuration file",
    }

    config = {}
    missing_vars = []

    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var} ({description})")
        else:
            config[var.lower()] = value

    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

    # Optional environment variables with defaults
    config["log_level"] = os.getenv("LOG_LEVEL", "INFO")
    config["validate_files"] = os.getenv("VALIDATE_FILES", "true").lower() == "true"
    config["remove_duplicates"] = os.getenv("REMOVE_DUPLICATES", "true").lower() == "true"

    return config


def main():
    """
    Main entry point for the data processing microservice.

    Processes command line arguments, validates environment, and runs data extraction.
    """
    parser = argparse.ArgumentParser(description="AI/ML Data Processing Microservice")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--data-dir", help="Path to data directory")
    parser.add_argument("--output-dir", help="Path to output directory")
    parser.add_argument("--log-level", help="Logging level", default="INFO")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate files, do not process",
    )
    parser.add_argument(
        "--resilient-mode",
        action="store_true",
        help="Use resilient field detection mode (default: true)",
    )
    parser.add_argument(
        "--standard-mode",
        action="store_true",
        help="Use standard configuration-based mode",
    )

    args = parser.parse_args()

    # Set up logging
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)

    try:
        # Validate environment and get configuration
        env_config = validate_environment()

        # Override with command line arguments if provided
        data_dir = args.data_dir or env_config["data_dir"]
        output_dir = args.output_dir or env_config["output_dir"]
        config_file = args.config or env_config["config_file"]

        logger.info("Starting Data Processing Microservice")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Config file: {config_file}")

        # Initialize configuration manager
        config_manager = ConfigManager(config_file)

        # Determine processing mode
        if args.standard_mode:
            use_resilient_mode = False
        elif args.resilient_mode:
            use_resilient_mode = True
        else:
            use_resilient_mode = os.getenv("USE_RESILIENT_MODE", "true").lower() == "true"

        logger.info(f"Using {'resilient' if use_resilient_mode else 'standard'} processing mode")

        # Initialize data processor
        processor = DataProcessor(
            data_dir=Path(data_dir),
            output_dir=Path(output_dir),
            config_manager=config_manager,
            use_adaptive_mode=use_resilient_mode,
        )

        if args.validate_only:
            # Only validate files
            logger.info("Running file validation only")
            processor.validate_input_files()
            logger.info("File validation completed successfully")
        else:
            # Run full data processing
            logger.info("Running full data processing")
            processor.process_data()
            logger.info("Data processing completed successfully")

    except Exception as e:
        logger.error(f"Data processing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
