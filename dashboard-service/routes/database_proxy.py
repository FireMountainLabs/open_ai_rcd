"""Database service proxy routes."""

import logging
from flask import Blueprint, jsonify, request

logger = logging.getLogger(__name__)


def create_database_proxy_blueprint(database_url: str, api_client, api_config):  # noqa: C901
    """Create blueprint for database proxy routes.

    Args:
        database_url: URL of the database service
        api_client: DatabaseAPIClient instance for some routes
        api_config: API configuration dict for limits
    """
    bp = Blueprint("database_proxy", __name__)

    @bp.route("/api/risks")
    def proxy_risks():
        """Proxy risks request to database service."""
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("default_limit", 100)
            limit = request.args.get("limit", default_limit, type=int)
            offset = request.args.get("offset", 0, type=int)
            category = request.args.get("category")

            risks = api_client.get_risks(limit=limit, offset=offset, category=category)
            return jsonify(risks)
        except Exception as e:
            logger.error(f"Failed to fetch risks: {e}")
            return jsonify([])

    @bp.route("/api/risks/summary")
    def proxy_risks_summary():
        """Proxy risks summary request to database service."""
        risks_summary = api_client.get_risks_summary()
        return jsonify(risks_summary)

    @bp.route("/api/controls")
    def proxy_controls():
        """Proxy controls request to database service."""
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("default_limit", 100)
            limit = request.args.get("limit", default_limit, type=int)
            offset = request.args.get("offset", 0, type=int)
            domain = request.args.get("domain")

            controls = api_client.get_controls(limit=limit, offset=offset, domain=domain)
            return jsonify(controls)
        except Exception as e:
            logger.error(f"Failed to fetch controls: {e}")
            return jsonify([])

    @bp.route("/api/controls/summary")
    def proxy_controls_summary():
        """Proxy controls summary request to database service."""
        controls_summary = api_client.get_controls_summary()
        return jsonify(controls_summary)

    @bp.route("/api/controls/mapped")
    def proxy_mapped_control_ids():
        """Proxy mapped control IDs request to database service."""
        try:
            response = api_client.session.get(f"{api_client.base_url}/api/controls/mapped")
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"Failed to fetch mapped control IDs: {e}")
            return jsonify({"mapped_control_ids": []})

    @bp.route("/api/questions")
    def proxy_questions():
        """Proxy questions request to database service."""
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("default_limit", 100)
            limit = request.args.get("limit", default_limit, type=int)
            offset = request.args.get("offset", 0, type=int)
            category = request.args.get("category")

            questions = api_client.get_questions(limit=limit, offset=offset, category=category)
            return jsonify(questions)
        except Exception as e:
            logger.error(f"Failed to fetch questions: {e}")
            return jsonify([])

    @bp.route("/api/questions/summary")
    def proxy_questions_summary():
        """Proxy questions summary request to database service."""
        questions_summary = api_client.get_questions_summary()
        return jsonify(questions_summary)

    @bp.route("/api/definitions")
    def proxy_definitions():
        """Proxy definitions request to database service."""
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("default_limit", 100)
            limit = request.args.get("limit", default_limit, type=int)
            offset = request.args.get("offset", 0, type=int)
            category = request.args.get("category")

            definitions = api_client.get_definitions(limit=limit, offset=offset, category=category)
            return jsonify(definitions)
        except Exception as e:
            logger.error(f"Failed to fetch definitions: {e}")
            return jsonify([])

    @bp.route("/api/relationships")
    def proxy_relationships():
        """Proxy relationships request to database service."""
        try:
            relationship_type = request.args.get("relationship_type")
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("relationships_limit", 1000)
            limit = request.args.get("limit", default_limit, type=int)

            relationships = api_client.get_relationships(relationship_type=relationship_type, limit=limit)
            return jsonify(relationships)
        except Exception as e:
            logger.error(f"Failed to fetch relationships: {e}")
            return jsonify([])

    @bp.route("/api/search")
    def proxy_search():
        """Proxy search request to database service."""
        query = request.args.get("q", "")
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("search_limit", 50)
            limit = request.args.get("limit", default_limit, type=int)

            if not query:
                return jsonify({"query": "", "results": []})

            results = api_client.search(query=query, limit=limit)
            return jsonify(results)
        except Exception as e:
            logger.error(f"Failed to search: {e}")
            return jsonify({"query": query, "results": []})

    @bp.route("/api/stats")
    def proxy_stats():
        """Proxy stats request to database service."""
        try:
            stats = api_client.get_stats()
            return jsonify(stats)
        except Exception as e:
            logger.error(f"Failed to fetch stats: {e}")
            return jsonify({"total_risks": 0, "total_controls": 0, "total_questions": 0})

    @bp.route("/api/network")
    def proxy_network():
        """Proxy network request to database service."""
        try:
            response = api_client.session.get(f"{api_client.base_url}/api/network")
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"Failed to fetch network data: {e}")
            return jsonify(
                {
                    "risk_control_links": [],
                    "question_risk_links": [],
                    "question_control_links": [],
                }
            )

    @bp.route("/api/gaps")
    def proxy_gaps():
        """Proxy gaps request to database service."""
        try:
            response = api_client.session.get(f"{api_client.base_url}/api/gaps")
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"Failed to fetch gaps data: {e}")
            return jsonify(
                {
                    "summary": {
                        "total_risks": 0,
                        "total_controls": 0,
                        "unmapped_risks": 0,
                    },
                    "unmapped_risks": [],
                }
            )

    @bp.route("/api/last-updated")
    def proxy_last_updated():
        """Proxy last-updated request to database service."""
        try:
            response = api_client.session.get(f"{api_client.base_url}/api/last-updated")
            response.raise_for_status()
            return jsonify(response.json())
        except Exception as e:
            logger.error(f"Failed to fetch last updated data: {e}")
            return jsonify(
                {
                    "risk_control_links": [],
                    "question_risk_links": [],
                    "question_control_links": [],
                }
            )

    @bp.route("/api/file-metadata")
    def proxy_file_metadata():
        """Proxy file-metadata request to database service."""
        try:
            metadata = api_client.get_file_metadata()
            return jsonify(metadata)
        except Exception as e:
            logger.error(f"Failed to fetch file metadata: {e}")
            return jsonify({"files": []})

    @bp.route("/api/risk/<risk_id>")
    def proxy_risk(risk_id):
        """Proxy individual risk request to database service."""
        try:
            detail = api_client.get_risk_detail(risk_id)
            return jsonify(detail)
        except Exception as e:
            logger.error(f"Failed to fetch risk detail: {e}")
            return jsonify({"risk": {}, "associated_controls": [], "associated_questions": []})

    @bp.route("/api/control/<control_id>")
    def proxy_control(control_id):
        """Proxy individual control request to database service."""
        try:
            detail = api_client.get_control_detail(control_id)
            return jsonify(detail)
        except Exception as e:
            logger.error(f"Failed to fetch control detail: {e}")
            return jsonify({"control": {}, "associated_risks": [], "associated_questions": []})

    @bp.route("/api/question/<question_id>")
    def proxy_question(question_id):
        """Proxy individual question request to database service."""
        try:
            detail = api_client.get_question_detail(question_id)
            return jsonify(detail)
        except Exception as e:
            logger.error(f"Failed to fetch question detail: {e}")
            return jsonify({"question": {}, "associated_risks": [], "associated_controls": []})

    @bp.route("/api/managing-roles")
    def proxy_managing_roles():
        """Proxy managing-roles request to database service."""
        try:
            roles = api_client.get_managing_roles()
            return jsonify(roles)
        except Exception as e:
            logger.error(f"Failed to fetch managing roles: {e}")
            return jsonify({"managing_roles": []})

    @bp.route("/api/capabilities")
    def proxy_capabilities():
        """Proxy capabilities request to database service."""
        try:
            # Use config defaults if not provided
            default_limit = api_config.get("limits", {}).get("default_limit", 100)
            limit = request.args.get("limit", default_limit, type=int)
            offset = request.args.get("offset", 0, type=int)
            capability_type = request.args.get("capability_type")
            domain = request.args.get("domain")

            capabilities = api_client.get_capabilities(
                limit=limit, offset=offset, capability_type=capability_type, domain=domain
            )
            return jsonify(capabilities)
        except Exception as e:
            logger.error(f"Failed to fetch capabilities: {e}")
            return jsonify([])

    @bp.route("/api/capabilities/<capability_id>")
    def proxy_capability(capability_id):
        """Proxy individual capability request to database service."""
        try:
            detail = api_client.get_capability_detail(capability_id)
            return jsonify(detail)
        except Exception as e:
            logger.error(f"Failed to fetch capability detail: {e}")
            return jsonify({"error": str(e)})

    @bp.route("/api/capability-tree")
    def proxy_capability_tree():
        """Proxy capability-tree request to database service."""
        try:
            tree = api_client.get_capability_tree()
            logger.info(f"Proxying capability tree: {len(tree) if isinstance(tree, list) else 'non-list'} items")
            if not tree or (isinstance(tree, list) and len(tree) == 0):
                logger.warning("Capability tree is empty - no capabilities found")
            return jsonify(tree)
        except Exception as e:
            logger.error(f"Failed to fetch capability tree: {e}", exc_info=True)
            return jsonify([])

    return bp
