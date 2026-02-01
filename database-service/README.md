# Database Service

A FastAPI-based microservice that provides REST API access to the SQLite database for the AI_RCD platform. This service acts as the data access layer, handling all database queries and providing structured API responses to the Dashboard Service.

## 🎯 Overview

The Database Service is responsible for:

- **REST API**: Provides HTTP endpoints for all database operations
- **Data Access**: Manages SQLite database connections and queries
- **Relationship Queries**: Handles complex queries for risk-control mappings
- **Search Functionality**: Full-text search across all entities
- **Metadata Management**: Tracks file versions and processing information

**Note**: This is a long-running service that must be running for the Dashboard Service to function.

## 🏗️ Architecture

### Service Role

```
┌─────────────────────────────────────────┐
│      Dashboard Service (Port 5002)      │
│  • Flask web application                │
│  • Frontend UI                          │
└──────────────────┬──────────────────────┘
                   │ HTTP REST API
                   │ (via Docker network)
                   ▼
┌─────────────────────────────────────────┐
│      Database Service (Port 5001)      │
│  • FastAPI REST API                    │
│  • SQLite database access              │
│  • Query processing                    │
│  • Relationship mapping                │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      SQLite Database                    │
│  aiml_data.db (read-only)             │
│  • Risks, Controls                       │
│  • Definitions                        │
│  • Relationship mappings               │
│  • Metadata                            │
└─────────────────────────────────────────┘
```

### Key Components

- **`app.py`**: Main FastAPI application and API endpoints
- **`config_manager.py`**: Configuration management from YAML files
- `db/connections.py`: Database connection management
- **`config.yaml`**: Service configuration

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- SQLite database file (`aiml_data.db`)
- Port 5001 available

### Running Locally

```bash
# Install dependencies
cd database-service
pip install -r requirements.txt

# Set environment variables
export DATABASE_PORT=5001
export DB_PATH=../aiml_data.db

# Run the service
python app.py
```

The API will be available at `http://localhost:5001`.

### Using Docker

The service is typically run via the launcher script:

```bash
# From project root
docker compose up
```

Or using Docker Compose directly:

```bash
docker-compose up database-service
```

### API Documentation

Once running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:5001/docs`
- **ReDoc**: `http://localhost:5001/redoc`

## ⚙️ Configuration

### Configuration File

The service uses `config.yaml` for configuration. Key sections:

#### Server Configuration

```yaml
server:
  host: "0.0.0.0"
  port: "${DATABASE_PORT}"
  debug: false
```

#### Database Configuration

```yaml
database:
  path: "${DB_PATH:-aiml_data.db}"
  timeout: 30
  check_same_thread: false
  required_tables:
    - "risks"
    - "controls"
    - "definitions"
```

#### API Configuration

```yaml
api:
  limits:
    default_limit: 100
    max_limit: 1000
    max_relationships_limit: 5000
    search_limit: 200
  request_timeout: 30
```

### Environment Variables

The service respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_PORT` | Service port | Required |
| `DB_PATH` | Path to SQLite database file | `aiml_data.db` |
| `API_HOST` | Bind address | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `false` |

### CORS Configuration

CORS is configured to allow requests from localhost only by default:

```python
cors_origins = [f"http://localhost:{database_port}"]
```

This can be modified in `app.py` if needed for different deployment scenarios.

## 📡 API Endpoints

### Health & Status

- `GET /` - Root endpoint (returns health status)
- `GET /api/health` - Health check endpoint
- `GET /api/stats` - Database statistics
- `GET /api/file-metadata` - File metadata including versions
- `GET /api/last-updated` - Last update timestamp

### Core Data Endpoints

#### Risks

- `GET /api/risks` - List all risks (with pagination and filtering)
  - Query parameters: `limit`, `offset`, `category`
- `GET /api/risks/summary` - Risks summary with counts
- `GET /api/risk/{risk_id}` - Get specific risk details

#### Controls

- `GET /api/controls` - List all controls (with pagination and filtering)
  - Query parameters: `limit`, `offset`, `domain`
- `GET /api/controls/summary` - Controls summary with counts
- `GET /api/control/{control_id}` - Get specific control details
- `GET /api/controls/mapped` - Get controls with risk mappings

#### Definitions

- `GET /api/definitions` - List all definitions (with pagination and filtering)
  - Query parameters: `limit`, `offset`, `category`

#### Relationships
 & Mapping Endpoints

- `GET /api/relationships` - Get relationship mappings
  - Query parameters: `relationship_type`, `limit`
- `GET /api/network` - Get network graph data for visualizations
- `GET /api/gaps` - Get coverage gap analysis

### Search

- `GET /api/search` - Search across all entities
  - Query parameters: `q` (search query, required), `limit`

## 🛠️ Development

### Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r tests/requirements-test.txt
```

### Running in Development

```bash
# Run directly
python app.py

# Or with uvicorn for hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 5001
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_endpoints.py
pytest tests/test_integration.py

# Run with coverage
pytest --cov=. --cov-report=html
```

### Project Structure

```
database-service/
├── app.py                    # Main FastAPI application
├── config_manager.py         # Configuration management
├── config.yaml               # Service configuration
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container definition
├── start.sh                 # Launcher script
├── api/                     # API route modules
│   └── README.md
├── db/                      # Database utilities
│   └── connections.py
└── tests/                   # Test suite
    ├── test_endpoints.py
    ├── test_integration.py
    └── ...
```

### Adding New Endpoints

1. Define Pydantic models for request/response:
   ```python
   class MyModel(BaseModel):
       id: str
       title: str
   ```

2. Add endpoint in `app.py`:
   ```python
   @app.get("/api/my-endpoint", response_model=List[MyModel])
   async def get_my_data():
       # Implementation
       pass
   ```

3. Add tests in `tests/test_endpoints.py`

## 🐳 Docker

### Building

```bash
# Build from project root
docker build -f database-service/Dockerfile -t database-service .

# Or from service directory
cd database-service
docker build -t database-service .
```

### Running

```bash
# Run container with volume mount for database
docker run -p 5001:5001 \
  -v $(pwd)/aiml_data.db:/data/aiml_data.db \
  -e DATABASE_PORT=5001 \
  -e DB_PATH=/data/aiml_data.db \
  database-service
```

### Health Check

The container includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${DATABASE_PORT}/api/health || exit 1
```

## 🗄️ Database Schema

The service accesses a SQLite database with the following structure:

### Core Tables

- **`risks`**: Risk definitions
  - `risk_id`, `risk_title`, `risk_description`, `category`
- **`controls`**: Control definitions
  - `control_id`, `control_title`, `control_description`, `security_function`

- **`definitions`**: AI/ML terminology
  - `definition_id`, `term`, `title`, `description`, `category`, `source`

### Relationship Tables

- **`risk_control_mapping`**: Risk-control relationships

### Metadata Tables

- **`file_metadata`**: File versioning and processing information
- **`processing_metadata`**: Processing statistics and timestamps

## 🔒 Security

### Database Access

- The service uses **read-only** access to the main database by default
- Database file is mounted as a volume in Docker
- Connection pooling and timeout management prevent resource exhaustion

### CORS

CORS is configured to allow requests only from localhost by default. Modify `cors_origins` in `app.py` for production deployments.

### Input Validation

- All endpoints use Pydantic models for request/response validation
- Query parameters are validated (limits, offsets, etc.)
- SQL injection prevention via parameterized queries

## 🆘 Troubleshooting

### Service Won't Start

1. **Check port availability**:
   ```bash
   lsof -i :5001
   ```

2. **Verify database file exists**:
   ```bash
   ls -la aiml_data.db
   ```

3. **Check environment variables**:
   ```bash
   echo $DATABASE_PORT
   echo $DB_PATH
   ```

### Database Connection Issues

1. **Verify database file path**:
   ```bash
   # Check if file exists at configured path
   ls -la $DB_PATH
   ```

2. **Check database file permissions**:
   ```bash
   ls -l aiml_data.db
   # Should be readable by the service user
   ```

3. **Validate database schema**:
   ```bash
   sqlite3 aiml_data.db ".tables"
   ```

4. **Test database connection**:
   ```bash
   sqlite3 aiml_data.db "SELECT COUNT(*) FROM risks;"
   ```

### API Errors

1. **Check service logs**:
   ```bash
   docker logs database-service
   # Or if running locally
   python app.py
   ```

2. **Test health endpoint**:
   ```bash
   curl http://localhost:5001/api/health
   ```

3. **Check API documentation**:
   ```bash
   # Open in browser
   http://localhost:5001/docs
   ```

### Missing Tables Error

If you see errors about missing tables:

1. **Verify database was generated**:
   ```bash
docker compose run --rm data-processing-service
```

2. **Check required tables exist**:
   ```bash
   sqlite3 aiml_data.db ".tables"
   ```

3. **Review database validation**:
   The service validates required tables on startup. Check logs for missing table names.

### CORS Errors

If you see CORS errors:

1. **Check CORS configuration** in `app.py`:
   ```python
   cors_origins = [f"http://localhost:{database_port}"]
   ```

2. **Verify the origin** matches the configured origins

3. **Check browser console** for specific CORS error messages

## 📊 Performance

### Query Optimization

- **Pagination**: All list endpoints support `limit` and `offset`
- **Indexing**: Database indexes on foreign keys and frequently queried columns
- **Connection Pooling**: Managed database connections
- **Query Caching**: Optional query result caching (configurable)

### Rate Limiting

API limits are configurable in `config.yaml`:

```yaml
api:
  limits:
    default_limit: 100
    max_limit: 1000
    search_limit: 200
```

### Monitoring

- Health check endpoint provides service status
- Database statistics endpoint for monitoring
- Comprehensive logging at multiple levels

## 📝 Notes

- The service uses **FastAPI** for high-performance async API handling
- **Pydantic** models ensure type safety and validation
- **SQLite** is used for main data
- Database connections use context managers for proper cleanup
- All endpoints return JSON responses
- Interactive API documentation is available at `/docs`

## 🔗 Related Documentation

- **Main README**: `/README.md` - Overall platform documentation
- **Dashboard Service**: `/dashboard-service/README.md` - Frontend service documentation
- **Data Processing Service**: `/data-processing-service/README.md` - Database generation service documentation
- **Test Documentation**: `/database-service/tests/README.md` - Test suite documentation
