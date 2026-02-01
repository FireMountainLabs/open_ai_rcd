#!/usr/bin/env python3
"""
AIML Dashboard Service

A microservice that provides the frontend interface for the AIML Risk Management
Dashboard. This service consumes the Database Service API instead of accessing
the database directly.
"""

import logging
import requests
import os
from typing import Dict, Any
from flask import Flask, render_template, jsonify
from flask_cors import CORS

from config_manager import ConfigManager
from routes.database_proxy import create_database_proxy_blueprint

# Import CommonConfigManager with fallback
try:
    from shared_services.common_config import common_config

    COMMON_CONFIG_AVAILABLE = True
except ImportError:
    COMMON_CONFIG_AVAILABLE = False
    common_config = None

# Initialize configuration manager
config_manager = ConfigManager()

# Load configuration
config = config_manager.load_config()
server_config = config_manager.get_server_config()
database_service_config = config_manager.get_database_service_config()
api_config = config_manager.get_api_config()
frontend_config = config_manager.get_frontend_config()
logging_config = config_manager.get_logging_config()


# Configure logging
def get_log_level(level_str):
    """Convert string log level to logging constant."""
    level_str = str(level_str).upper()
    if hasattr(logging, level_str):
        return getattr(logging, level_str)
    else:
        # Default to INFO if invalid level
        return logging.INFO


logging.basicConfig(
    level=get_log_level(logging_config.get("level", "INFO")),
    format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)


# Configuration from CommonConfigManager
def _get_service_urls():
    """Get service URLs from environment variables or CommonConfigManager."""

    # Always check environment variables first - they take precedence
    database_url = os.getenv("DATABASE_URL")

    # If URL is provided via environment, use it
    if database_url:
        return database_url

    # If CommonConfigManager is available, use it for missing URLs
    if COMMON_CONFIG_AVAILABLE and common_config:
        if not database_url:
            database_url = common_config.get_service_url("database")
    else:
        # Build URLs from individual environment variables
        if not database_url:
            database_host = os.getenv("DATABASE_HOST", "database-service")
            database_port = os.getenv("DATABASE_PORT")
            database_url = f"http://{database_host}:{database_port}"

    return database_url


DATABASE_URL = _get_service_urls()
PORT = server_config.get("port")
HOST = server_config.get("host", "0.0.0.0")

# Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management


# Configure CORS for localhost only
def _get_cors_origins():
    """Get CORS origins for localhost only."""
    dashboard_port = os.getenv("DASHBOARD_PORT", "5002")
    return [f"http://localhost:{dashboard_port}"]


cors_origins = _get_cors_origins()
CORS(
    app,
    origins=cors_origins,
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    supports_credentials=True,
)


# Add security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' https://d3js.org https://unpkg.com; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    )
    return response


# API client for database service
class DatabaseAPIClient:
    """Client for communicating with the database service."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.timeout = database_service_config.get("timeout", 30)

    def health_check(self) -> Dict[str, Any]:
        """Check database service health."""
        try:
            response = self.session.get(f"{self.base_url}/api/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Database service health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_risks(self, limit: int = 100, offset: int = 0, category: str = None) -> Dict[str, Any]:
        """Get risks from database service."""
        try:
            params = {"limit": limit, "offset": offset}
            if category:
                params["category"] = category

            response = self.session.get(f"{self.base_url}/api/risks", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch risks: {e}")
            return []

    def get_risks_summary(self) -> Dict[str, Any]:
        """Get risks summary with counts for dashboard tables."""
        try:
            response = self.session.get(f"{self.base_url}/api/risks/summary")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch risks summary: {e}")
            return {"details": []}

    def get_controls(self, limit: int = 100, offset: int = 0, domain: str = None) -> Dict[str, Any]:
        """Get controls from database service."""
        try:
            params = {"limit": limit, "offset": offset}
            if domain:
                params["domain"] = domain

            response = self.session.get(f"{self.base_url}/api/controls", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch controls: {e}")
            return []

    def get_controls_summary(self) -> Dict[str, Any]:
        """Get controls summary with counts for dashboard tables."""
        try:
            response = self.session.get(f"{self.base_url}/api/controls/summary")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch controls summary: {e}")
            return {"details": []}


    def get_definitions(self, limit: int = 100, offset: int = 0, category: str = None) -> Dict[str, Any]:
        """Get definitions from database service."""
        try:
            params = {"limit": limit, "offset": offset}
            if category:
                params["category"] = category

            response = self.session.get(f"{self.base_url}/api/definitions", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch definitions: {e}")
            return []

    def get_relationships(self, relationship_type: str = None, limit: int = 1000) -> Dict[str, Any]:
        """Get relationships from database service."""
        try:
            params = {"limit": limit}
            if relationship_type:
                params["relationship_type"] = relationship_type

            response = self.session.get(f"{self.base_url}/api/relationships", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch relationships: {e}")
            return []

    def search(self, query: str, limit: int = 50) -> Dict[str, Any]:
        """Search across all entities."""
        try:
            params = {"q": query, "limit": limit}
            response = self.session.get(f"{self.base_url}/api/search", params=params)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"query": query, "results": []}

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            response = self.session.get(f"{self.base_url}/api/stats")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch stats: {e}")
            return {}

    def get_file_metadata(self) -> Dict[str, Any]:
        """Get file metadata including versions."""
        try:
            response = self.session.get(f"{self.base_url}/api/file-metadata")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch file metadata: {e}")
            return {}

    def get_risk_detail(self, risk_id: str) -> Dict[str, Any]:
        """Get detailed risk information."""
        try:
            response = self.session.get(f"{self.base_url}/api/risk/{risk_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch risk detail: {e}")
            return {"error": str(e)}

    def get_control_detail(self, control_id: str) -> Dict[str, Any]:
        """Get detailed control information."""
        try:
            response = self.session.get(f"{self.base_url}/api/control/{control_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch control detail: {e}")
            return {"error": str(e)}




# Initialize API client
api_client = DatabaseAPIClient(DATABASE_URL)

# Register blueprints
# Register database proxy routes
database_proxy_bp = create_database_proxy_blueprint(DATABASE_URL, api_client, api_config)
app.register_blueprint(database_proxy_bp)



# Routes
@app.route("/")
def index():
    """Serves the main dashboard page."""
    # Get configuration for frontend from YAML
    viz_config = frontend_config.get("visualization", {})
    ui_config = frontend_config.get("ui", {})
    dependencies = frontend_config.get("dependencies", {})
    api_limits = api_config.get("limits", {})
    api_timeouts = api_config.get("timeouts", {})

    config = {
        "database_url": DATABASE_URL,
        "api_endpoints": {
            "risks": f"{DATABASE_URL}/api/risks",
            "controls": f"{DATABASE_URL}/api/controls",
            "questions": f"{DATABASE_URL}/api/questions",
            "relationships": f"{DATABASE_URL}/api/relationships",
            "search": f"{DATABASE_URL}/api/search",
            "stats": f"{DATABASE_URL}/api/stats",
        },
        "visualization": viz_config,
        "ui": ui_config,
    }

    search_config = {
        "max_results": api_limits.get("search_limit", 50),
        "timeout": api_timeouts.get("search_timeout", 5000),
        "debounce_delay": api_timeouts.get("debounce_delay", 300),
    }

    return render_template(
        "index.html",
        config=config,
        viz_config=viz_config,
        ui_config=ui_config,
        search_config=search_config,
        d3_js=dependencies.get("d3_js", "https://d3js.org/d3.v7.min.js"),
        d3_sankey=dependencies.get("d3_sankey", "https://unpkg.com/d3-sankey@0.12.3/dist/d3-sankey.min.js"),
    )


@app.route("/api/current-user")
def current_user():
    """Get current user information. Hard-coded to user_id 1 for this release."""
    return jsonify({"user_id": 1})


@app.route("/api/health")
def health():
    """Health check endpoint."""
    try:
        db_health = api_client.health_check()
        return jsonify(
            {
                "status": ("healthy" if db_health.get("status") == "healthy" else "unhealthy"),
                "database_service": db_health,
                "dashboard_service": {
                    "status": "healthy",
                    "database_url": DATABASE_URL,
                },
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify(
            {
                "status": "unhealthy",
                "database_service": {"status": "unhealthy", "error": str(e)},
                "dashboard_service": {
                    "status": "healthy",
                    "database_url": DATABASE_URL,
                },
            }
        )


def main():
    """Main entry point."""
    logger.info(f"Starting AIML Dashboard Service on {HOST}:{PORT}")
    logger.info(f"Database service URL: {DATABASE_URL}")

    # Test database service connection
    db_health = api_client.health_check()
    if db_health.get("status") != "healthy":
        logger.warning(f"Database service is not healthy: {db_health}")
    else:
        logger.info("Database service connection successful")

    app.run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    main()
