# Open AI Risk, Controls & Definitions (Open AI RCD)

An open-source AI/ML risk management platform featuring:

- **100+ AI Risks** - Comprehensive taxonomy covering model, data, operational, and governance risks
- **150+ Controls** - Organized across 10 domains (AI Governance, Data Management, Model Development, Security, etc.)
- **400+ Definitions** - Standardized AI/ML terminology and concepts

Built as a microservices architecture with an interactive dashboard for exploring risk-control relationships, coverage analysis, and gap identification.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for database generation)
- 2GB+ available RAM
- Ports 5001 and 5002 available

### Quickstart Deploy

```bash
# 1. Clone the repository and navigate into it
git clone <repository-url>
cd AI_RCD

# 2. Build the Docker images
docker compose build

# 3. Generate the initial database from Excel source docs
docker compose run --rm data-processing-service

# 4. Launch the platform
docker compose up -d
```

The dashboard will be available at [http://localhost:5002](http://localhost:5002) once services are healthy.

## 🏗️ Architecture

### Overview

The platform is built as a microservices architecture with three core services working together:

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                             │
│                  http://localhost:5002                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Dashboard Service (Port 5002)                  │
│  • Flask web application                                     │
│  • Frontend UI and visualization                            │
│  • Proxies API requests to Database Service                 │
│  • Serves static assets and templates                       │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP REST API
                       │ (via Docker network)
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Database Service (Port 5001)                   │
│  • FastAPI REST API                                          │
│  • SQLite database access                                    │
│  • Data querying and relationships                           │
│  • Data relationship management                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    SQLite Database                          │
│              aiml_data.db (read-only)                       │
│  • Risks, Controls, Definitions                          │
│  • Relationship mappings                                     │
│  • Metadata and processing information                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Data Processing Service (Standalone)                 │
│  • Excel file extraction and processing                     │
│  • Database generation from source_docs/                    │
│  • Runs via docker compose: docker compose run ...          │
│  • Outputs: aiml_data.db                                    │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

#### Dashboard Service
- **Technology**: Flask (Python)
- **Port**: 5002
- **Purpose**: Frontend web interface
- **Responsibilities**:
  - Serves HTML/CSS/JavaScript to browsers
  - Proxies API requests to Database Service
  - Handles user interactions and visualization
- **Dependencies**: Database Service (must be healthy before starting)

#### Database Service
- **Technology**: FastAPI (Python)
- **Port**: 5001
- **Purpose**: Data access layer
- **Responsibilities**:
  - Provides REST API endpoints for all data
  - Manages SQLite database connections
  - Handles queries, searches, and relationships
- **Dependencies**: SQLite database file (`aiml_data.db`)

#### Data Processing Service
- **Technology**: Python (standalone script)
- **Purpose**: Data extraction and transformation
- **Responsibilities**:
  - Reads Excel files from `source_docs/`
  - Processes data according to `default_config.yaml`
  - Generates normalized SQLite database
  - Validates and cleans data
- **Execution**: Run via `docker compose run --rm data-processing-service` (not a running service)

### Data Flow

1. **Database Generation** (One-time or on-demand):
   ```
   source_docs/*.xlsx → Data Processing Service → aiml_data.db
   ```

2. **User Request Flow**:
   ```
   Browser → Dashboard Service → Database Service → SQLite DB
                ↓
           (Response with UI)
   ```

3. **API Request Flow**:
   ```
   Browser → Dashboard Service (/api/*) → Database Service → SQLite DB
                ↓
           (JSON Response)
   ```

### Network Architecture

- **Docker Network**: `aiml-network` (bridge driver)
- **Service Communication**: Internal Docker network (service names as hostnames)
- **External Access**: Port mappings to host machine
- **Health Checks**: All services have health check endpoints

### Storage

- **Database Volume**: `./aiml_data.db` mounted as read-only to Database Service
- **Source Files**: `./source_docs/` (local filesystem, accessed by Data Processing Service)

## 📊 Service Ports

| Service             | Port | Purpose                   |
| ------------------- | ---- | ------------------------- |
| **Dashboard** | 5002 | Main UI and visualization |
| **Database**  | 5001 | Data API                  |

## 🛠️ Launcher Commands

### Primary Commands

```bash
# Launch services (default - uses local build)
docker compose up

# Generate database from Excel files only (does not start services)
docker compose run --rm data-processing-service
```

### Management Commands

```bash
# Service management
docker compose ps     # Show service status
docker compose logs       # View service logs
docker compose restart    # Stop and restart services
docker compose down       # Stop all services
docker compose up --health     # Check service health
```

### Database Management

# Database operations
docker compose run --rm data-processing-service   # Generate database from local Excel files
```

**Database Generation Process:**

- The `--generate-db` command processes Excel files from `source_docs/` directory
- Configuration is read from `data-processing-service/config/default_config.yaml`
- The generated database (`aiml_data.db`) is created in the project root
- Services automatically use the database when launched

## ⚙️ Configuration

### Configuring Source Documents

The platform processes Excel files from the `source_docs/` directory. The data processing service uses `data-processing-service/config/default_config.yaml` to configure how these files are processed.

#### Source Document Configuration

To configure which files are processed and how their columns are mapped, edit `data-processing-service/config/default_config.yaml`:

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
  
  definitions:
    file: "source_docs/AI_Definitions_and_Taxonomy_V1.xlsx"
    description: "AI/ML terminology definitions and taxonomy"
    columns:
      id: "Term"
      title: "Term"
      description: "Definition"
      category: "Category"
      source: "Source"
    # ... alternative_columns ...
  
  capabilities:
    file: "source_docs/AI_ML_Security_Capabilities.xlsx"
    description: "Technical and non-technical security capabilities"
    sheets: ["Technical Security Capabilities", "Non-Technical Capabilities"]
    columns:
      controls: "Controls"
      products: "Candidate Products (modern, AI-defense)"
      notes: "Notes"
    # ... alternative_columns ...
```

#### Key Configuration Options

1. **File Paths**: Update the `file` field to point to your Excel files in `source_docs/`
2. **Column Mappings**: Specify which columns contain which data using the `columns` section
3. **Alternative Columns**: Provide fallback column names in `alternative_columns` for schema flexibility
4. **Sheet Selection**: For multi-sheet files, specify `sheets: "all"` or a list of sheet names
5. **Processing Mode**: The service uses "resilient" mode by default, which auto-detects column names

#### Example: Adding a New Source Document

1. Place your Excel file in the `source_docs/` directory
2. Add a new entry to `data_sources` in `default_config.yaml`:
   ```yaml
   data_sources:
     my_new_source:
       file: "source_docs/My_New_Document.xlsx"
       description: "Description of the new data source"
       columns:
         id: "ID"
         title: "Title"
         description: "Description"
   ```
3. Regenerate the database: `docker compose run --rm data-processing-service`

### Service Ports

The default port mappings are defined in `config/common.yaml`. You can override these by creating a `.env` file in the project root:

```bash
# Optional: Override ports defined in config/common.yaml
DATABASE_PORT=5001
DASHBOARD_PORT=5002
```

> [!TIP]
> If you change ports in `.env`, the Docker containers will automatically use the new values for both internal communication and host mapping.

### Deployment

1. **Set environment variables**:

   The system defaults to values in `config/common.yaml`. You can override them with a `.env` file if needed, but it is not required.
2. **Generate database**:

   ```bash
   docker compose run --rm data-processing-service
   ```
3. **Deploy with Docker Compose**:

   ```bash
   docker compose up
   ```
4. **Verify deployment**:

   ```bash
   docker compose up --health
   ```

## 📁 Project Structure

```
AI_RCD/
├── config/                          # Centralized configuration
│   ├── common.yaml                  # Shared configuration
│   ├── database.yaml               # Database service config
│   └── dashboard.yaml              # Dashboard service config
├── source_docs/                     # Source Excel files
│   ├── AIML_RISK_TAXONOMY_V6.xlsx
│   ├── AIML_CONTROL_FRAMEWORK_V4.xlsx
│   └── AI_Definitions_and_Taxonomy_V1.xlsx
├── data-processing-service/         # Data extraction and processing
│   ├── config/
│   │   └── default_config.yaml     # Source document configuration
│   └── extractors/                 # Excel file extractors
├── database-service/               # Database API service
├── dashboard-service/              # Frontend dashboard
├── docker-compose.yml              # Production deployment
```

## 📊 API Documentation

### Database Service API

- `GET /api/health` - Health check
- `GET /api/risks` - List all risks
- `GET /api/controls` - List all controls
- `GET /api/definitions` - List all AI/ML terminology definitions
- `GET /api/relationships` - Get relationship mappings
- `GET /api/search?q={query}` - Search across all data

### Dashboard Service API

- `GET /` - Main dashboard interface
- `GET /api/health` - Health check
- All database API endpoints are proxied through the dashboard service

## 📋 Data Sources

The platform processes five main Excel files from the `source_docs/` directory to build the AI/ML risk management database:

### Risk Taxonomy

- **File**: `AIML_RISK_TAXONOMY_V6.xlsx`
- **Content**: AI/ML risk definitions and descriptions
- **Configuration**: `data-processing-service/config/default_config.yaml` → `data_sources.risks`

### Control Framework

- **File**: `AIML_CONTROL_FRAMEWORK_V4.xlsx`
- **Content**: AI control domains and purposes
- **Configuration**: `data-processing-service/config/default_config.yaml` → `data_sources.controls`


### AI/ML Definitions & Taxonomy

- **File**: `AI_Definitions_and_Taxonomy_V1.xlsx`
- **Content**: AI/ML terminology definitions
- **Configuration**: `data-processing-service/config/default_config.yaml` → `data_sources.definitions`

### Database Schema

The processed data is stored in a normalized SQLite database (`aiml_data.db`) with the following tables:

- `risks` - Risk definitions and descriptions
- `controls` - Control definitions and metadata
- `definitions` - AI/ML terminology definitions
- `risk_control_mapping` - Many-to-many risk-control relationships
- `file_metadata` - File versioning and processing information
- `processing_metadata` - Processing statistics and timestamps

## 🛠️ Development

### Service-Specific Development

Each service can be developed independently:

```bash
# Database Service
cd database-service
pip install -r requirements.txt
python app.py

# Dashboard Service
cd dashboard-service
pip install -r requirements.txt
python app.py

# Data Processing Service
cd data-processing-service
pip install -r requirements.txt
python app.py
```

### Adding Dependencies

1. Add to the appropriate file in `requirements/`
2. Update the service's `requirements.txt` to reference it
3. Update Dockerfiles if needed

### Configuration Changes

1. Update the appropriate file in `config/` or `data-processing-service/config/`
2. Test with the affected service
3. Regenerate database if source document configuration changed: `docker compose run --rm data-processing-service`
4. Update documentation if needed

### Testing

Each service has a comprehensive test suite:

```bash
# Run tests for a specific service
cd <service-directory>
pytest

# Run all tests
python run_all_tests.py
```

## 🆘 Troubleshooting

### Services Won't Start

```bash
# Check service status
docker compose ps

# View logs
docker compose logs

# Restart services
docker compose restart
```

### Database Connection Issues

```bash
# Check database service health
curl http://localhost:5001/api/health

# Regenerate database
docker compose run --rm data-processing-service
```

### Database Generation Fails

If database generation fails:

1. **Check source files exist**:

   ```bash
   ls -la source_docs/*.xlsx
   ```
2. **Verify configuration**:

   ```bash
   cat data-processing-service/config/default_config.yaml
   ```
3. **Check file paths in config**: Ensure file paths in `default_config.yaml` match actual file names in `source_docs/`

   ```bash
   cd data-processing-service
   python app.py
   ```

### Port Conflicts

If ports 5001 or 5002 are already in use:

1. Edit `.env` file
2. Change `DATABASE_PORT` and `DASHBOARD_PORT`
3. Restart services: `docker compose restart`

### Source Document Configuration Issues

If data isn't being extracted correctly:

1. **Check column names**: Verify the `columns` section in `default_config.yaml` matches your Excel file headers
2. **Use alternative columns**: The service supports `alternative_columns` for flexible schema matching
3. **Enable resilient mode**: The default mode auto-detects columns, but you can verify in the config
4. **Check sheet names**: For multi-sheet files, verify the `sheets` configuration matches actual sheet names



## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

- [Deployment Guide](docs/DEPLOYMENT.md)
- [Data Processing Config](data-processing-service/README.md)

## 🤝 Community

- [Contributing Guidelines](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
