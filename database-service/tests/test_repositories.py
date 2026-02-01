import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from db.connections import DatabaseManager
from db.repositories import RiskRepository, ControlRepository

@pytest.fixture
def temp_db(tmp_path):
    db_path = tmp_path / "test_aiml.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("CREATE TABLE risks (risk_id TEXT PRIMARY KEY, risk_title TEXT, risk_description TEXT)")
    cursor.execute("CREATE TABLE controls (control_id TEXT PRIMARY KEY, control_title TEXT, control_description TEXT, security_function TEXT)")
    cursor.execute("CREATE TABLE risk_control_mapping (risk_id TEXT, control_id TEXT)")
    
    # Insert sample data
    cursor.execute("INSERT INTO risks VALUES ('R1', 'Risk 1', 'Desc 1')")
    cursor.execute("INSERT INTO controls VALUES ('C1', 'Control 1', 'Desc 1', 'Domain 1')")
    cursor.execute("INSERT INTO risk_control_mapping VALUES ('R1', 'C1')")
    
    conn.commit()
    conn.close()
    return str(db_path)

@pytest.fixture
def db_manager(temp_db):
    return DatabaseManager(temp_db)

def test_risk_repository_get_all(db_manager):
    repo = RiskRepository(db_manager)
    risks = repo.get_all(limit=10)
    assert len(risks) == 1
    assert risks[0]["id"] == "R1"
    assert risks[0]["title"] == "Risk 1"

def test_risk_repository_get_by_id(db_manager):
    repo = RiskRepository(db_manager)
    risk = repo.get_by_id("R1")
    assert risk is not None
    assert risk["id"] == "R1"
    
    risk_none = repo.get_by_id("R99")
    assert risk_none is None

def test_risk_repository_get_associated_controls(db_manager):
    repo = RiskRepository(db_manager)
    controls = repo.get_associated_controls("R1")
    assert len(controls) == 1
    assert controls[0]["id"] == "C1"

def test_control_repository_get_all(db_manager):
    repo = ControlRepository(db_manager)
    controls = repo.get_all(limit=10)
    assert len(controls) == 1
    assert controls[0]["id"] == "C1"
    assert controls[0]["domain"] == "Domain 1"

def test_control_repository_get_associated_risks(db_manager):
    repo = ControlRepository(db_manager)
    risks = repo.get_associated_risks("C1")
    assert len(risks) == 1
    assert risks[0]["id"] == "R1"
