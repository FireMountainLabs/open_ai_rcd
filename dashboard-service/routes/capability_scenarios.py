"""Capability scenario routes."""

import logging
import requests
from flask import Blueprint, jsonify, request, current_app, session
from utils.error_handling import extract_error_detail_from_response, format_error_response

logger = logging.getLogger(__name__)


def create_capability_scenarios_blueprint(database_url: str, require_auth=None, enable_auth=True):  # noqa: C901
    """Create blueprint for capability scenario routes.

    Args:
        database_url: URL of the database service
        require_auth: Optional authentication decorator to apply to routes
        enable_auth: Whether authentication is enabled (default: True)
    """
    bp = Blueprint("capability_scenarios", __name__)

    def get_user_id():
        """Extract user_id from authenticated user or request body.

        When authentication is disabled, uses user_id from request body
        (which comes from session-based identification via /api/current-user).
        This ensures each browser session gets unique worksheets.
        """
        auth_enabled = enable_auth
        try:
            auth_enabled = current_app.config.get("ENABLE_AUTH", auth_enabled)
        except RuntimeError:
            pass

        if not auth_enabled:
            # When auth is disabled, trust user_id from request body
            # The frontend gets this from /api/current-user which uses session-based ID
            if request.is_json:
                data = request.get_json()
                if data and "user_id" in data:
                    user_id = data.get("user_id")
                    session["session_user_id"] = user_id
                    session.permanent = True
                    return user_id
            # Fallback: try to get from query params (for GET requests)
            if request.args and "user_id" in request.args:
                try:
                    user_id = int(request.args.get("user_id"))
                    session["session_user_id"] = user_id
                    session.permanent = True
                    return user_id
                except (ValueError, TypeError):
                    pass
            # Fallback to session-based user id for tests/local runs
            session_user_id = session.get("session_user_id")
            if session_user_id is None:
                import uuid
                import hashlib

                session_uuid = str(uuid.uuid4())
                session_user_id = int(hashlib.md5(session_uuid.encode()).hexdigest()[:8], 16) % 1000000
                session_user_id = abs(session_user_id) + 1
                session["session_user_id"] = session_user_id
                session.permanent = True
            return session_user_id

        if hasattr(request, "current_user") and request.current_user:
            user_id = request.current_user.get("id")
            if user_id is not None:
                return user_id
        return None

    @bp.route("/api/capability-scenarios", methods=["GET", "POST"])
    def _proxy_capability_scenarios():
        """Proxy capability scenarios requests to database service."""
        # Extract scenario name early for use in error handling
        scenario_name = None
        if request.method == "POST":
            data = request.get_json()
            scenario_name = data.get("scenario_name", "this scenario") if data else "this scenario"

        try:
            if request.method == "GET":
                # Get user_id from authenticated user
                user_id = get_user_id()
                if not user_id:
                    return jsonify({"error": "Authentication required"}), 401

                response = requests.get(
                    f"{database_url}/api/capability-scenarios",
                    params={"user_id": user_id},
                    timeout=10,
                )
                response.raise_for_status()
                return jsonify(response.json())

            elif request.method == "POST":
                # Create new scenario
                logger.info(f"Proxying POST request to create scenario: {scenario_name}")
                data = request.get_json()
                if not data:
                    return jsonify({"error": "Request body is required"}), 400

                # Get user_id from authenticated user or request body
                user_id = get_user_id()
                if not user_id:
                    # When auth is enabled, this means not authenticated
                    # When auth is disabled, this means no user_id in request (shouldn't happen)
                    return jsonify({"error": "Authentication required"}), 401

                # Override user_id in request body with authenticated user's ID
                # (or use the one from request body when auth is disabled)
                data["user_id"] = user_id

                response = requests.post(f"{database_url}/api/capability-scenarios", json=data, timeout=10)
                response.raise_for_status()
                return jsonify(response.json())

        except requests.exceptions.HTTPError as e:
            error_detail, status_code = extract_error_detail_from_response(e, scenario_name)
            return format_error_response(error_detail, status_code)
        except requests.exceptions.RequestException as e:
            error_detail = str(e)
            # If it's a connection error, provide more context
            if isinstance(e, requests.exceptions.ConnectionError):
                error_detail = "Could not connect to database service. Please check if the service is running."
            elif isinstance(e, requests.exceptions.Timeout):
                error_detail = "Request to database service timed out. Please try again."
            elif not error_detail or not error_detail.strip():
                error_detail = "An unknown error occurred while creating the scenario."

            logger.error(f"Failed to proxy capability scenarios: {error_detail}")
            logger.exception("Full traceback:")
            return jsonify({"error": error_detail, "detail": error_detail}), 500

    @bp.route("/api/capability-scenarios/<int:scenario_id>", methods=["GET", "PUT", "DELETE"])
    def _proxy_capability_scenario(scenario_id):
        """Proxy individual scenario requests to database service."""
        try:
            # Get authenticated user_id
            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401

            if request.method == "GET":
                response = requests.get(
                    f"{database_url}/api/capability-scenarios/{scenario_id}", params={"user_id": user_id}, timeout=10
                )
                response.raise_for_status()
                data = response.json()
                if isinstance(data, list):
                    data = data[0] if data else {}
                return jsonify(data)

            elif request.method == "PUT":
                data = request.get_json()
                logger.info(f"Proxying PUT request for scenario {scenario_id}")
                logger.debug(
                    f"Request data: selections={len(data.get('selections', []))}, control_selections={len(data.get('control_selections', []))}"
                )

                response = requests.put(
                    f"{database_url}/api/capability-scenarios/{scenario_id}",
                    params={"user_id": user_id},
                    json=data,
                    timeout=10,
                )
                response.raise_for_status()
                return jsonify(response.json())

            elif request.method == "DELETE":
                logger.info(f"Proxying DELETE request for scenario {scenario_id}")
                response = requests.delete(
                    f"{database_url}/api/capability-scenarios/{scenario_id}", params={"user_id": user_id}, timeout=10
                )
                response.raise_for_status()
                return jsonify({"message": "Scenario deleted successfully"})

        except requests.exceptions.HTTPError as e:
            error_detail = str(e)
            try:
                if e.response is not None:
                    try:
                        error_body = e.response.json()
                        error_detail = error_body.get("detail", error_body.get("error", str(e)))
                        # Ensure error_detail is a string, not a MagicMock or other object
                        if not isinstance(error_detail, str):
                            error_detail = str(error_detail)
                    except (ValueError, TypeError):
                        error_detail = e.response.text or str(e)
            except Exception:
                error_detail = str(e)

            # Final safety check - ensure error_detail is always a string
            if not isinstance(error_detail, str):
                error_detail = str(error_detail)

            logger.error(f"HTTP error in scenario operation: {error_detail}")
            return jsonify({"error": error_detail}), e.response.status_code if e.response else 500
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy scenario operation: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/capability-selections", methods=["POST"])
    def _proxy_capability_selections():
        """Proxy capability selections bulk save to database service."""
        try:
            # Get authenticated user_id
            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401

            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400

            # Ensure user_id in request body matches authenticated user
            data["user_id"] = user_id

            response = requests.post(f"{database_url}/api/capability-selections", json=data, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy capability selections: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/capability-selections/<int:scenario_id>", methods=["GET"])
    def _proxy_get_capability_selections(scenario_id):
        """Proxy get capability selections for a scenario."""
        try:
            # Get authenticated user_id
            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401

            response = requests.get(
                f"{database_url}/api/capability-selections/{scenario_id}", params={"user_id": user_id}, timeout=10
            )

            response.raise_for_status()
            return jsonify(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy capability selections for scenario {scenario_id}: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/control-selections", methods=["POST"])
    def _proxy_control_selections():
        """Proxy control selections bulk save to database service."""
        try:
            # Get authenticated user_id
            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401

            data = request.get_json()
            if not data:
                return jsonify({"error": "Request body is required"}), 400

            # Ensure user_id in request body matches authenticated user
            data["user_id"] = user_id

            response = requests.post(f"{database_url}/api/control-selections", json=data, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy control selections: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/control-selections/<int:scenario_id>", methods=["GET"])
    def _proxy_get_control_selections(scenario_id):
        """Proxy get control selections for a scenario."""
        try:
            # Get authenticated user_id
            user_id = get_user_id()
            if not user_id:
                return jsonify({"error": "Authentication required"}), 401

            response = requests.get(
                f"{database_url}/api/control-selections/{scenario_id}", params={"user_id": user_id}, timeout=10
            )

            response.raise_for_status()
            return jsonify(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy get control selections: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/capability-analysis", methods=["POST"])
    def proxy_capability_analysis():
        """Proxy capability analysis calculation to database service."""
        try:
            data = request.get_json()
            capability_ids = data.get("capability_ids", []) if data else []
            logger.info(
                f"📥 Received capability analysis request with {len(capability_ids)} capabilities: {capability_ids[:10]}..."
            )  # Log first 10
            response = requests.post(f"{database_url}/api/capability-analysis", json=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            logger.info(
                f"📤 API returned: active_controls={result.get('active_controls', 0)}, exposed_risks={result.get('exposed_risks', 0)}"
            )
            return jsonify(result)

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy capability analysis: {e}")
            return jsonify({"error": str(e)}), 500

    @bp.route("/api/capability-unique-controls", methods=["GET"])
    def proxy_capability_unique_controls():
        """Proxy request to get unique controls for capabilities."""
        try:
            capability_ids = request.args.getlist("capability_ids")
            params = {"capability_ids": capability_ids}
            response = requests.get(f"{database_url}/api/capability-unique-controls", params=params, timeout=10)
            response.raise_for_status()
            return jsonify(response.json())

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to proxy capability unique controls: {e}")
            return jsonify({"error": str(e)}), 500

    # Apply authentication decorator to all routes if provided
    if require_auth:
        # Wrap all route handlers with require_auth
        # Note: We need to do this after all routes are defined but before returning
        # Create a copy of view_functions to avoid modification during iteration
        endpoints_to_wrap = list(bp.view_functions.keys())
        for endpoint in endpoints_to_wrap:
            view_func = bp.view_functions[endpoint]
            bp.view_functions[endpoint] = require_auth(view_func)

    return bp
