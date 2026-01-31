"""Error handling utilities for API proxies."""

import logging

logger = logging.getLogger(__name__)


def extract_error_detail_from_response(error_response, scenario_name=None):
    """Extract error detail from HTTP error response."""
    error_detail = str(error_response)
    status_code = 500

    try:
        if error_response.response is not None:
            status_code = error_response.response.status_code
            try:
                error_body = error_response.response.json()
                # Try multiple possible error message fields
                detail = error_body.get("detail")
                error_msg = error_body.get("error")
                message = error_body.get("message")

                # Check each field and use the first non-empty one
                if detail and detail.strip():
                    error_detail = detail.strip()
                elif error_msg and error_msg.strip():
                    error_detail = error_msg.strip()
                elif message and message.strip():
                    error_detail = message.strip()
                else:
                    error_detail = (
                        str(error_response) if str(error_response) else f"Request failed with status {status_code}"
                    )

                # Check if error indicates duplicate scenario name
                error_text_lower = error_detail.lower()
                if (
                    "unique constraint" in error_text_lower
                    or "already exists" in error_text_lower
                    or "integrity" in error_text_lower
                ):
                    if scenario_name:
                        error_detail = f"Scenario name '{scenario_name}' already exists for this user. Please choose a different name."
                    else:
                        error_detail = "Scenario name already exists for this user. Please choose a different name."
                    status_code = 400
            except (ValueError, TypeError):
                # Response is not JSON, try to get text
                try:
                    error_detail = error_response.response.text or str(error_response)
                except Exception:
                    error_detail = str(error_response)

            # Ensure error_detail is not empty
            if not error_detail or not error_detail.strip():
                error_detail = f"Request failed with status {status_code}"

            logger.error(f"HTTP error creating scenario ({status_code}): {error_detail}")
            logger.debug(
                f"Full error response: {error_response.response.text if hasattr(error_response.response, 'text') else 'N/A'}"
            )
        else:
            error_detail = f"Request failed: {str(error_response)}"
            logger.error(f"HTTP error creating scenario: {error_response} (no response)")
    except Exception as ex:
        error_detail = f"Error processing request: {str(ex)}"
        logger.error(f"HTTP error creating scenario: {error_response}")
        logger.exception("Exception while processing error:")

    return error_detail, status_code


def format_error_response(error_detail, status_code):
    """Format error response based on status code."""
    from flask import jsonify

    if status_code == 400:
        return jsonify({"error": error_detail, "detail": error_detail}), status_code
    else:
        return (
            jsonify({"error": f"{status_code} Server Error: {error_detail}", "detail": error_detail}),
            status_code,
        )
