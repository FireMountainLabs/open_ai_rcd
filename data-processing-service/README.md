# Data Processing Service

A containerized microservice for extracting AI/ML risk management data from Excel files and generating a normalized SQLite database. This service processes source documents and creates the database that powers the AI_RCD platform.

## 🎯 Overview

The Data Processing Service is responsible for:

- **Data Extraction**: Extracts data from Excel files (risks, controls, definitions)
- **Database Generation**: Creates a normalized SQLite database (`aiml_data.db`)
- **Relationship Mapping**: Builds mappings between risks and controls
- **Data Validation**: Validates file formats and data integrity
- **Metadata Collection**: Tracks file versions and processing information

**Note**: This service runs as a standalone process (not a long-running service). It's typically executed via the launcher script: `./launch_dataviewer --generate-db`

## 🏗️ Architecture

### Service Role

```
┌─────────────────────────────────────────┐
│      Source Excel Files                  │
│  source_docs/*.xlsx                     │
│  • AIML_RISK_TAXONOMY_V6.xlsx          │
│  • AIML_CONTROL_FRAMEWORK_V4.xlsx       │
│  • AI_Definitions_and_Taxonomy_V1.xlsx  │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│   Data Processing Service               │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      SQLite Database                    │
│  aiml_data.db                           │
│  • Normalized relational structure      │
│  • Risk, Control tables                 │
│  • Relationship mappings                │
│  • Metadata and versioning              │
└─────────────────────────────────────────┘
```

### Key Components

- **`app.py`**: Main entry point and CLI interface
- **`data_processor.py`**: Orchestrates the complete processing workflow
- **`database_manager.py`**: Handles all database operations and schema management
- **`extractors/`**: Specialized extractors for different data types
  - `risk_extractor.py`: Risk data extraction
  - `control_extractor.py`: Control data extraction
  - `definitions_extractor.py`: Definitions extraction
  - `mapping_extractor.py`: Relationship mapping extraction
- **`processors/`**: Processing utilities
  - `base_processor.py`: Base processor class
  - `data_validator.py`: Data validation
  - `metadata_collector.py`: Metadata collection
  - `standard_extractor.py`: Standard extraction mode
- **`utils/`**: Utility functions
  - `file_utils.py`: File operations and validation
  - `data_utils.py`: Data cleaning and normalization
  - `field_detector.py`: Adaptive field detection
  - `id_normalizer.py`: ID normalization
  - `config_reader.py`: Configuration reading
- **`config/`**: Configuration management
  - `config_manager.py`: Configuration loader and validator
  - `default_config.yaml`: Default configuration file

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Excel files in `source_docs/` directory
- Required Python packages (installed via `requirements.txt`)

### Using the Launcher Script (Recommended)

The easiest way to generate the database is using the launcher script from the project root:

```bash
# Generate database from Excel files
./launch_dataviewer --generate-db
```

This will:
1. Validate configuration and required files
2. Process all Excel files from `source_docs/`
3. Generate `aiml_data.db` in the project root
4. Use configuration from `data-processing-service/config/default_config.yaml`

### Running Standalone

If you need to run the service directly:

```bash
cd data-processing-service

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATA_DIR="../source_docs"
export OUTPUT_DIR="../"
export CONFIG_FILE="./config/default_config.yaml"

# Run the service
python app.py
```

### Using the Start Script

The service includes a convenient launcher script:

```bash
cd data-processing-service

# Basic usage (uses defaults)
./start.sh

# Custom directories
./start.sh -d /path/to/data -o /path/to/output

# Validate files only (no processing)
./start.sh --validate-only

# Custom configuration
./start.sh -c custom_config.yaml -l DEBUG
```

## ⚙️ Configuration

### Configuration File

The service uses YAML configuration files. The main configuration is in `config/default_config.yaml`.

#### Data Sources Configuration

Each data source is configured with file paths and column mappings:

```yaml
data_sources:
  risks:
    file: "source_docs/AIML_RISK_TAXONOMY_V6.xlsx"
    description: "AI Risk Taxonomy with risk definitions and descriptions"
    columns:
      id: "ID"
      title: "Risk"
      description: "Risk Description"
    alternative_columns:
      id: ["ID", "Risk ID", "AIR"]
      title: ["Risk", "Risk Title", "Title", "Name"]
      description: ["Risk Description", "Description", "Details"]
  
  controls:
    file: "source_docs/AIML_CONTROL_FRAMEWORK_V4.xlsx"
    description: "AI Control Framework with control domains and purposes"
    columns:
      id: "Code"
      title: "Purpose"
      description: "Purpose"
    # ... alternative_columns ...
```

#### Key Configuration Options

1. **File Paths**: Specify the Excel file location relative to `DATA_DIR`
2. **Column Mappings**: Map configuration column names to Excel column headers
3. **Alternative Columns**: Provide fallback column names for schema flexibility
4. **Sheet Selection**: For multi-sheet files, specify `sheets: "all"` or a list of sheet names
5. **Processing Mode**: Choose between resilient (adaptive) or standard mode

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DATA_DIR` | Path to directory containing Excel files | - | Yes |
| `OUTPUT_DIR` | Path to directory for output database | - | Yes |
| `CONFIG_FILE` | Path to configuration file | `./config/default_config.yaml` | Yes |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `VALIDATE_FILES` | Enable file validation | `true` | No |
| `REMOVE_DUPLICATES` | Remove duplicate records | `true` | No |
| `USE_RESILIENT_MODE` | Use adaptive field detection | `true` | No |

### Processing Modes

The service supports two processing modes:

#### Resilient Mode (Default)

- **Adaptive Field Detection**: Automatically detects column names even if they don't match configuration exactly
  - The detection normalizes column names (lowercase, whitespace, separators) and matches them against patterns, so it handles variations like "Risk ID", "risk_id", "RiskID", etc.
- **Flexible Schema**: Handles variations in Excel file structure
- **Fallback Support**: Uses `alternative_columns` configuration for column matching
- **Best for**: Files with inconsistent column names or evolving schemas

Enable with: `--resilient-mode` or `USE_RESILIENT_MODE=true`

#### Standard Mode

- **Configuration-Based**: Strictly follows column mappings in configuration
- **Predictable**: Requires exact column name matches
- **Faster**: Slightly faster processing (no field detection overhead)
- **Best for**: Files with stable, well-defined schemas

Enable with: `--standard-mode` or `USE_RESILIENT_MODE=false`

## 📊 Data Sources

The service processes the following Excel files from `source_docs/`:

### Risk Taxonomy

- **File**: `AIML_RISK_TAXONOMY_V6.xlsx`
- **Content**: AI/ML risk definitions and descriptions
- **Required Columns**: ID, Risk, Risk Description
- **Configuration**: `data_sources.risks` in `default_config.yaml`

### Control Framework

- **File**: `AIML_CONTROL_FRAMEWORK_V4.xlsx`
- **Content**: AI control domains and purposes
- **Required Columns**: Code, Purpose
- **Configuration**: `data_sources.controls` in `default_config.yaml`

### AI/ML Definitions & Taxonomy

- **File**: `AI_Definitions_and_Taxonomy_V1.xlsx`
- **Content**: AI/ML terminology definitions
- **Required Columns**: Term, Definition, Category, Source
- **Configuration**: `data_sources.definitions` in `default_config.yaml`

## 📤 Output

### Database Schema

The service generates a normalized SQLite database (`aiml_data.db`) with the following structure:

#### Core Tables

- **`risks`**: Risk definitions and descriptions
  - `id`, `title`, `description`, `category`, `created_at`, `updated_at`
- **`controls`**: Control definitions and metadata
  - `id`, `title`, `description`, `domain`, `created_at`, `updated_at`
- **`definitions`**: AI/ML terminology definitions
  - `id`, `title`, `description`, `category`, `source`, `created_at`, `updated_at`

#### Relationship Tables

- **`risk_control_mapping`**: Many-to-many risk-control relationships

#### Metadata Tables

- **`file_metadata`**: File versioning and processing information
  - `filename`, `version`, `last_modified`, `file_size`, `processed_at`
- **`processing_metadata`**: Processing statistics and timestamps
  - `processing_date`, `total_risks`, `total_controls`, `status`

### Processing Logs

The service generates detailed logs:

- **Console Output**: Real-time processing status
- **Log File**: `data_processing.log` (in service directory)
- **Log Levels**: DEBUG, INFO, WARNING, ERROR

## 🛠️ Usage Examples

### Basic Processing

```bash
# Process all data with default settings (via launcher)
./launch_dataviewer --generate-db

# Process with custom directories (standalone)
python app.py --data-dir /path/to/data --output-dir /path/to/output

# Validate files only (no processing)
python app.py --validate-only
```

### Advanced Usage

```bash
# Custom configuration and logging
python app.py \
  --config custom_config.yaml \
  --data-dir /path/to/data \
  --output-dir /path/to/output \
  --log-level DEBUG

# Use standard mode (strict column matching)
python app.py --standard-mode

# Use resilient mode (adaptive field detection)
python app.py --resilient-mode

# Environment variable configuration
DATA_DIR=/data OUTPUT_DIR=/output LOG_LEVEL=DEBUG python app.py
```

### Using the Start Script

```bash
# Basic usage
./start.sh

# Custom directories
./start.sh -d /custom/data -o /custom/output

# Validate only
./start.sh --validate-only

# Standard mode
./start.sh --standard-mode

# Debug logging
./start.sh -l DEBUG
```

## 🧪 Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-test.txt
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_extractors.py
pytest tests/test_data_processor.py
pytest tests/test_database_manager.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Project Structure

```
data-processing-service/
├── app.py                    # Main entry point
├── data_processor.py         # Processing orchestrator
├── database_manager.py       # Database operations
├── requirements.txt          # Dependencies
├── requirements-test.txt      # Test dependencies
├── Dockerfile                # Container definition
├── start.sh                  # Launcher script
├── config/                   # Configuration
│   ├── config_manager.py
│   ├── default_config.yaml
│   └── test_config.yaml
├── extractors/               # Data extractors
│   ├── risk_extractor.py
│   ├── control_extractor.py
│   ├── definitions_extractor.py
│   └── mapping_extractor.py
├── processors/               # Processing utilities
│   ├── base_processor.py
│   ├── data_validator.py
│   ├── metadata_collector.py
│   └── standard_extractor.py
├── utils/                    # Utilities
│   ├── file_utils.py
│   ├── data_utils.py
│   ├── field_detector.py
│   ├── id_normalizer.py
│   └── config_reader.py
├── test_data/                # Test data files
│   └── basic/
└── tests/                    # Test suite
    ├── test_extractors.py
    ├── test_data_processor.py
    └── ...
```

### Adding New Extractors

1. Create a new extractor class in `extractors/`:
   ```python
   from processors.base_processor import BaseProcessor
   
   class MyExtractor(BaseProcessor):
       def extract(self, file_path: Path) -> pd.DataFrame:
           # Extraction logic
           pass
   ```

2. Add configuration in `default_config.yaml`:
   ```yaml
   data_sources:
     my_data:
       file: "source_docs/My_File.xlsx"
       columns:
         id: "ID"
         title: "Title"
   ```

3. Register the extractor in `data_processor.py`:
   ```python
   self.my_extractor = MyExtractor(config_manager)
   ```

4. Add extraction call in `process_data()` method

### Configuration Management

The service uses a hierarchical configuration system:

1. **Default values** in `default_config.yaml`
2. **Environment variable** overrides
3. **Command-line argument** overrides (highest priority)

## 🐳 Docker

### Building

```bash
# Build from project root
docker build -f data-processing-service/Dockerfile -t data-processing-service .

# Or from service directory
cd data-processing-service
docker build -t data-processing-service .
```

### Running

```bash
# Run container with volume mounts
docker run -v $(pwd)/source_docs:/app/data \
           -v $(pwd):/app/output \
           -e DATA_DIR=/app/data \
           -e OUTPUT_DIR=/app/output \
           -e CONFIG_FILE=/app/config/default_config.yaml \
           data-processing-service
```

### Docker Compose

The service is typically run via the launcher script, which handles Docker Compose orchestration. For manual Docker Compose usage, see the main project README.

## 🆘 Troubleshooting

### File Not Found Errors

**Problem**: Service can't find Excel files

**Solutions**:
1. Verify files exist in `source_docs/` directory:
   ```bash
   ls -la source_docs/*.xlsx
   ```

2. Check file paths in `default_config.yaml` match actual file names

3. Verify `DATA_DIR` environment variable points to correct directory:
   ```bash
   echo $DATA_DIR
   ```

4. Check file permissions:
   ```bash
   ls -l source_docs/
   ```

### Database Generation Fails

**Problem**: Database file not created or incomplete

**Solutions**:
1. Check output directory is writable:
   ```bash
   ls -ld output/
   chmod 755 output/
   ```

2. Verify disk space:
   ```bash
   df -h .
   ```

3. Check for database lock (another process using it):
   ```bash
   lsof aiml_data.db
   ```

4. Review processing logs:
   ```bash
   tail -f data_processing.log
   ```

### Configuration Errors

**Problem**: Invalid configuration or column mapping issues

**Solutions**:
1. Validate YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config/default_config.yaml'))"
   ```

2. Check column mappings match Excel file headers:
   ```bash
   # Inspect Excel file headers
   python -c "import pandas as pd; print(pd.read_excel('source_docs/AIML_RISK_TAXONOMY_V6.xlsx', nrows=0).columns.tolist())"
   ```

3. Use resilient mode for flexible column matching:
   ```bash
   python app.py --resilient-mode
   ```

4. Enable debug logging to see column detection:
   ```bash
   python app.py --log-level DEBUG
   ```

### Data Quality Issues

**Problem**: Missing or incorrect data in database

**Solutions**:
1. Enable validation:
   ```bash
   export VALIDATE_FILES=true
   python app.py
   ```

2. Check for duplicate removal issues:
   ```bash
   # Disable duplicate removal to see all records
   export REMOVE_DUPLICATES=false
   python app.py
   ```

3. Review extraction logs for warnings:
   ```bash
   grep -i warning data_processing.log
   ```

4. Validate relationships:
   ```bash
   sqlite3 aiml_data.db "SELECT COUNT(*) FROM risk_control_mapping;"
   ```

### Processing Mode Issues

**Problem**: Data not extracted correctly

**Solutions**:
1. Try switching processing modes:
   ```bash
   # If standard mode fails, try resilient
   python app.py --resilient-mode
   
   # If resilient mode fails, try standard
   python app.py --standard-mode
   ```

2. Check alternative column configuration:
   - Review `alternative_columns` in `default_config.yaml`
   - Add more alternative column names if needed

3. Enable debug logging to see field detection:
   ```bash
   python app.py --log-level DEBUG --resilient-mode
   ```

## 📝 Logging

The service provides comprehensive logging:

- **DEBUG**: Detailed processing information, field detection, column matching
- **INFO**: General processing status, file processing, record counts
- **WARNING**: Non-fatal issues, missing optional columns, data quality issues
- **ERROR**: Fatal errors that stop processing

Logs are written to:
- **Console**: Real-time output
- **File**: `data_processing.log` (in service directory)

## 🔗 Integration with Launcher

The service is designed to be used via the launcher script (`./launch_dataviewer`):

```bash
# Generate database (recommended)
./launch_dataviewer --generate-db

# The launcher:
# 1. Validates configuration and files
# 2. Sets environment variables automatically
# 3. Runs the data processing service
# 4. Copies database to project root
# 5. Provides status and error reporting
```

The launcher handles:
- Environment variable setup
- File validation
- Error handling and reporting
- Database file management

## 📚 Related Documentation

- **Main README**: `/README.md` - Overall platform documentation
- **Dashboard Service**: `/dashboard-service/README.md` - Frontend service documentation
- **Database Service**: `/database-service/README.md` - Database API service documentation
- **Test Documentation**: `/data-processing-service/tests/README.md` - Test suite documentation
- **Configuration Guide**: See `config/default_config.yaml` for detailed configuration options

## 📋 Notes

- The service is **not a long-running service** - it runs to completion and exits
- Database generation is **idempotent** - running multiple times will recreate the database
- The service supports **incremental processing** - can process individual data sources
- **File metadata** is tracked to detect changes in source files
- **Relationship mappings** are automatically extracted from Excel files
- The service uses **pandas** for Excel file processing and data manipulation
- **SQLite** is used for the output database (read-only for other services)
