#!/bin/bash
# Data Processing Microservice Launcher Script
# Provides easy startup for local development and testing

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DATA_DIR="${DATA_DIR:-../}"
OUTPUT_DIR="${OUTPUT_DIR:-./output}"
CONFIG_FILE="${CONFIG_FILE:-./config/default_config.yaml}"
LOG_LEVEL="${LOG_LEVEL:-INFO}"
VALIDATE_ONLY="${VALIDATE_ONLY:-false}"
PROCESSING_MODE="${PROCESSING_MODE:-resilient}"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --data-dir DIR      Data directory containing Excel files (default: ../)"
    echo "  -o, --output-dir DIR    Output directory for database (default: ./output)"
    echo "  -c, --config FILE       Configuration file (default: ./config/default_config.yaml)"
    echo "  -l, --log-level LEVEL   Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)"
    echo "  -v, --validate-only     Only validate files, do not process"
    echo "  -r, --resilient-mode    Use resilient field detection mode (default)"
    echo "  -s, --standard-mode     Use standard configuration-based mode"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  DATA_DIR                Data directory path"
    echo "  OUTPUT_DIR              Output directory path"
    echo "  CONFIG_FILE             Configuration file path"
    echo "  LOG_LEVEL               Logging level"
    echo "  VALIDATE_ONLY           Set to 'true' to only validate files"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use defaults"
    echo "  $0 -d /path/to/data -o /path/to/output"
    echo "  $0 --validate-only"
    echo "  DATA_DIR=/custom/path $0"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--data-dir)
            DATA_DIR="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -l|--log-level)
            LOG_LEVEL="$2"
            shift 2
            ;;
        -v|--validate-only)
            VALIDATE_ONLY="true"
            shift
            ;;
        -r|--resilient-mode)
            PROCESSING_MODE="resilient"
            shift
            ;;
        -s|--standard-mode)
            PROCESSING_MODE="standard"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate arguments
if [[ ! -d "$DATA_DIR" ]]; then
    print_error "Data directory does not exist: $DATA_DIR"
    exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
    print_error "Configuration file does not exist: $CONFIG_FILE"
    exit 1
fi

# Create output directory if it doesn't exist
if [[ ! -d "$OUTPUT_DIR" ]]; then
    print_status "Creating output directory: $OUTPUT_DIR"
    mkdir -p "$OUTPUT_DIR"
fi

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if required Python packages are installed
print_status "Checking Python dependencies..."
if ! python3 -c "import pandas, openpyxl, yaml" 2>/dev/null; then
    print_warning "Required Python packages not found. Installing..."
    pip3 install -r requirements.txt
fi

# Set environment variables
export DATA_DIR
export OUTPUT_DIR
export CONFIG_FILE
export LOG_LEVEL
export VALIDATE_FILES=true
export REMOVE_DUPLICATES=true

# Print configuration
print_status "Starting Data Processing Microservice"
print_status "Data directory: $DATA_DIR"
print_status "Output directory: $OUTPUT_DIR"
print_status "Config file: $CONFIG_FILE"
print_status "Log level: $LOG_LEVEL"
print_status "Processing mode: $PROCESSING_MODE"
print_status "Validate only: $VALIDATE_ONLY"

# Build command
CMD="python3 app.py --data-dir \"$DATA_DIR\" --output-dir \"$OUTPUT_DIR\" --config \"$CONFIG_FILE\" --log-level \"$LOG_LEVEL\""

if [[ "$VALIDATE_ONLY" == "true" ]]; then
    CMD="$CMD --validate-only"
fi

if [[ "$PROCESSING_MODE" == "resilient" ]]; then
    CMD="$CMD --resilient-mode"
elif [[ "$PROCESSING_MODE" == "standard" ]]; then
    CMD="$CMD --standard-mode"
fi

# Run the microservice
print_status "Executing: $CMD"
echo ""

if eval $CMD; then
    print_success "Data processing completed successfully"
    exit 0
else
    print_error "Data processing failed"
    exit 1
fi
