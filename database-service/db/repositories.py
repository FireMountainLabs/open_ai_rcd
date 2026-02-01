import sqlite3
import logging
from typing import List, Optional, Dict, Any
from .connections import DatabaseManager

logger = logging.getLogger(__name__)

class BaseRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

class RiskRepository(BaseRepository):
    def get_all(self, limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
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
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, risk_id: str) -> Optional[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT risk_id as id, risk_title as title, risk_description as description, NULL as category "
                "FROM risks WHERE risk_id = ?",
                (risk_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_associated_controls(self, risk_id: str) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT c.control_id as id, c.control_title as title, 
                       c.control_description as description, c.security_function as domain
                FROM controls c
                JOIN risk_control_mapping m ON c.control_id = m.control_id
                WHERE m.risk_id = ?
                """,
                (risk_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

class ControlRepository(BaseRepository):
    def get_all(self, limit: int = 100, offset: int = 0, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            query = (
                "SELECT control_id as id, control_title as title, "
                "control_description as description, security_function as domain "
                "FROM controls"
            )
            params = []
            if domain:
                query += " WHERE security_function = ?"
                params.append(domain)
            query += " ORDER BY id LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_by_id(self, control_id: str) -> Optional[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT control_id as id, control_title as title, control_description as description, "
                "security_function as domain FROM controls WHERE control_id = ?",
                (control_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_associated_risks(self, control_id: str) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT r.risk_id as id, r.risk_title as title, r.risk_description as description, NULL as category
                FROM risks r
                JOIN risk_control_mapping m ON r.risk_id = m.risk_id
                WHERE m.control_id = ?
                """,
                (control_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

class DefinitionRepository(BaseRepository):
    def get_all(self, limit: int = 100, offset: int = 0, category: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT definition_id, term, title, description, category, source FROM definitions"
            params = []
            if category:
                query += " WHERE category = ?"
                params.append(category)
            query += " ORDER BY term LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

class RelationshipRepository(BaseRepository):
    def get_relationships(self, relationship_type: Optional[str] = None, limit: int = 1000) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            relationships = []
            
            if not relationship_type or relationship_type == "risk_control":
                cursor.execute(
                    "SELECT risk_id as source_id, control_id as target_id, 'risk_control' as relationship_type "
                    "FROM risk_control_mapping LIMIT ?", (limit,)
                )
                relationships.extend([dict(row) for row in cursor.fetchall()])


            return relationships[:limit]

class SearchRepository(BaseRepository):
    def search(self, entity_type: str, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        import re
        sanitized_q = re.sub(r"[^\w\s\-\.]", "", query.strip())
        if not sanitized_q:
            return []
            
        search_term = f"%{sanitized_q}%"
        results = []
        
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            if entity_type == "risk":
                cursor.execute(
                    "SELECT 'risk' as type, risk_id as id, risk_title as title, risk_description as description "
                    "FROM risks WHERE risk_title LIKE ? OR risk_description LIKE ? OR risk_id LIKE ? LIMIT ?",
                    (search_term, search_term, search_term, limit)
                )
                results.extend([dict(row) for row in cursor.fetchall()])
            
            elif entity_type == "control":
                cursor.execute(
                    "SELECT 'control' as type, control_id as id, control_title as title, control_description as description "
                    "FROM controls WHERE control_title LIKE ? OR control_description LIKE ? OR control_id LIKE ? LIMIT ?",
                    (search_term, search_term, search_term, limit)
                )
                results.extend([dict(row) for row in cursor.fetchall()])
            
            elif entity_type == "definition":
                cursor.execute(
                    "SELECT 'definition' as type, definition_id as id, term as title, description, category, source "
                    "FROM definitions WHERE term LIKE ? OR description LIKE ? OR category LIKE ? LIMIT ?",
                    (search_term, search_term, search_term, limit)
                )
                results.extend([dict(row) for row in cursor.fetchall()])
            
            return results[:limit]

class StatsRepository(BaseRepository):
    def get_stats(self) -> Dict[str, Any]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            stats = {}
            cursor.execute("SELECT COUNT(*) FROM risks")
            stats["total_risks"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM controls")
            stats["total_controls"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM definitions")
            stats["total_definitions"] = cursor.fetchone()[0]
            
            # Sum of all mappings
            total_rel = 0
            cursor.execute("SELECT COUNT(*) FROM risk_control_mapping")
            total_rel += cursor.fetchone()[0]
            stats["total_relationships"] = total_rel
            
            return stats

    def get_file_metadata(self) -> List[Dict[str, Any]]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM file_metadata")
            return [dict(row) for row in cursor.fetchall()]

class NetworkRepository(BaseRepository):
    def get_network_data(self) -> Dict[str, Any]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT risk_id as source_id, control_id as target_id, 'risk_control' as relationship_type FROM risk_control_mapping")
            risk_control_links = [dict(row) for row in cursor.fetchall()]
            
            return {
                "risk_control_links": risk_control_links,
            }

class GapsRepository(BaseRepository):
    def get_gaps_analysis(self) -> Dict[str, Any]:
        with self.db_manager.get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT risk_id, risk_title, risk_description FROM risks")
            all_risks = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT control_id, control_title, control_description FROM controls")
            all_controls = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT risk_id FROM risk_control_mapping")
            mapped_risk_ids = {row["risk_id"] for row in cursor.fetchall()}
            
            cursor.execute("SELECT DISTINCT control_id FROM risk_control_mapping")
            mapped_control_ids = {row["control_id"] for row in cursor.fetchall()}
            
            unmapped_risks = [r for r in all_risks if r["risk_id"] not in mapped_risk_ids]
            unmapped_controls = [c for c in all_controls if c["control_id"] not in mapped_control_ids]
            
            total_risks = len(all_risks)
            total_controls = len(all_controls)
            
            risk_coverage_pct = ((total_risks - len(unmapped_risks)) / total_risks * 100) if total_risks > 0 else 0
            control_coverage_pct = ((total_controls - len(unmapped_controls)) / total_controls * 100) if total_controls > 0 else 0
            
            return {
                "summary": {
                    "total_risks": total_risks,
                    "total_controls": total_controls,
                    "mapped_risks": total_risks - len(unmapped_risks),
                    "mapped_controls": total_controls - len(unmapped_controls),
                    "unmapped_risks": len(unmapped_risks),
                    "unmapped_controls": len(unmapped_controls),
                    "risk_coverage_pct": round(risk_coverage_pct, 1),
                    "control_coverage_pct": round(control_coverage_pct, 1),
                    "control_utilization_pct": round(control_coverage_pct, 1),
                },
                "unmapped_risks": unmapped_risks,
                "unmapped_controls": unmapped_controls,
            }
