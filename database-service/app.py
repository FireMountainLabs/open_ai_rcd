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
from pydantic import BaseModel
import uvicorn

from config_manager import ConfigManager
from api.capability_scenarios import router as capability_scenarios_router, set_db_manager
from db.connections import DatabaseManager

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
# Use a dedicated configs directory to avoid Docker file mount issues
# Check for mounted configs directory first, then fall back to same dir as main DB
if os.path.exists("/data/configs"):
    CAPABILITY_CONFIG_DB_PATH = "/data/configs/capability_configs.db"
else:
    CAPABILITY_CONFIG_DB_PATH = os.path.join(os.path.dirname(DB_PATH), "capability_configs.db")
# Allow override via environment variable
CAPABILITY_CONFIG_DB_PATH = os.getenv("CAPABILITY_CONFIG_DB_PATH", CAPABILITY_CONFIG_DB_PATH)
API_PORT = int(server_config.get("port"))
API_HOST = server_config.get("host", "0.0.0.0")


# Pydantic models for API responses
class Risk(BaseModel):
    id: str
    title: str
    description: str
    category: Optional[str] = None


class Control(BaseModel):
    id: str
    title: str
    description: str
    domain: Optional[str] = None


class Question(BaseModel):
    id: str
    text: str
    category: Optional[str] = None
    topic: Optional[str] = None


class Definition(BaseModel):
    definition_id: str
    term: str
    title: str
    description: str
    category: Optional[str] = None
    source: Optional[str] = None


class Capability(BaseModel):
    capability_id: str
    capability_name: str
    capability_type: str
    capability_domain: Optional[str] = None
    capability_definition: Optional[str] = None
    candidate_products: Optional[str] = None
    notes: Optional[str] = None


class CapabilityTree(BaseModel):
    capability_id: str
    capability_name: str
    capability_type: str
    capability_domain: Optional[str] = None
    capability_definition: Optional[str] = None
    controls: List[dict] = []
    risks: List[dict] = []


class Relationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str


class DatabaseStats(BaseModel):
    total_risks: int
    total_controls: int
    total_questions: int
    total_definitions: int
    total_capabilities: int
    total_relationships: int
    database_version: Optional[str] = None


class HealthStatus(BaseModel):
    status: str
    database_connected: bool
    database_path: str
    total_records: int


# Capability Configuration Models
class CapabilityScenario(BaseModel):
    scenario_id: Optional[int] = None
    user_id: int
    scenario_name: str
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CapabilityScenarioUpdate(BaseModel):
    scenario_name: Optional[str] = None
    is_default: Optional[bool] = None


class CapabilitySelection(BaseModel):
    capability_id: str
    is_active: bool


class CapabilitySelectionsBulk(BaseModel):
    scenario_id: int
    selections: List[CapabilitySelection]


class CapabilityAnalysisRequest(BaseModel):
    capability_ids: List[str]


class CapabilityAnalysisResponse(BaseModel):
    total_controls: int
    controls_in_capabilities: int
    active_controls: int
    exposed_risks: int
    total_risks: int
    active_risks: int
    partially_covered_risks: int
    # Detailed lists for modal display
    active_controls_list: List[dict] = []
    partially_covered_risks_list: List[dict] = []
    exposed_risks_list: List[dict] = []


# Database connection manager
@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        if conn:
            conn.close()


@contextmanager
def get_capability_config_db():
    """Context manager for capability configuration database connections."""
    conn = None
    try:
        # Ensure the directory exists before creating the database file
        db_dir = os.path.dirname(CAPABILITY_CONFIG_DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Created directory for capability config database: {db_dir}")

        # SQLite will create the file if it doesn't exist
        conn = sqlite3.connect(CAPABILITY_CONFIG_DB_PATH)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Capability config database error: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except OSError as e:
        logger.error(f"OS error creating capability config database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create database directory: {e}")
    finally:
        if conn:
            conn.close()


def init_capability_config_db():
    """Initialize the capability configuration database with schema."""
    logger.info(f"Initializing capability config database at {CAPABILITY_CONFIG_DB_PATH}")

    with get_capability_config_db() as conn:
        cursor = conn.cursor()

        # Create capability_scenarios table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS capability_scenarios (
                scenario_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                scenario_name TEXT NOT NULL,
                is_default BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, scenario_name)
            )
        """
        )

        # Create capability_selections table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS capability_selections (
                selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                capability_id TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
                UNIQUE(scenario_id, capability_id)
            )
        """
        )

        # Create control_selections table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS control_selections (
                selection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                scenario_id INTEGER NOT NULL,
                control_id TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 0,
                FOREIGN KEY (scenario_id) REFERENCES capability_scenarios(scenario_id) ON DELETE CASCADE,
                UNIQUE(scenario_id, control_id)
            )
        """
        )

        # Create indexes
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_scenario_user
            ON capability_scenarios(user_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_selection_scenario
            ON capability_selections(scenario_id)
        """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_control_selection_scenario
            ON control_selections(scenario_id)
        """
        )

        conn.commit()
        logger.info("Capability config database initialized successfully")


# FastAPI app
app = FastAPI(
    title="AIML Database Service",
    description="REST API for AIML Risk Management Database",
    version="1.0.0",
)

# Initialize DatabaseManager and set it for the router
db_manager_instance = DatabaseManager(DB_PATH, CAPABILITY_CONFIG_DB_PATH)
set_db_manager(db_manager_instance)

# Include capability scenarios router
app.include_router(capability_scenarios_router, prefix="/api", tags=["capability-scenarios"])

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
                ["risks", "controls", "questions", "definitions", "capabilities"],
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
    total_records = 0

    if db_connected:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM risks")
                total_records += cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM controls")
                total_records += cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM questions")
                total_records += cursor.fetchone()[0]
        except Exception as e:
            logger.error(f"Error counting records: {e}")

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
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("default_limit", 100)

        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT risk_id as id, risk_title as title, "
                "risk_description as description, NULL as category FROM risks"
            )
            params = []

            if category:
                query += " WHERE category = ?"
                params.append(category)

            query += " ORDER BY id LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Risk(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    category=row["category"],
                )
                for row in rows
            ]

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
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("default_limit", 100)

        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT control_id as id, control_title as title, "
                "control_description as description, "
                "security_function as domain "
                "FROM controls"
            )
            params = []

            if domain:
                query += " WHERE security_function = ?"
                params.append(domain)

            query += " ORDER BY id LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Control(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    domain=row["domain"],
                )
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Error fetching controls: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/questions", response_model=List[Question])
async def get_questions(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
):
    """Get all questions with optional filtering."""
    try:
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("default_limit", 100)

        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT question_id as id, question_text as text, category, topic " "FROM questions"
            params = []

            if category:
                query += " WHERE category = ?"
                params.append(category)

            query += " ORDER BY id LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Question(
                    id=row["id"],
                    text=row["text"],
                    category=row["category"],
                    topic=row["topic"],
                )
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Error fetching questions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/definitions", response_model=List[Definition])
async def get_definitions(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    category: Optional[str] = None,
):
    """Get all definitions with optional filtering."""
    try:
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("default_limit", 100)

        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = "SELECT definition_id, term, title, description, category, source FROM definitions"
            params = []

            if category:
                query += " WHERE category = ?"
                params.append(category)

            query += " ORDER BY term LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Definition(
                    definition_id=row["definition_id"],
                    term=row["term"],
                    title=row["title"],
                    description=row["description"],
                    category=row["category"],
                    source=row["source"],
                )
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Error fetching definitions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/relationships", response_model=List[Relationship])
async def get_relationships(relationship_type: Optional[str] = None, limit: int = Query(None, ge=1)):
    """Get relationship mappings between entities."""
    try:
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("max_relationships_limit", 1000)

        max_limit = api_config.get("limits", {}).get("max_relationships_limit", 5000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all relationship tables
            relationships = []

            # Risk-Control mappings
            if not relationship_type or relationship_type == "risk_control":
                cursor.execute(
                    """
                    SELECT risk_id as source_id, control_id as target_id,
                           'risk_control' as relationship_type
                    FROM risk_control_mapping
                    LIMIT ?
                """,
                    (limit,),
                )
                relationships.extend(
                    [
                        Relationship(
                            source_id=row["source_id"],
                            target_id=row["target_id"],
                            relationship_type=row["relationship_type"],
                        )
                        for row in cursor.fetchall()
                    ]
                )

            # Question-Risk mappings
            if not relationship_type or relationship_type == "question_risk":
                cursor.execute(
                    """
                    SELECT question_id as source_id, risk_id as target_id,
                           'question_risk' as relationship_type
                    FROM question_risk_mapping
                    LIMIT ?
                """,
                    (limit,),
                )
                relationships.extend(
                    [
                        Relationship(
                            source_id=row["source_id"],
                            target_id=row["target_id"],
                            relationship_type=row["relationship_type"],
                        )
                        for row in cursor.fetchall()
                    ]
                )

            # Question-Control mappings
            if not relationship_type or relationship_type == "question_control":
                cursor.execute(
                    """
                    SELECT question_id as source_id, control_id as target_id,
                           'question_control' as relationship_type
                    FROM question_control_mapping
                    LIMIT ?
                """,
                    (limit,),
                )
                relationships.extend(
                    [
                        Relationship(
                            source_id=row["source_id"],
                            target_id=row["target_id"],
                            relationship_type=row["relationship_type"],
                        )
                        for row in cursor.fetchall()
                    ]
                )

            return relationships[:limit]

    except Exception as e:
        logger.error(f"Error fetching relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2, max_length=100), limit: int = Query(None, ge=1)):
    """Search across all entities."""
    try:
        # Validate and sanitize search input
        if not q or len(q.strip()) < 2:
            raise HTTPException(status_code=400, detail="Search query must be at least 2 characters")

        # Sanitize search term - remove potentially dangerous characters
        import re

        sanitized_q = re.sub(r"[^\w\s\-\.]", "", q.strip())
        if not sanitized_q:
            raise HTTPException(status_code=400, detail="Invalid search query")

        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("search_limit", 50)

        max_limit = api_config.get("limits", {}).get("search_limit", 200)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            search_term = f"%{sanitized_q}%"
            results = []

            # Search risks
            cursor.execute(
                """
                SELECT 'risk' as type, risk_id as id, risk_title as title,
                       risk_description as description
                FROM risks
                WHERE risk_title LIKE ? OR risk_description LIKE ?
                LIMIT ?
            """,
                (search_term, search_term, limit),
            )
            results.extend(
                [
                    {
                        "type": row["type"],
                        "id": row["id"],
                        "title": row["title"],
                        "description": row["description"],
                    }
                    for row in cursor.fetchall()
                ]
            )

            # Search controls
            cursor.execute(
                """
                SELECT 'control' as type, control_id as id, control_title as title,
                       control_description as description
                FROM controls
                WHERE control_title LIKE ? OR control_description LIKE ?
                LIMIT ?
            """,
                (search_term, search_term, limit),
            )
            results.extend(
                [
                    {
                        "type": row["type"],
                        "id": row["id"],
                        "title": row["title"],
                        "description": row["description"],
                    }
                    for row in cursor.fetchall()
                ]
            )

            # Search questions
            cursor.execute(
                """
                SELECT 'question' as type, question_id as id, question_text as title,
                       '' as description
                FROM questions
                WHERE question_text LIKE ?
                LIMIT ?
            """,
                (search_term, limit),
            )
            results.extend(
                [
                    {
                        "type": row["type"],
                        "id": row["id"],
                        "title": row["title"],
                        "description": row["description"],
                    }
                    for row in cursor.fetchall()
                ]
            )

            # Search definitions
            cursor.execute(
                """
                SELECT 'definition' as type, definition_id as id, term as title,
                       description, category, source
                FROM definitions
                WHERE term LIKE ? OR description LIKE ? OR category LIKE ?
                LIMIT ?
            """,
                (search_term, search_term, search_term, limit),
            )
            results.extend(
                [
                    {
                        "type": row["type"],
                        "id": row["id"],
                        "title": row["title"],
                        "description": row["description"],
                        "category": row["category"],
                        "source": row["source"],
                    }
                    for row in cursor.fetchall()
                ]
            )

            return {"query": q, "results": results[:limit]}

    except Exception as e:
        logger.error(f"Error searching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats", response_model=DatabaseStats)
async def get_stats():
    """Get database statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Count records
            cursor.execute("SELECT COUNT(*) FROM risks")
            total_risks = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM controls")
            total_controls = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM questions")
            total_questions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM definitions")
            total_definitions = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM capabilities")
            total_capabilities = cursor.fetchone()[0]

            # Count relationships
            cursor.execute("SELECT COUNT(*) FROM risk_control_mapping")
            risk_control_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM question_risk_mapping")
            question_risk_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM question_control_mapping")
            question_control_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM capability_control_mapping")
            capability_control_count = cursor.fetchone()[0]

            total_relationships = (
                risk_control_count + question_risk_count + question_control_count + capability_control_count
            )

            return DatabaseStats(
                total_risks=total_risks,
                total_controls=total_controls,
                total_questions=total_questions,
                total_definitions=total_definitions,
                total_capabilities=total_capabilities,
                total_relationships=total_relationships,
                database_version=None,  # Could be added to database metadata
            )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risks/summary")
async def get_risks_summary():
    """Get risks with control and question counts for dashboard tables."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get risks with counts - simplified approach
            cursor.execute(
                """
                SELECT
                    r.risk_id,
                    r.risk_title,
                    r.risk_description,
                    COALESCE(rc_count.control_count, 0) as control_count,
                    COALESCE(qr_count.question_count, 0) as question_count
                FROM risks r
                LEFT JOIN (
                    SELECT risk_id, COUNT(*) as control_count
                    FROM risk_control_mapping
                    GROUP BY risk_id
                ) rc_count ON r.risk_id = rc_count.risk_id
                LEFT JOIN (
                    SELECT risk_id, COUNT(*) as question_count
                    FROM question_risk_mapping
                    GROUP BY risk_id
                ) qr_count ON r.risk_id = qr_count.risk_id
                ORDER BY r.risk_id
            """
            )

            risks = []
            for row in cursor.fetchall():
                risks.append(
                    {
                        "risk_id": row["risk_id"],
                        "risk_title": row["risk_title"],
                        "risk_description": row["risk_description"],
                        "control_count": row["control_count"],
                        "question_count": row["question_count"],
                    }
                )

            return {"details": risks}

    except Exception as e:
        logger.error(f"Error fetching risks summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/controls/summary")
async def get_controls_summary():
    """Get controls with risk and question counts for dashboard tables."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get controls with counts
            cursor.execute(
                """
                SELECT
                    c.control_id,
                    c.control_title,
                    c.control_description,
                    c.control_type,
                    c.security_function,
                    c.maturity_level,
                    COALESCE(rc_count.risk_count, 0) as risk_count,
                    COALESCE(qc_count.question_count, 0) as question_count
                FROM controls c
                LEFT JOIN (
                    SELECT control_id, COUNT(*) as risk_count
                    FROM risk_control_mapping
                    GROUP BY control_id
                ) rc_count ON c.control_id = rc_count.control_id
                LEFT JOIN (
                    SELECT control_id, COUNT(*) as question_count
                    FROM question_control_mapping
                    GROUP BY control_id
                ) qc_count ON c.control_id = qc_count.control_id
                ORDER BY c.control_id
            """
            )

            controls = []
            for row in cursor.fetchall():
                controls.append(
                    {
                        "control_id": row["control_id"],
                        "control_title": row["control_title"],
                        "control_description": row["control_description"],
                        "control_type": row["control_type"],
                        "security_function": row["security_function"],
                        "maturity_level": row["maturity_level"],
                        "risk_count": row["risk_count"],
                        "question_count": row["question_count"],
                    }
                )

            return {"details": controls}

    except Exception as e:
        logger.error(f"Error fetching controls summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/questions/summary")
async def get_questions_summary():
    """Get questions with risk and control counts for dashboard tables."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get questions with counts - simplified approach
            cursor.execute(
                """
                SELECT
                    q.question_id,
                    q.question_text,
                    q.category,
                    q.topic,
                    q.managing_role,
                    COALESCE(qr_count.risk_count, 0) as risk_count,
                    COALESCE(qc_count.control_count, 0) as control_count
                FROM questions q
                LEFT JOIN (
                    SELECT question_id, COUNT(*) as risk_count
                    FROM question_risk_mapping
                    GROUP BY question_id
                ) qr_count ON q.question_id = qr_count.question_id
                LEFT JOIN (
                    SELECT question_id, COUNT(*) as control_count
                    FROM question_control_mapping
                    GROUP BY question_id
                ) qc_count ON q.question_id = qc_count.question_id
                ORDER BY q.question_id
            """
            )

            questions = []
            for row in cursor.fetchall():
                questions.append(
                    {
                        "question_id": row["question_id"],
                        "question_text": row["question_text"],
                        "category": row["category"],
                        "topic": row["topic"],
                        "managing_role": row["managing_role"],
                        "risk_count": row["risk_count"],
                        "control_count": row["control_count"],
                    }
                )

            # Calculate summary statistics
            total_questions = len(questions)
            mapped_questions = len([q for q in questions if q["risk_count"] > 0 or q["control_count"] > 0])

            return {
                "summary": {
                    "total_questions": total_questions,
                    "mapped_questions": mapped_questions,
                    "unmapped_questions": total_questions - mapped_questions,
                },
                "details": questions,
            }

    except Exception as e:
        logger.error(f"Error fetching questions summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/risk/{risk_id}")
async def get_risk_detail(risk_id: str):
    """Get detailed information for a specific risk."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get risk details
            cursor.execute(
                """
                SELECT risk_id as id, risk_title as title,
                       risk_description as description
                FROM risks
                WHERE risk_id = ?
            """,
                (risk_id,),
            )

            risk_row = cursor.fetchone()
            if not risk_row:
                raise HTTPException(status_code=404, detail="Risk not found")

            risk = {
                "id": risk_row["id"],
                "title": risk_row["title"],
                "description": risk_row["description"],
            }

            # Get associated controls
            cursor.execute(
                """
                SELECT c.control_id as id, c.control_title as title,
                       c.control_description as description,
                       c.security_function as domain,
                       c.control_type as control_type,
                       c.maturity_level as maturity_level
                FROM controls c
                JOIN risk_control_mapping rcm ON c.control_id = rcm.control_id
                WHERE rcm.risk_id = ?
                ORDER BY c.control_id
            """,
                (risk_id,),
            )

            associated_controls = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "domain": row["domain"],
                    "type": row["control_type"],
                    "maturity": row["maturity_level"],
                }
                for row in cursor.fetchall()
            ]

            # Get associated questions
            cursor.execute(
                """
                SELECT q.question_id as id, q.question_text as text, q.category, q.topic
                FROM questions q
                JOIN question_risk_mapping qrm ON q.question_id = qrm.question_id
                WHERE qrm.risk_id = ?
                ORDER BY q.question_id
            """,
                (risk_id,),
            )

            associated_questions = [
                {
                    "id": row["id"],
                    "text": row["text"],
                    "category": row["category"],
                    "topic": row["topic"],
                }
                for row in cursor.fetchall()
            ]

            return {
                "risk": risk,
                "associated_controls": associated_controls,
                "associated_questions": associated_questions,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching risk detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/control/{control_id}")
async def get_control_detail(control_id: str):
    """Get detailed information for a specific control."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get control details
            cursor.execute(
                """
                SELECT control_id as id, control_title as title,
                       control_description as description,
                       security_function as domain,
                       control_type as control_type,
                       maturity_level as maturity_level,
                       asset_type as asset_type
                FROM controls
                WHERE control_id = ?
            """,
                (control_id,),
            )

            control_row = cursor.fetchone()
            if not control_row:
                raise HTTPException(status_code=404, detail="Control not found")

            control = {
                "id": control_row["id"],
                "title": control_row["title"],
                "description": control_row["description"],
                "domain": control_row["domain"],
                "type": control_row["control_type"],
                "maturity": control_row["maturity_level"],
                "asset_type": control_row["asset_type"],
            }

            # Get associated risks
            cursor.execute(
                """
                SELECT r.risk_id as id, r.risk_title as title,
                       r.risk_description as description
                FROM risks r
                JOIN risk_control_mapping rcm ON r.risk_id = rcm.risk_id
                WHERE rcm.control_id = ?
                ORDER BY r.risk_id
            """,
                (control_id,),
            )

            associated_risks = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                }
                for row in cursor.fetchall()
            ]

            # Get associated questions
            cursor.execute(
                """
                SELECT q.question_id as id, q.question_text as text, q.category, q.topic
                FROM questions q
                JOIN question_control_mapping qcm ON q.question_id = qcm.question_id
                WHERE qcm.control_id = ?
                ORDER BY q.question_id
            """,
                (control_id,),
            )

            associated_questions = [
                {
                    "id": row["id"],
                    "text": row["text"],
                    "category": row["category"],
                    "topic": row["topic"],
                }
                for row in cursor.fetchall()
            ]

            # Get associated parent capabilities
            cursor.execute(
                """
                SELECT c.capability_id as id, c.capability_name as name,
                       c.capability_type as type, c.capability_domain as domain,
                       c.capability_definition as definition
                FROM capabilities c
                JOIN capability_control_mapping ccm ON c.capability_id = ccm.capability_id
                WHERE ccm.control_id = ?
                ORDER BY c.capability_type, c.capability_name
            """,
                (control_id,),
            )

            associated_capabilities = [
                {
                    "id": row["id"],
                    "name": row["name"],
                    "type": row["type"],
                    "domain": row["domain"],
                    "definition": row["definition"],
                }
                for row in cursor.fetchall()
            ]

            return {
                "control": control,
                "associated_risks": associated_risks,
                "associated_questions": associated_questions,
                "associated_capabilities": associated_capabilities,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching control detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/question/{question_id}")
async def get_question_detail(question_id: str):
    """Get detailed information for a specific question."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get question details
            cursor.execute(
                """
                SELECT question_id as id, question_text as text, category, topic,
                       managing_role
                FROM questions
                WHERE question_id = ?
            """,
                (question_id,),
            )

            question_row = cursor.fetchone()
            if not question_row:
                raise HTTPException(status_code=404, detail="Question not found")

            question = {
                "id": question_row["id"],
                "text": question_row["text"],
                "category": question_row["category"],
                "topic": question_row["topic"],
                "managing_role": question_row["managing_role"],
            }

            # Get managing roles for this question (supporting multiple roles)
            cursor.execute(
                """
                SELECT DISTINCT managing_role
                FROM questions
                WHERE question_id = ? AND managing_role IS NOT NULL
                AND managing_role != ''
            """,
                (question_id,),
            )

            managing_roles = [row["managing_role"] for row in cursor.fetchall()]

            # Get associated risks
            cursor.execute(
                """
                SELECT r.risk_id as id, r.risk_title as title,
                       r.risk_description as description
                FROM risks r
                JOIN question_risk_mapping qrm ON r.risk_id = qrm.risk_id
                WHERE qrm.question_id = ?
                ORDER BY r.risk_id
            """,
                (question_id,),
            )

            associated_risks = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                }
                for row in cursor.fetchall()
            ]

            # Get associated controls
            cursor.execute(
                """
                SELECT c.control_id as id, c.control_title as title,
                       c.control_description as description,
                       c.security_function as domain,
                       c.control_type as control_type,
                       c.maturity_level as maturity_level
                FROM controls c
                JOIN question_control_mapping qcm ON c.control_id = qcm.control_id
                WHERE qcm.question_id = ?
                ORDER BY c.control_id
            """,
                (question_id,),
            )

            associated_controls = [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "description": row["description"],
                    "domain": row["domain"],
                    "control_type": row["control_type"],
                    "maturity_level": row["maturity_level"],
                }
                for row in cursor.fetchall()
            ]

            return {
                "question": question,
                "managing_roles": managing_roles,
                "associated_risks": associated_risks,
                "associated_controls": associated_controls,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching question detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/managing-roles")
async def get_managing_roles():
    """Get distinct managing roles from questions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT DISTINCT managing_role
                FROM questions
                WHERE managing_role IS NOT NULL AND managing_role != ''
                ORDER BY managing_role
            """
            )

            roles = [row["managing_role"] for row in cursor.fetchall()]

            return {"managing_roles": roles}

    except Exception as e:
        logger.error(f"Error getting managing roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/file-metadata")
async def get_file_metadata():
    """Get file metadata including versions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT data_type, version, filename, file_modified_time
                FROM file_metadata
                ORDER BY data_type
            """
            )

            rows = cursor.fetchall()

            metadata = {}
            for row in rows:
                data_type = row["data_type"]
                metadata[data_type] = {
                    "version": row["version"],
                    "filename": row["filename"],
                    "file_modified_time": row["file_modified_time"],
                }

            return metadata

    except Exception as e:
        logger.error(f"Error getting file metadata: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/network")
async def get_network_data():
    """Get network data for relationship visualization."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get risk-control relationships
            cursor.execute(
                """
                SELECT risk_id as source_id, control_id as target_id,
                       'risk_control' as relationship_type
                FROM risk_control_mapping
            """
            )
            risk_control_links = [dict(row) for row in cursor.fetchall()]

            # Get question-risk relationships
            cursor.execute(
                """
                SELECT question_id as source_id, risk_id as target_id,
                       'question_risk' as relationship_type
                FROM question_risk_mapping
            """
            )
            question_risk_links = [dict(row) for row in cursor.fetchall()]

            # Get question-control relationships
            cursor.execute(
                """
                SELECT question_id as source_id, control_id as target_id,
                       'question_control' as relationship_type
                FROM question_control_mapping
            """
            )
            question_control_links = [dict(row) for row in cursor.fetchall()]

            return {
                "risk_control_links": risk_control_links,
                "question_risk_links": question_risk_links,
                "question_control_links": question_control_links,
            }

    except Exception as e:
        logger.error(f"Error fetching network data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/gaps")
async def get_gaps_analysis():
    """Get critical gaps analysis - unmapped risks, controls, and questions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all entities
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT control_id, control_title, control_description FROM controls")
            all_controls = [dict(row) for row in cursor.fetchall()]

            cursor.execute("SELECT question_id, question_text, category FROM questions")
            all_questions = [dict(row) for row in cursor.fetchall()]

            # Get mapped entities
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risk_ids = {row["risk_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_control_ids = {row["control_id"] for row in cursor.fetchall()}

            cursor.execute("SELECT DISTINCT question_id FROM question_risk_mapping")
            mapped_question_ids = {row["question_id"] for row in cursor.fetchall()}

            # Add question-control mappings to mapped entities
            cursor.execute("SELECT DISTINCT control_id FROM question_control_mapping")
            mapped_control_ids.update({row["control_id"] for row in cursor.fetchall()})

            cursor.execute("SELECT DISTINCT question_id FROM question_control_mapping")
            mapped_question_ids.update({row["question_id"] for row in cursor.fetchall()})

            # Find unmapped entities
            unmapped_risks = [r for r in all_risks if r["risk_id"] not in mapped_risk_ids]
            unmapped_controls = [c for c in all_controls if c["control_id"] not in mapped_control_ids]
            unmapped_questions = [q for q in all_questions if q["question_id"] not in mapped_question_ids]

            # Find risks without questions (risks not addressed by any questions)
            cursor.execute("SELECT DISTINCT risk_id FROM question_risk_mapping")
            risks_with_questions = {row["risk_id"] for row in cursor.fetchall()}
            risks_without_questions = [r for r in all_risks if r["risk_id"] not in risks_with_questions]

            # Find controls without questions (controls not addressed by any questions)
            cursor.execute("SELECT DISTINCT control_id FROM question_control_mapping")
            controls_with_questions = {row["control_id"] for row in cursor.fetchall()}
            controls_without_questions = [c for c in all_controls if c["control_id"] not in controls_with_questions]

            # Calculate coverage percentages
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            total_questions = len(all_questions)

            risk_coverage_pct = ((total_risks - len(unmapped_risks)) / total_risks * 100) if total_risks > 0 else 0
            control_coverage_pct = (
                ((total_controls - len(unmapped_controls)) / total_controls * 100) if total_controls > 0 else 0
            )
            question_coverage_pct = (
                ((total_questions - len(unmapped_questions)) / total_questions * 100) if total_questions > 0 else 0
            )

            # Calculate risks without questions percentage
            risks_without_questions_pct = (len(risks_without_questions) / total_risks * 100) if total_risks > 0 else 0

            # Calculate controls without questions percentage
            controls_without_questions_pct = (
                (len(controls_without_questions) / total_controls * 100) if total_controls > 0 else 0
            )

            return {
                "summary": {
                    "total_risks": total_risks,
                    "total_controls": total_controls,
                    "total_questions": total_questions,
                    "mapped_risks": total_risks - len(unmapped_risks),
                    "mapped_controls": total_controls - len(unmapped_controls),
                    "mapped_questions": total_questions - len(unmapped_questions),
                    "unmapped_risks": len(unmapped_risks),
                    "unmapped_controls": len(unmapped_controls),
                    "unmapped_questions": len(unmapped_questions),
                    "risks_without_questions": len(risks_without_questions),
                    "controls_without_questions": len(controls_without_questions),
                    "risk_coverage_pct": round(risk_coverage_pct, 1),
                    "control_coverage_pct": round(control_coverage_pct, 1),
                    "question_coverage_pct": round(question_coverage_pct, 1),
                    "risks_without_questions_pct": round(risks_without_questions_pct, 1),
                    "controls_without_questions_pct": round(controls_without_questions_pct, 1),
                    "control_utilization_pct": round(control_coverage_pct, 1),  # Same as coverage for controls
                },
                "unmapped_risks": unmapped_risks,
                "unmapped_controls": unmapped_controls,
                "unmapped_questions": unmapped_questions,
                "risks_without_questions": risks_without_questions,
                "controls_without_questions": controls_without_questions,
            }

    except Exception as e:
        logger.error(f"Error fetching gaps data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/last-updated")
async def get_last_updated():
    """Get last updated timestamps and file versions."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT data_type, version, file_modified_time
                FROM file_metadata
                ORDER BY data_type
            """
            )

            rows = cursor.fetchall()

            metadata = {}
            for row in rows:
                data_type = row["data_type"]
                metadata[data_type] = {
                    "version": row["version"],
                    "file_modified_time": row["file_modified_time"],
                }

            return {
                "risks": {
                    "last_updated": metadata.get("risks", {}).get("file_modified_time", "2025-09-24T20:00:00Z"),
                    "version": metadata.get("risks", {}).get("version", "unknown"),
                },
                "controls": {
                    "last_updated": metadata.get("controls", {}).get("file_modified_time", "2025-09-24T20:00:00Z"),
                    "version": metadata.get("controls", {}).get("version", "unknown"),
                },
                "questions": {
                    "last_updated": metadata.get("questions", {}).get("file_modified_time", "2025-09-24T20:00:00Z"),
                    "version": metadata.get("questions", {}).get("version", "unknown"),
                },
                "definitions": {
                    "last_updated": metadata.get("definitions", {}).get("file_modified_time", "2025-09-24T20:00:00Z"),
                    "version": metadata.get("definitions", {}).get("version", "unknown"),
                },
            }

    except Exception as e:
        logger.error(f"Error getting last updated data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capabilities", response_model=List[Capability])
async def get_capabilities(
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
    capability_type: Optional[str] = None,
    domain: Optional[str] = None,
):
    """Get all capabilities with optional filtering."""
    try:
        # Use config limits if not provided
        if limit is None:
            limit = api_config.get("limits", {}).get("default_limit", 100)

        max_limit = api_config.get("limits", {}).get("max_limit", 1000)
        limit = min(limit, max_limit)

        with get_db_connection() as conn:
            cursor = conn.cursor()

            query = (
                "SELECT capability_id, capability_name, capability_type, "
                "capability_domain, capability_definition, candidate_products, notes "
                "FROM capabilities"
            )
            params = []
            conditions = []

            if capability_type:
                conditions.append("capability_type = ?")
                params.append(capability_type)

            if domain:
                conditions.append("capability_domain = ?")
                params.append(domain)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY capability_id LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Capability(
                    capability_id=row["capability_id"],
                    capability_name=row["capability_name"],
                    capability_type=row["capability_type"],
                    capability_domain=row["capability_domain"],
                    capability_definition=row["capability_definition"],
                    candidate_products=row["candidate_products"],
                    notes=row["notes"],
                )
                for row in rows
            ]

    except Exception as e:
        logger.error(f"Error fetching capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capabilities/{capability_id}", response_model=Capability)
async def get_capability(capability_id: str):
    """Get a specific capability by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT capability_id, capability_name, capability_type,
                       capability_domain, capability_definition, candidate_products, notes
                FROM capabilities
                WHERE capability_id = ?
                """,
                (capability_id,),
            )

            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Capability not found")

            return Capability(
                capability_id=row["capability_id"],
                capability_name=row["capability_name"],
                capability_type=row["capability_type"],
                capability_domain=row["capability_domain"],
                capability_definition=row["capability_definition"],
                candidate_products=row["candidate_products"],
                notes=row["notes"],
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching capability {capability_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capability-tree", response_model=List[CapabilityTree])
async def get_capability_tree():
    """Get hierarchical capability tree with controls and risks."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get all capabilities with their controls and associated risks
            # Use COALESCE to handle NULL values from GROUP_CONCAT
            # IMPORTANT: Use ccm.control_id instead of ctrl.control_id to include mapped controls
            # even if they don't exist in the controls table (data integrity issue)
            cursor.execute(
                """
                SELECT
                    c.capability_id,
                    c.capability_name,
                    c.capability_type,
                    c.capability_domain,
                    c.capability_definition,
                    c.candidate_products,
                    c.notes,
                    COALESCE(GROUP_CONCAT(DISTINCT ccm.control_id), '') as control_ids,
                    COALESCE(GROUP_CONCAT(DISTINCT ctrl.control_title), '') as control_titles,
                    COALESCE(GROUP_CONCAT(DISTINCT ctrl.security_function), '') as control_domains,
                    COALESCE(GROUP_CONCAT(DISTINCT r.risk_id), '') as risk_ids,
                    COALESCE(GROUP_CONCAT(DISTINCT r.risk_title), '') as risk_titles
                FROM capabilities c
                LEFT JOIN capability_control_mapping ccm ON c.capability_id = ccm.capability_id
                LEFT JOIN controls ctrl ON ccm.control_id = ctrl.control_id
                LEFT JOIN risk_control_mapping rcm ON ccm.control_id = rcm.control_id
                LEFT JOIN risks r ON rcm.risk_id = r.risk_id
                GROUP BY c.capability_id, c.capability_name, c.capability_type, c.capability_domain,
                         c.capability_definition, c.candidate_products, c.notes
                ORDER BY c.capability_type, c.capability_domain, c.capability_name
                """
            )

            rows = cursor.fetchall()
            logger.info(f"Capability tree query returned {len(rows)} rows")
            capability_trees = []

            for row in rows:
                # Parse control data - handle empty strings and NULL values
                # sqlite3.Row uses dictionary-style access - handle None values from COALESCE
                controls = []
                control_ids_str = row["control_ids"] or ""
                if control_ids_str and control_ids_str.strip():
                    control_ids = [cid.strip() for cid in control_ids_str.split(",") if cid.strip()]
                    control_titles_str = row["control_titles"] or ""
                    control_titles = (
                        [ct.strip() for ct in control_titles_str.split(",") if ct.strip()] if control_titles_str else []
                    )
                    control_domains_str = row["control_domains"] or ""
                    control_domains = (
                        [cd.strip() for cd in control_domains_str.split(",") if cd.strip()]
                        if control_domains_str
                        else []
                    )

                    # Create a map of control_id to title/domain for easier lookup
                    # Some controls may not exist in controls table, so titles/domains may be missing
                    control_title_map = {}
                    control_domain_map = {}
                    for idx, title in enumerate(control_titles):
                        if idx < len(control_ids):
                            control_title_map[control_ids[idx]] = title
                    for idx, domain in enumerate(control_domains):
                        if idx < len(control_ids):
                            control_domain_map[control_ids[idx]] = domain

                    for control_id in control_ids:
                        controls.append(
                            {
                                "control_id": control_id,
                                "control_title": control_title_map.get(
                                    control_id, control_id
                                ),  # Use control_id as fallback title
                                "control_domain": control_domain_map.get(control_id, ""),
                            }
                        )

                # Parse risk data - handle empty strings and NULL values
                risks = []
                risk_ids_str = row["risk_ids"] or ""
                if risk_ids_str and risk_ids_str.strip():
                    risk_ids = [rid.strip() for rid in risk_ids_str.split(",") if rid.strip()]
                    risk_titles_str = row["risk_titles"] or ""
                    risk_titles = (
                        [rt.strip() for rt in risk_titles_str.split(",") if rt.strip()] if risk_titles_str else []
                    )

                    for i, risk_id in enumerate(risk_ids):
                        risks.append(
                            {
                                "risk_id": risk_id,
                                "risk_title": (risk_titles[i] if i < len(risk_titles) else ""),
                            }
                        )

                # Log non-technical capabilities with 0 controls/risks for debugging
                if row["capability_type"] == "non-technical" and len(controls) == 0 and len(risks) == 0:
                    logger.debug(
                        f"Non-technical capability {row['capability_id']} ({row['capability_name']}) "
                        f"has 0 controls and 0 risks. Control IDs from DB: '{control_ids_str}'"
                    )

                capability_trees.append(
                    CapabilityTree(
                        capability_id=row["capability_id"],
                        capability_name=row["capability_name"],
                        capability_type=row["capability_type"],
                        capability_domain=row["capability_domain"],
                        capability_definition=row["capability_definition"],
                        controls=controls,
                        risks=risks,
                    )
                )

            logger.info(f"Returning {len(capability_trees)} capability trees (with controls and risks)")
            if len(capability_trees) == 0:
                logger.warning("No capability trees returned - database may be empty or query returned no results")

            return capability_trees

    except Exception as e:
        logger.error(f"Error fetching capability tree: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

    # Capability Configuration API Endpoints
    # NOTE: These endpoints are now handled by the router in api/capability_scenarios.py
    # The router includes support for control selections. These direct endpoints are kept
    # for backward compatibility but may be removed in the future.

    # Commented out - now handled by router in api/capability_scenarios.py
    # @app.get("/api/capability-scenarios")
    # async def get_capability_scenarios(user_id: int = Query(...)):
    #     """Get all scenarios for a specific user."""
    #     # Implementation moved to router


# Commented out - now handled by router in api/capability_scenarios.py
# @app.post("/api/capability-scenarios")
# async def create_capability_scenario(scenario: CapabilityScenario):
#     """Create a new capability scenario."""
#     # Implementation moved to router


# Commented out - now handled by router
# Commented out - now handled by router in api/capability_scenarios.py
# @app.get("/api/capability-scenarios/{scenario_id}")
# async def get_capability_scenario(scenario_id: int):
#     """Get a specific scenario with all its selections."""
#     # Implementation moved to router


# Commented out - now handled by router in api/capability_scenarios.py
# @app.put("/api/capability-scenarios/{scenario_id}")
# async def update_capability_scenario(scenario_id: int, scenario: CapabilityScenarioUpdate):
#     """Update a scenario's name or default status."""
#     # Implementation moved to router


# Commented out - now handled by router in api/capability_scenarios.py
# @app.delete("/api/capability-scenarios/{scenario_id}")
# async def delete_capability_scenario(scenario_id: int):
#     """Delete a scenario and all its selections."""
#     # Implementation moved to router


# Commented out - now handled by router in api/capability_scenarios.py
# @app.post("/api/capability-selections")
# async def save_capability_selections(bulk: CapabilitySelectionsBulk):
#     """Bulk save capability selections for a scenario."""
#     # Implementation moved to router


# Commented out - now handled by router in api/capability_scenarios.py
# @app.get("/api/capability-selections/{scenario_id}")
# async def get_capability_selections(scenario_id: int):
#     """Get all selections for a scenario."""
#     # Implementation moved to router


# @app.post("/api/capability-analysis", response_model=CapabilityAnalysisResponse)
async def analyze_capabilities(request: CapabilityAnalysisRequest):
    """Calculate metrics based on active capabilities."""
    try:
        logger.info(
            f"🔍 API analyze_capabilities called with {len(request.capability_ids)} capability_ids: {request.capability_ids[:10]}..."
        )
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get total counts from main database
            cursor.execute("SELECT COUNT(*) as count FROM controls")
            total_controls = cursor.fetchone()["count"]

            cursor.execute("SELECT COUNT(*) as count FROM risks")
            total_risks = cursor.fetchone()["count"]

            # Get all controls that belong to any capability
            cursor.execute(
                """
                SELECT DISTINCT control_id
                FROM capability_control_mapping
            """
            )
            controls_in_capabilities = cursor.fetchall()
            controls_in_capabilities_count = len(controls_in_capabilities)

            # If no capabilities are active, return zeros for active metrics
            if not request.capability_ids:
                # All risks are exposed if no controls are active
                cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
                exposed_risks_list = [
                    {
                        "risk_id": row["risk_id"],
                        "risk_title": row["risk_title"],
                        "risk_description": row["risk_description"],
                        "required_controls": [],
                        "total_controls": 0,
                    }
                    for row in cursor.fetchall()
                ]

                return CapabilityAnalysisResponse(
                    total_controls=total_controls,
                    controls_in_capabilities=controls_in_capabilities_count,
                    active_controls=0,
                    exposed_risks=total_risks,
                    total_risks=total_risks,
                    active_risks=0,
                    partially_covered_risks=0,
                    active_controls_list=[],
                    partially_covered_risks_list=[],
                    exposed_risks_list=exposed_risks_list,
                )

            # Get controls from active capabilities
            logger.info(f"🔍 Querying controls for {len(request.capability_ids)} capabilities")
            placeholders = ",".join("?" * len(request.capability_ids))
            cursor.execute(
                f"""
                SELECT DISTINCT control_id
                FROM capability_control_mapping
                WHERE capability_id IN ({placeholders})
            """,
                request.capability_ids,
            )

            active_control_ids = [row["control_id"] for row in cursor.fetchall()]
            active_controls_count = len(active_control_ids)
            logger.info(
                f"🔍 Found {active_controls_count} active controls from {len(request.capability_ids)} capabilities"
            )

            # Get detailed active controls list
            active_controls_list = []
            if active_control_ids:
                placeholders = ",".join("?" * len(active_control_ids))
                cursor.execute(
                    f"""
                    SELECT DISTINCT c.control_id, c.control_description,
                           GROUP_CONCAT(DISTINCT cap.capability_name) as capability_names
                    FROM controls c
                    JOIN capability_control_mapping ccm ON c.control_id = ccm.control_id
                    JOIN capabilities cap ON ccm.capability_id = cap.capability_id
                    WHERE c.control_id IN ({placeholders})
                    GROUP BY c.control_id, c.control_description
                """,
                    active_control_ids,
                )

                for row in cursor.fetchall():
                    active_controls_list.append(
                        {
                            "control_id": row["control_id"],
                            "control_description": row["control_description"],
                            "capability_names": (row["capability_names"].split(",") if row["capability_names"] else []),
                        }
                    )

            # Get risks covered by active controls - FIXED LOGIC
            # CRITICAL FIX: Handle ALL risks, including those without controls mapped
            # Risks without any controls should always be considered exposed

            # Get all risks first
            cursor.execute("SELECT risk_id FROM risks")
            all_risks = {row["risk_id"] for row in cursor.fetchall()}

            if active_control_ids:
                # Get risks that have controls mapped
                cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
                risks_with_controls = {row["risk_id"] for row in cursor.fetchall()}

                # Risks without controls are always exposed
                risks_without_controls = all_risks - risks_with_controls

                fully_covered_risks = []
                partially_covered_risks = []
                partially_covered_details = []
                exposed_risks_list = []

                # Add risks without controls to exposed risks list
                for risk_id in risks_without_controls:
                    cursor.execute(
                        "SELECT risk_title, risk_description FROM risks WHERE risk_id = ?",
                        (risk_id,),
                    )
                    risk_row = cursor.fetchone()
                    risk_title = risk_row["risk_title"] if risk_row and risk_row["risk_title"] else "No title"
                    risk_description = (
                        risk_row["risk_description"] if risk_row and risk_row["risk_description"] else "No description"
                    )
                    exposed_risks_list.append(
                        {
                            "risk_id": risk_id,
                            "risk_title": risk_title,
                            "risk_description": risk_description,
                            "required_controls": [],
                            "total_controls": 0,
                        }
                    )

                # For each risk with controls, check if ALL its required controls are active
                for risk_id in risks_with_controls:

                    # Get risk details
                    cursor.execute(
                        "SELECT risk_title, risk_description FROM risks WHERE risk_id = ?",
                        (risk_id,),
                    )
                    risk_row = cursor.fetchone()
                    risk_title = risk_row["risk_title"] if risk_row and risk_row["risk_title"] else "No title"
                    risk_description = (
                        risk_row["risk_description"] if risk_row and risk_row["risk_description"] else "No description"
                    )

                    # Get all controls required for this risk
                    cursor.execute(
                        """
                        SELECT control_id
                        FROM risk_control_mapping
                        WHERE risk_id = ?
                    """,
                        (risk_id,),
                    )
                    required_controls = {row["control_id"] for row in cursor.fetchall()}

                    # Check how many required controls are active
                    active_required = required_controls.intersection(set(active_control_ids))

                    if len(active_required) == len(required_controls):
                        # All required controls are active
                        fully_covered_risks.append(risk_id)
                    elif len(active_required) > 0:
                        # Some but not all required controls are active
                        partially_covered_risks.append(risk_id)
                        partially_covered_details.append(
                            {
                                "risk_id": risk_id,
                                "risk_title": risk_title,
                                "risk_description": risk_description,
                                "active_controls": list(active_required),
                                "inactive_controls": list(required_controls - active_required),
                                "total_controls": len(required_controls),
                            }
                        )
                    else:
                        # No required controls are active - exposed risk
                        exposed_risks_list.append(
                            {
                                "risk_id": risk_id,
                                "risk_title": risk_title,
                                "risk_description": risk_description,
                                "required_controls": list(required_controls),
                                "total_controls": len(required_controls),
                            }
                        )

                fully_covered_count = len(fully_covered_risks)
                partially_covered_count = len(partially_covered_risks)
            else:
                # No active controls - all risks are exposed
                fully_covered_count = 0
                partially_covered_count = 0
                partially_covered_details = []
                exposed_risks_list = []

                # Get all risks and add them to exposed list
                cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
                for row in cursor.fetchall():
                    exposed_risks_list.append(
                        {
                            "risk_id": row["risk_id"],
                            "risk_title": row["risk_title"] or "No title",
                            "risk_description": row["risk_description"] or "No description",
                            "required_controls": [],
                            "total_controls": 0,
                        }
                    )

            # Exposed risks = total - fully covered - partially covered
            exposed_risks = total_risks - fully_covered_count - partially_covered_count

            logger.info(
                f"📊 Final metrics: active_controls={active_controls_count}, exposed_risks={exposed_risks}, partially_covered={partially_covered_count}, fully_covered={fully_covered_count}"
            )

            return CapabilityAnalysisResponse(
                total_controls=total_controls,
                controls_in_capabilities=controls_in_capabilities_count,
                active_controls=active_controls_count,
                exposed_risks=exposed_risks,
                total_risks=total_risks,
                active_risks=fully_covered_count,
                partially_covered_risks=partially_covered_count,
                active_controls_list=active_controls_list,
                partially_covered_risks_list=partially_covered_details,
                exposed_risks_list=exposed_risks_list,
            )
    except Exception as e:
        logger.error(f"Error analyzing capabilities: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/controls/mapped")
async def get_mapped_control_ids():
    """Get list of control IDs that are mapped to capabilities."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT control_id
                FROM capability_control_mapping
                ORDER BY control_id
                """
            )
            mapped_control_ids = [row["control_id"] for row in cursor.fetchall()]
            return {"mapped_control_ids": mapped_control_ids}
    except Exception as e:
        logger.error(f"Error fetching mapped control IDs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/capability-unique-controls")
async def get_capability_unique_controls():
    """
    Identify capabilities that have unique controls (controls not shared with other capabilities).
    These are important because removing them would actually change the active controls count.
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Find controls that are mapped to only ONE capability (unique controls)
            # First, get the count and IDs
            cursor.execute(
                """
                SELECT ccm.capability_id, COUNT(DISTINCT ccm.control_id) as unique_control_count,
                       GROUP_CONCAT(DISTINCT ccm.control_id) as unique_control_ids
                FROM capability_control_mapping ccm
                WHERE ccm.control_id IN (
                    SELECT control_id
                    FROM capability_control_mapping
                    GROUP BY control_id
                    HAVING COUNT(DISTINCT capability_id) = 1
                )
                GROUP BY ccm.capability_id
                HAVING COUNT(DISTINCT ccm.control_id) > 0
                """
            )

            rows = cursor.fetchall()
            capabilities_with_unique_controls = [row["capability_id"] for row in rows]

            # Create mapping of capability_id to unique_control_count
            unique_control_counts = {row["capability_id"]: row["unique_control_count"] for row in rows}

            # Create mapping of capability_id to list of unique control IDs
            unique_control_ids_map = {}
            for row in rows:
                capability_id = row["capability_id"]
                control_ids_str = row["unique_control_ids"]
                if control_ids_str:
                    unique_control_ids_map[capability_id] = control_ids_str.split(",")
                else:
                    unique_control_ids_map[capability_id] = []

            logger.info(f"Found {len(capabilities_with_unique_controls)} capabilities with unique controls")

            return {
                "capabilities_with_unique_controls": capabilities_with_unique_controls,
                "count": len(capabilities_with_unique_controls),
                "unique_control_counts": unique_control_counts,
                "unique_control_ids": unique_control_ids_map,
            }

    except Exception as e:
        logger.error(f"Error identifying unique control capabilities: {e}")
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

    # Initialize capability config database
    init_capability_config_db()

    logger.info("Starting server...")

    uvicorn.run("app:app", host=API_HOST, port=API_PORT, log_level="info", access_log=True)


if __name__ == "__main__":
    main()
