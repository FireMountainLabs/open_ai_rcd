from typing import List, Optional
from pydantic import BaseModel

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

class Definition(BaseModel):
    definition_id: str
    term: str
    title: str
    description: str
    category: Optional[str] = None
    source: Optional[str] = None

class Relationship(BaseModel):
    source_id: str
    target_id: str
    relationship_type: str

class DatabaseStats(BaseModel):
    total_risks: int
    total_controls: int
    total_definitions: int
    total_relationships: int
    database_version: Optional[str] = None

class HealthStatus(BaseModel):
    status: str
    database_connected: bool
    database_path: str
    total_records: int
