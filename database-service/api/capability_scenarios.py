"""Capability scenario management API endpoints."""

import logging
import sqlite3
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic Models
class CapabilityScenario(BaseModel):
    scenario_id: Optional[int] = None
    user_id: int
    scenario_name: str
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CapabilitySelection(BaseModel):
    capability_id: str
    is_active: bool


class CapabilitySelectionsBulk(BaseModel):
    scenario_id: int
    user_id: Optional[int] = None
    selections: List[CapabilitySelection]


class ControlSelection(BaseModel):
    control_id: str
    is_active: bool


class ControlSelectionsBulk(BaseModel):
    scenario_id: int
    user_id: Optional[int] = None
    selections: List[ControlSelection]


class CapabilityScenarioUpdate(BaseModel):
    scenario_name: Optional[str] = None
    is_default: Optional[bool] = None
    selections: Optional[List[CapabilitySelection]] = None
    control_selections: Optional[List[ControlSelection]] = None


class CapabilityAnalysisRequest(BaseModel):
    capability_ids: List[str]
    control_ids: Optional[List[str]] = None


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


# Global database manager - will be set by main app
db_manager = None


def set_db_manager(manager):
    """Set the database manager instance."""
    global db_manager
    db_manager = manager


@router.get("/capability-scenarios")
async def get_capability_scenarios(user_id: int = Query(...)):
    """Get all scenarios for a specific user."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT scenario_id, user_id, scenario_name, is_default,
                       created_at, updated_at
                FROM capability_scenarios
                WHERE user_id = ?
                ORDER BY is_default DESC, updated_at DESC
                """,
                (user_id,),
            )

            scenarios = []
            for row in cursor.fetchall():
                scenarios.append(
                    {
                        "scenario_id": row["scenario_id"],
                        "user_id": row["user_id"],
                        "scenario_name": row["scenario_name"],
                        "is_default": bool(row["is_default"]),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    }
                )

            return scenarios
    except Exception as e:
        logger.error(f"Error fetching scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capability-scenarios")
async def create_capability_scenario(scenario: CapabilityScenario):
    """Create a new capability scenario."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # If this is set as default, unset other defaults for this user
            if scenario.is_default:
                cursor.execute(
                    "UPDATE capability_scenarios SET is_default = 0 WHERE user_id = ?",
                    (scenario.user_id,),
                )

            cursor.execute(
                """
                INSERT INTO capability_scenarios (user_id, scenario_name, is_default)
                VALUES (?, ?, ?)
                """,
                (scenario.user_id, scenario.scenario_name, scenario.is_default),
            )

            scenario_id = cursor.lastrowid
            conn.commit()

            # Fetch the created scenario
            cursor.execute(
                """
                SELECT scenario_id, user_id, scenario_name, is_default,
                       created_at, updated_at
                FROM capability_scenarios
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            row = cursor.fetchone()
            return {
                "scenario_id": row["scenario_id"],
                "user_id": row["user_id"],
                "scenario_name": row["scenario_name"],
                "is_default": bool(row["is_default"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        logger.warning(f"IntegrityError creating scenario: {error_msg}")
        # Check for UNIQUE constraint violation (duplicate scenario name)
        if (
            "UNIQUE constraint" in error_msg
            or "UNIQUE constraint failed" in error_msg
            or "capability_scenarios.user_id" in error_msg
        ):
            raise HTTPException(
                status_code=400,
                detail=f"Scenario name '{scenario.scenario_name}' already exists for this user. Please choose a different name.",
            )
        else:
            raise HTTPException(status_code=400, detail=f"Scenario name already exists for this user: {error_msg}")
    except HTTPException:
        # Re-raise HTTPExceptions (like the one we just raised)
        raise
    except Exception as e:
        logger.error(f"Error creating scenario: {e}")
        logger.exception("Full traceback:")
        # Check if it's actually an IntegrityError that wasn't caught
        if "UNIQUE constraint" in str(e) or "IntegrityError" in str(type(e).__name__):
            raise HTTPException(
                status_code=400,
                detail=f"Scenario name '{scenario.scenario_name}' already exists for this user. Please choose a different name.",
            )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capability-scenarios/{scenario_id}")
async def get_capability_scenario(scenario_id: int, user_id: Optional[int] = Query(None)):
    """Get a specific scenario with all its selections."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Get scenario details and verify ownership
            cursor.execute(
                """
                SELECT scenario_id, user_id, scenario_name, is_default,
                       created_at, updated_at
                FROM capability_scenarios
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            scenario_row = cursor.fetchone()
            if not scenario_row:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership if user_id explicitly provided
            if user_id is not None and scenario_row["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            # Get capability selections for this scenario
            cursor.execute(
                """
                SELECT capability_id, is_active
                FROM capability_selections
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            selections = []
            for row in cursor.fetchall():
                selections.append(
                    {
                        "capability_id": row["capability_id"],
                        "is_active": bool(row["is_active"]),
                    }
                )

            # Get control selections for this scenario
            cursor.execute(
                """
                SELECT control_id, is_active
                FROM control_selections
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            control_selections = []
            for row in cursor.fetchall():
                control_selections.append(
                    {
                        "control_id": row["control_id"],
                        "is_active": bool(row["is_active"]),
                    }
                )

            return {
                "scenario_id": scenario_row["scenario_id"],
                "user_id": scenario_row["user_id"],
                "scenario_name": scenario_row["scenario_name"],
                "is_default": bool(scenario_row["is_default"]),
                "created_at": scenario_row["created_at"],
                "updated_at": scenario_row["updated_at"],
                "selections": selections,
                "control_selections": control_selections,
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/capability-scenarios/{scenario_id}")
async def update_capability_scenario(
    scenario_id: int,
    scenario: CapabilityScenarioUpdate,
    user_id: Optional[int] = Query(None),
):
    """Update a scenario's name or default status."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Verify scenario exists and get current values
            cursor.execute(
                "SELECT user_id, scenario_name, is_default FROM capability_scenarios WHERE scenario_id = ?",
                (scenario_id,),
            )
            row = cursor.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Scenario not found")

            owner_user_id = row["user_id"]

            # Verify ownership when explicitly provided
            if user_id is not None and owner_user_id != user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            # Get current values and use provided ones if present
            new_scenario_name = scenario.scenario_name if scenario.scenario_name is not None else row["scenario_name"]
            new_is_default = scenario.is_default if scenario.is_default is not None else row["is_default"]

            # If setting as default, unset other defaults for this user
            if new_is_default:
                cursor.execute(
                    "UPDATE capability_scenarios SET is_default = 0 WHERE user_id = ?",
                    (owner_user_id,),
                )

            cursor.execute(
                """
                UPDATE capability_scenarios
                SET scenario_name = ?, is_default = ?, updated_at = CURRENT_TIMESTAMP
                WHERE scenario_id = ?
                """,
                (new_scenario_name, new_is_default, scenario_id),
            )

            # Handle capability selections if provided
            if scenario.selections is not None:
                # Delete existing capability selections for this scenario
                cursor.execute(
                    "DELETE FROM capability_selections WHERE scenario_id = ?",
                    (scenario_id,),
                )

                # Insert new capability selections
                for selection in scenario.selections:
                    cursor.execute(
                        """
                        INSERT INTO capability_selections (scenario_id, capability_id, is_active)
                        VALUES (?, ?, ?)
                        """,
                        (scenario_id, selection.capability_id, selection.is_active),
                    )

            # Handle control selections if provided
            if scenario.control_selections is not None:
                logger.info(
                    f"Updating control selections for scenario {scenario_id}: {len(scenario.control_selections)} selections"
                )
                # Delete existing control selections for this scenario
                cursor.execute(
                    "DELETE FROM control_selections WHERE scenario_id = ?",
                    (scenario_id,),
                )

                # Insert new control selections
                for idx, control_selection in enumerate(scenario.control_selections):
                    try:
                        # Validate control_selection data
                        if not hasattr(control_selection, "control_id") or not control_selection.control_id:
                            logger.error(f"Invalid control_selection at index {idx}: missing control_id")
                            raise ValueError(f"Invalid control_selection at index {idx}: missing control_id")

                        cursor.execute(
                            """
                            INSERT INTO control_selections (scenario_id, control_id, is_active)
                            VALUES (?, ?, ?)
                            """,
                            (scenario_id, control_selection.control_id, bool(control_selection.is_active)),
                        )
                    except sqlite3.IntegrityError as e:
                        logger.error(f"Integrity error inserting control_selection {idx}: {e}")
                        logger.error(
                            f"Control selection data: control_id={control_selection.control_id}, is_active={control_selection.is_active}"
                        )
                        raise
                    except Exception as e:
                        logger.error(f"Error inserting control_selection {idx}: {e}")
                        logger.error(f"Control selection data: {control_selection}")
                        raise

            conn.commit()

            # Return updated scenario
            cursor.execute(
                """
                SELECT scenario_id, user_id, scenario_name, is_default,
                       created_at, updated_at
                FROM capability_scenarios
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            updated_row = cursor.fetchone()
            return {
                "scenario_id": updated_row["scenario_id"],
                "user_id": updated_row["user_id"],
                "scenario_name": updated_row["scenario_name"],
                "is_default": bool(updated_row["is_default"]),
                "created_at": updated_row["created_at"],
                "updated_at": updated_row["updated_at"],
            }
    except HTTPException:
        raise
    except sqlite3.Error as e:
        logger.error(f"Database error updating scenario {scenario_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Error updating scenario {scenario_id}: {e}")
        logger.exception("Full traceback:")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/capability-scenarios/{scenario_id}")
async def delete_capability_scenario(scenario_id: int, user_id: Optional[int] = Query(None)):
    """Delete a scenario and all its selections."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Verify scenario exists and get user_id
            cursor.execute(
                "SELECT user_id FROM capability_scenarios WHERE scenario_id = ?",
                (scenario_id,),
            )
            scenario = cursor.fetchone()
            if not scenario:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership if provided
            if user_id is not None and scenario["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            # Delete scenario (selections will be cascade deleted)
            cursor.execute("DELETE FROM capability_scenarios WHERE scenario_id = ?", (scenario_id,))

            conn.commit()

            return {"message": "Scenario deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capability-selections")
async def save_capability_selections(bulk: CapabilitySelectionsBulk):
    """Bulk save capability selections for a scenario."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Verify scenario exists and ownership
            cursor.execute(
                "SELECT user_id FROM capability_scenarios WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )
            scenario = cursor.fetchone()
            if not scenario:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership
            scenario_owner_id = scenario["user_id"]

            if bulk.user_id is not None and scenario_owner_id != bulk.user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            # Delete existing selections for this scenario
            cursor.execute(
                "DELETE FROM capability_selections WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )

            # Insert new selections
            for selection in bulk.selections:
                cursor.execute(
                    """
                    INSERT INTO capability_selections (scenario_id, capability_id, is_active)
                    VALUES (?, ?, ?)
                    """,
                    (bulk.scenario_id, selection.capability_id, selection.is_active),
                )

            # Update scenario's updated_at timestamp
            cursor.execute(
                "UPDATE capability_scenarios SET updated_at = CURRENT_TIMESTAMP WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )

            conn.commit()

            return {
                "message": "Selections saved successfully",
                "count": len(bulk.selections),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving selections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capability-selections/{scenario_id}")
async def get_capability_selections(scenario_id: int, user_id: Optional[int] = Query(None)):
    """Get all selections for a scenario."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # First verify the scenario exists and ownership
            cursor.execute(
                "SELECT user_id FROM capability_scenarios WHERE scenario_id = ?",
                (scenario_id,),
            )
            scenario = cursor.fetchone()
            if not scenario:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership
            if user_id is not None and scenario["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            cursor.execute(
                """
                SELECT capability_id, is_active
                FROM capability_selections
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            selections = []
            for row in cursor.fetchall():
                selections.append(
                    {
                        "capability_id": row["capability_id"],
                        "is_active": bool(row["is_active"]),
                    }
                )

            return selections
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching selections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/control-selections")
async def save_control_selections(bulk: ControlSelectionsBulk):
    """Bulk save control selections for a scenario."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # Verify scenario exists and ownership
            cursor.execute(
                "SELECT user_id FROM capability_scenarios WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )
            scenario = cursor.fetchone()
            if not scenario:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership
            scenario_owner_id = scenario["user_id"]

            if bulk.user_id is not None and scenario_owner_id != bulk.user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            # Delete existing selections for this scenario
            cursor.execute(
                "DELETE FROM control_selections WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )

            # Insert new selections
            for selection in bulk.selections:
                cursor.execute(
                    """
                    INSERT INTO control_selections (scenario_id, control_id, is_active)
                    VALUES (?, ?, ?)
                    """,
                    (bulk.scenario_id, selection.control_id, selection.is_active),
                )

            # Update scenario's updated_at timestamp
            cursor.execute(
                "UPDATE capability_scenarios SET updated_at = CURRENT_TIMESTAMP WHERE scenario_id = ?",
                (bulk.scenario_id,),
            )

            conn.commit()

            return {
                "message": "Control selections saved successfully",
                "count": len(bulk.selections),
            }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving control selections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/control-selections/{scenario_id}")
async def get_control_selections(scenario_id: int, user_id: Optional[int] = Query(None)):
    """Get all control selections for a scenario."""
    try:
        with db_manager.get_capability_config_db() as conn:
            cursor = conn.cursor()

            # First verify the scenario exists and ownership
            cursor.execute(
                "SELECT user_id FROM capability_scenarios WHERE scenario_id = ?",
                (scenario_id,),
            )
            scenario = cursor.fetchone()
            if not scenario:
                raise HTTPException(status_code=404, detail="Scenario not found")

            # Verify ownership
            if user_id is not None and scenario["user_id"] != user_id:
                raise HTTPException(status_code=403, detail="Access denied: scenario belongs to another user")

            cursor.execute(
                """
                SELECT control_id, is_active
                FROM control_selections
                WHERE scenario_id = ?
                """,
                (scenario_id,),
            )

            selections = []
            for row in cursor.fetchall():
                selections.append(
                    {
                        "control_id": row["control_id"],
                        "is_active": bool(row["is_active"]),
                    }
                )

            return selections
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching control selections: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/capability-analysis", response_model=CapabilityAnalysisResponse)
async def analyze_capabilities(request: CapabilityAnalysisRequest):
    """Calculate metrics based on active capabilities."""
    try:
        with db_manager.get_db_connection() as conn:
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
            placeholders = ",".join("?" * len(request.capability_ids))
            cursor.execute(
                f"""
                SELECT DISTINCT control_id
                FROM capability_control_mapping
                WHERE capability_id IN ({placeholders})
            """,
                request.capability_ids,
            )

            controls_from_active_capabilities = {row["control_id"] for row in cursor.fetchall()}

            # Apply control-level granularity if control_ids provided
            # A control is active only if:
            # 1. Its capability is active (already filtered above) AND
            # 2. The control is explicitly in control_ids (if provided)
            if request.control_ids is not None:
                # Filter to only controls that are both from active capabilities AND in control_ids
                requested_control_set = set(request.control_ids)
                active_control_ids = list(controls_from_active_capabilities.intersection(requested_control_set))
            else:
                # Backward compatibility: all controls from active capabilities are active
                active_control_ids = list(controls_from_active_capabilities)

            active_controls_count = len(active_control_ids)

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
