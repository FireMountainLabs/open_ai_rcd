#!/usr/bin/env python3
"""
AIML Database Service

A microservice that provides REST API access to SQLite database files.
This service can ingest database files at runtime and provide controlled
API access for the dashboard service.
Updated: Fresh build trigger
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from config_manager import ConfigManager
from db.connections import DatabaseManager
from api.models import Risk, Control, Definition, Relationship, DatabaseStats, HealthStatus
from db.repositories import (
    RiskRepository, ControlRepository, DefinitionRepository,
    RelationshipRepository, SearchRepository, StatsRepository, NetworkRepository, GapsRepository
)

# Initialize configuration manager
config_manager = ConfigManager()

# Load configuration
config = config_manager.load_config()
server_config = config_manager.get_server_config()
database_config = config_manager.get_database_config()
api_config = config_manager.get_api_config()
logging_config = config_manager.get_logging_config()

# Configure logging
logging.basicConfig(
    level=getattr(logging, logging_config.get("level", "INFO")),
    format=logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
)
logger = logging.getLogger(__name__)

# Configuration from YAML
DB_PATH = database_config.get("path", "aiml_data.db")
API_PORT = int(server_config.get("port"))
API_HOST = server_config.get("host", "0.0.0.0")

# Initialize DatabaseManager and Repositories
db_manager = DatabaseManager(DB_PATH)
risk_repo = RiskRepository(db_manager)
control_repo = ControlRepository(db_manager)
definition_repo = DefinitionRepository(db_manager)
relationship_repo = RelationshipRepository(db_manager)
search_repo = SearchRepository(db_manager)
stats_repo = StatsRepository(db_manager)
network_repo = NetworkRepository(db_manager)
gaps_repo = GapsRepository(db_manager)


def reinitialize_repositories(new_db_path: str):
    """Reinitialize all repositories with a new database path. Used for testing."""
    global db_manager, risk_repo, control_repo, definition_repo
    global relationship_repo, search_repo, stats_repo, network_repo, gaps_repo
    global DB_PATH
    
    DB_PATH = new_db_path
    db_manager = DatabaseManager(new_db_path)
    risk_repo = RiskRepository(db_manager)
    control_repo = ControlRepository(db_manager)
    definition_repo = DefinitionRepository(db_manager)
    relationship_repo = RelationshipRepository(db_manager)
    search_repo = SearchRepository(db_manager)
    stats_repo = StatsRepository(db_manager)
    network_repo = NetworkRepository(db_manager)
    gaps_repo = GapsRepository(db_manager)



# Pydantic models for API responses
# FastAPI app
app = FastAPI(
    title="AIML Database Service",
    description="REST API for AIML Risk Management Database",
    version="1.0.0",
)




# Database connection manager
def get_db_connection():
    """Context manager for database connections."""
    return db_manager.get_db_connection()






# FastAPI app
# Initialized above





# CORS middleware - localhost only
cors_config = config.get("cors", {})
database_port = os.getenv("DATABASE_PORT", "5001")
cors_origins = [f"http://localhost:{database_port}"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=cors_config.get("allow_credentials", True),
    allow_methods=cors_config.get("allow_methods", ["*"]),
    allow_headers=cors_config.get("allow_headers", ["*"]),
)


# Database validation
def validate_database() -> bool:
    """Validate that the database exists and has required tables."""
    if not Path(DB_PATH).exists():
        logger.error(f"Database file not found: {DB_PATH}")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Check for required tables from config
            required_tables = database_config.get(
                "required_tables",
                ["risks", "controls", "definitions"],
            )
            table_placeholders = ",".join(["?" for _ in required_tables])

            cursor.execute(
                f"""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ({table_placeholders})
            """,
                required_tables,
            )
            tables = [row[0] for row in cursor.fetchall()]

            if len(tables) < len(required_tables):
                missing_tables = set(required_tables) - set(tables)
                logger.error(f"Missing required tables: {missing_tables}. Found: {tables}")
                return False

            return True
    except Exception as e:
        logger.error(f"Database validation failed: {e}")
        return False


# API Routes
@app.get("/", response_model=HealthStatus)
async def root():
    """Root endpoint that displays health status."""
    return await health_check()


@app.get("/api/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    db_connected = validate_database()
    stats = stats_repo.get_stats() if db_connected else {}
    total_records = sum(stats.get(k, 0) for k in ["total_risks", "total_controls"])

    return HealthStatus(
        status="healthy" if db_connected else "unhealthy",
        database_connected=db_connected,
        database_path=DB_PATH,
        total_records=total_records,
    )


@app.get("/api/risks", response_model=List[Risk])
async def get_risks(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
):
    """Get all risks with optional filtering."""
    try:
        limit = limit or api_config.get("limits", {}).get("default_limit", 100)
        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        rows = risk_repo.get_all(limit=limit, offset=offset, category=category)
        return [Risk(**row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching risks: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/controls", response_model=List[Control])
async def get_controls(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    domain: Optional[str] = None,
):
    """Get all controls with optional filtering."""
    try:
        limit = limit or api_config.get("limits", {}).get("default_limit", 100)
        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        rows = control_repo.get_all(limit=limit, offset=offset, domain=domain)
        return [Control(**row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching controls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/definitions", response_model=List[Definition])
async def get_definitions(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
):
    """Get all definitions with optional filtering."""
    try:
        limit = limit or api_config.get("limits", {}).get("default_limit", 100)
        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        rows = definition_repo.get_all(limit=limit, offset=offset, category=category)
        return [Definition(**row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relationships", response_model=List[Relationship])
async def get_relationships(relationship_type: Optional[str] = None, limit: int = Query(None, ge=1)):
    """Get relationship mappings between entities."""
    try:
        limit = limit or api_config.get("limits", {}).get("max_relationships_limit", 1000)
        max_limit = api_config.get("limits", {}).get("max_relationships_limit", 5000)
        limit = min(limit, max_limit)

        rows = relationship_repo.get_relationships(relationship_type=relationship_type, limit=limit)
        return [Relationship(**row) for row in rows]

    except Exception as e:
        logger.error(f"Error fetching relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2, max_length=100), limit: int = Query(None, ge=1)):
    """Search across all entities."""
    try:
        limit = limit or api_config.get("limits", {}).get("search_limit", 50)
        max_limit = api_config.get("limits", {}).get("search_limit", 200)
        limit = min(limit, max_limit)

        results = []

        # Search risks
        risk_results = search_repo.search("risk", q, limit)
        results.extend(risk_results)

        # Search controls
        control_results = search_repo.search("control", q, limit)
        results.extend(control_results)

        # Search definitions
        def_results = search_repo.search("definition", q, limit)
        results.extend(def_results)

        return {"query": q, "results": results[:limit]}

    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=DatabaseStats)
async def get_stats():
    """Get database statistics."""
    try:
        stats = stats_repo.get_stats()
        return DatabaseStats(
            total_risks=stats.get("total_risks", 0),
            total_controls=stats.get("total_controls", 0),
            total_definitions=stats.get("total_definitions", 0),
            total_relationships=stats.get("total_relationships", 0),
            database_version=stats.get("database_version"),
        )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risks/summary")
async def get_risks_summary():
    """Get risks with control and question counts for dashboard tables."""
    try:
        all_risks = risk_repo.get_all()
        risks = [
            {
                "risk_id": risk["id"],
                "risk_title": risk["title"],
                "risk_description": risk["description"],
                "control_count": len(risk_repo.get_associated_controls(risk["id"])),
            }
            for risk in all_risks
        ]
        return {"details": risks}

    except Exception as e:
        logger.error(f"Error fetching risks summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/controls/summary")
async def get_controls_summary():
    """Get controls with risk and question counts for dashboard tables."""
    try:
        all_controls = control_repo.get_all()
        controls = [
            {
                "control_id": control["id"],
                "control_title": control["title"],
                "control_description": control["description"],
                "security_function": control["domain"],
                "risk_count": len(control_repo.get_associated_risks(control["id"])),
            }
            for control in all_controls
        ]
        return {"details": controls}

    except Exception as e:
        logger.error(f"Error fetching controls summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/{risk_id}")
async def get_risk_detail(risk_id: str):
    """Get detailed risk information including associations."""
    try:
        risk = risk_repo.get_by_id(risk_id)
        if not risk:
            raise HTTPException(status_code=404, detail=f"Risk {risk_id} not found")

        return {
            "risk": Risk(**risk),
            "associated_controls": [Control(**c) for c in risk_repo.get_associated_controls(risk_id)],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/control/{control_id}")
async def get_control_detail(control_id: str):
    """Get detailed control information including associations."""
    try:
        control = control_repo.get_by_id(control_id)
        if not control:
            raise HTTPException(status_code=404, detail=f"Control {control_id} not found")

        return {
            "control": Control(**control),
            "associated_risks": [Risk(**r) for r in control_repo.get_associated_risks(control_id)],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching control detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file-metadata")
async def get_file_metadata():
    """Get metadata about source files used to build the database."""
    try:
        metadata = stats_repo.get_file_metadata()
        return {m["data_type"]: m for m in metadata}
    except Exception as e:
        logger.error(f"Error fetching file metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/network")
async def get_network_data():
    """Get network data for relationship visualization."""
    try:
        return network_repo.get_network_data()
    except Exception as e:
        logger.error(f"Error fetching network data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gaps")
async def get_gaps_analysis():
    """Get critical gaps analysis - unmapped risks, controls, and questions."""
    try:
        return gaps_repo.get_gaps_analysis()
    except Exception as e:
        logger.error(f"Error fetching gaps data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/last-updated")
async def get_last_updated():
    """Get last updated timestamps and file versions."""
    try:
        metadata_list = stats_repo.get_file_metadata()
        metadata = {row["data_type"]: row for row in metadata_list}

        def get_item(key):
            item = metadata.get(key, {})
            return {
                "last_updated": item.get("file_modified_time", "2025-09-24T20:00:00Z"),
                "version": item.get("version", "unknown"),
            }

        return {
            "risks": get_item("risks"),
            "controls": get_item("controls"),
            "definitions": get_item("definitions"),
        }
    except Exception as e:
        logger.error(f"Error getting last updated data: {e}")
        raise HTTPException(status_code=500, detail=str(e))





def main():
    """Main entry point."""
    logger.info(f"Starting AIML Database Service on {API_HOST}:{API_PORT}")
    logger.info(f"Database path: {DB_PATH}")

    # Validate database on startup
    if not validate_database():
        logger.error("Database validation failed. Exiting.")
        sys.exit(1)

    logger.info("Database validation successful.")


    logger.info("Starting server...")

    uvicorn.run("app:app", host=API_HOST, port=API_PORT, log_level="info", access_log=True)


if __name__ == "__main__":
    main()
