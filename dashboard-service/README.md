# Dashboard Service

A Flask-based microservice that provides the frontend web interface for the AIML Risk Management Dashboard. This service serves HTML/CSS/JavaScript to browsers and proxies API requests to the Database Service.

## 🎯 Overview

The Dashboard Service is the user-facing component of the AI_RCD platform. It provides:

- **Web Interface**: Interactive dashboard with visualizations and data exploration
- **API Proxy**: Routes API requests to the Database Service
- **Static Assets**: Serves CSS, JavaScript, and templates
- **Security**: Implements CORS, security headers, and content security policies

## 🏗️ Architecture

### Service Role

```
┌─────────────────────────────────────────┐
│         User Browser                     │
│      http://localhost:5002               │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│      Dashboard Service (Port 5002)      │
│  • Flask web application                │
│  • Serves HTML/CSS/JavaScript           │
│  • Proxies API requests                 │
│  • Handles CORS and security            │
└──────────────────┬───────────────────────┘
                   │ HTTP REST API
                   │ (via Docker network)
                   ▼
┌─────────────────────────────────────────┐
│      Database Service (Port 5001)       │
│  • FastAPI REST API                     │
│  • SQLite database access               │
└─────────────────────────────────────────┘
```

### Key Components

- **`app.py`**: Main Flask application and entry point
- **`config_manager.py`**: Configuration management from YAML files
- **`routes/`**: Blueprint modules for API endpoints
  - `database_proxy.py`: Proxies requests to Database Service
- **`auth/`**: Authentication utilities (currently disabled by default)
- **`utils/`**: Utility functions for error handling
- **`static/`**: Frontend assets (CSS, JavaScript)
- **`templates/`**: HTML templates (Jinja2)

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Database Service running and accessible
- Port 5002 available

### Running Locally

```bash
# Install dependencies
cd dashboard-service
pip install -r requirements.txt

# Set environment variables
export PORT=5002
export DATABASE_URL=http://localhost:5001
export DATABASE_PORT=5001

# Run the service
python app.py
```

The dashboard will be available at `http://localhost:5002`.

### Using Docker

The service is typically run via the launcher script:

```bash
# From project root
docker compose up
```

Or using Docker Compose directly:

```bash
docker-compose up dashboard-service
```

## ⚙️ Configuration

### Configuration File

The service uses `config.yaml` for configuration. Key sections:

#### Server Configuration

```yaml
server:
  host: "0.0.0.0"
  port: "${PORT}"
  debug: false
```

#### Database Service Connection

```yaml
database_service:
  url: "${DATABASE_URL:-http://localhost:${DATABASE_PORT}}"
  timeout: 30
  retry_attempts: 3
```

#### API Configuration

```yaml
api:
  limits:
    default_limit: 100
    max_limit: 1000
    search_limit: 50
  timeouts:
    request_timeout: 30
    search_timeout: 5000
```

#### Frontend Configuration

```yaml
frontend:
  visualization:
    max_items: 50
    animation_duration: 750
  ui:
    theme: "light"
    show_legends: true
```

### Environment Variables

The service respects the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Service port | Required |
| `DATABASE_URL` | Full database service URL | `http://localhost:${DATABASE_PORT}` |
| `DATABASE_HOST` | Database service hostname | `database-service` |
| `DATABASE_PORT` | Database service port | `5001` |
| `HOST` | Bind address | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `false` |

### CORS Configuration

CORS is configured to allow requests from localhost only by default:

```python
# CORS origins are set to localhost with the dashboard port
cors_origins = [f"http://localhost:{dashboard_port}"]
```

This can be modified in `app.py` if needed for different deployment scenarios.

## 📡 API Endpoints

### Dashboard Routes

- `GET /` - Main dashboard interface (serves `index.html`)
- `GET /api/health` - Health check endpoint (includes database service status)
- `GET /api/current-user` - Current user information (hard-coded to user_id 1)

### Proxied Database Service Endpoints

All database service endpoints are proxied through the dashboard service:

- `GET /api/risks` - List risks
- `GET /api/risks/summary` - Risks summary with counts
- `GET /api/risk/{risk_id}` - Risk details
- `GET /api/controls` - List controls
- `GET /api/controls/summary` - Controls summary
- `GET /api/control/{control_id}` - Control details
- `GET /api/control/{control_id}` - Control details
- `GET /api/definitions` - List definitions
- `GET /api/relationships` - Get relationship mappings
- `GET /api/search?q={query}` - Search across all entities
- `GET /api/stats` - Database statistics
- `GET /api/file-metadata` - File metadata including versions

## 🛠️ Development

### Setup

```bash
# Install dependencies
make install

# Install test dependencies
make install-test

# Or manually
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
```

### Running in Development

```bash
# Using Makefile
make run-dev

# Or directly
python app.py
```

### Available Make Commands

```bash
make help              # Show all available commands
make install           # Install production dependencies
make install-test      # Install test dependencies
make test              # Run all tests
make test-unit         # Run unit tests only
make test-integration  # Run integration tests
make test-e2e          # Run end-to-end tests
make test-coverage     # Run tests with coverage
make lint              # Run linting checks
make format            # Format code with black and isort
make clean             # Clean up temporary files
```

### Code Structure

```
dashboard-service/
├── app.py                 # Main Flask application
├── config_manager.py      # Configuration management
├── config.yaml            # Service configuration
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container definition
├── Makefile              # Development commands
├── auth/                 # Authentication utilities
│   ├── decorators.py
│   └── utils.py
├── routes/               # API route blueprints
│   ├── database_proxy.py
├── static/               # Frontend assets
│   ├── css/
│   └── js/
├── templates/            # HTML templates
│   └── index.html
├── utils/                # Utility functions
│   └── error_handling.py
└── tests/               # Test suite
    ├── test_runner.py
    └── ...
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-e2e

# Run with coverage
make test-coverage

# Run tests directly
pytest tests/
```

### Test Structure

- **Unit Tests**: Test individual components in isolation
- **Integration Tests**: Test service interactions with Database Service
- **E2E Tests**: Test complete user workflows

See `tests/README.md` for detailed test documentation.

## 🔒 Security

### Security Headers

The service adds security headers to all responses:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy`: Restricts resource loading

### CORS

CORS is configured to allow requests only from localhost by default. Modify `_get_cors_origins()` in `app.py` for production deployments.

### Authentication

Authentication is currently disabled by default. All routes are publicly accessible. To enable:

1. Set `ENABLE_AUTH=true` in environment
2. Configure authentication in `config.yaml`
3. Implement authentication middleware

## 🐳 Docker

### Building

```bash
# Build from project root
docker build -f dashboard-service/Dockerfile -t dashboard-service .

# Or using Makefile
cd dashboard-service
make docker-build
```

### Running

```bash
# Run container
docker run -p 5002:5002 \
  -e PORT=5002 \
  -e DATABASE_URL=http://database-service:5001 \
  dashboard-service
```

### Health Check

The container includes a health check:

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1
```

## 🆘 Troubleshooting

### Service Won't Start

1. **Check port availability**:
   ```bash
   lsof -i :5002
   ```

2. **Verify Database Service is running**:
   ```bash
   curl http://localhost:5001/api/health
   ```

3. **Check environment variables**:
   ```bash
   echo $PORT
   echo $DATABASE_URL
   ```

### Database Connection Issues

1. **Verify Database Service URL**:
   ```bash
   curl $DATABASE_URL/api/health
   ```

2. **Check service logs**:
   ```bash
   docker logs dashboard-service
   # Or if running locally
   python app.py
   ```

3. **Test database service connection**:
   The service logs database service health on startup.

### CORS Errors

If you see CORS errors in the browser:

1. **Check CORS configuration** in `app.py`:
   ```python
   cors_origins = _get_cors_origins()
   ```

2. **Verify the origin** matches the configured origins

3. **Check browser console** for specific CORS error messages

### Frontend Not Loading

1. **Check static files are copied**:
   ```bash
   ls -la static/
   ls -la templates/
   ```

2. **Verify template rendering**:
   ```bash
   curl http://localhost:5002/
   ```

3. **Check browser console** for JavaScript errors

## 📊 Dependencies

### Core Dependencies

- **Flask**: Web framework
- **Flask-CORS**: CORS support
- **requests**: HTTP client for Database Service API
- **PyYAML**: Configuration file parsing

### Development Dependencies

See `tests/requirements-test.txt` for test dependencies.

## 📝 Notes

- The service uses a `DatabaseAPIClient` class to communicate with the Database Service
- All database queries are proxied through the dashboard service
- The frontend is a single-page application served from `templates/index.html`
- Static assets are served from the `static/` directory
- Configuration can be overridden via environment variables

## 🔗 Related Documentation

- **Main README**: `/README.md` - Overall platform documentation
- **Database Service**: `/database-service/README.md` - Database service documentation
- **Test Documentation**: `/dashboard-service/tests/README.md` - Test suite documentation
