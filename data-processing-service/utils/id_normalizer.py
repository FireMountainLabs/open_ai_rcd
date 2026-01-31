"""
ID Normalization utilities for AIML risk management framework.

This module provides robust ID normalization and validation to ensure
consistent ID formats across different data sources and versions.
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class IDNormalizer:
    """
    Handles ID normalization and validation for consistent data processing.

    This class provides methods to normalize IDs from different formats
    and validate them against expected patterns.
    """

    # ID patterns for different entity types
    ID_PATTERNS = {
        "risk": r"^AIR\.(\d+)$",
        "control": r"^AI[A-Z]{2,4}\.(\d+)$",
        "question": r"^[A-Z]{2,6}\d+\.\d+$|^Q\d+$",
    }

    def __init__(self, enforce_strict_format: bool = True):
        """
        Initialize the ID normalizer.

        Args:
            enforce_strict_format: If True, enforces strict ID format validation
        """
        self.enforce_strict_format = enforce_strict_format

    def normalize_risk_id(self, risk_id: str) -> Optional[str]:
        """
        Normalize a risk ID to the standard format (AIR.XXX).

        Args:
            risk_id: Raw risk ID string

        Returns:
            Normalized risk ID in format AIR.XXX, or None if invalid
        """
        if not risk_id:
            return None

        # Handle both string and numeric inputs (e.g., from Excel)
        if isinstance(risk_id, (int, float)):
            risk_id = str(risk_id)
        elif not isinstance(risk_id, str):
            return None

        # Clean the input
        risk_id = str(risk_id).strip()

        # Handle different formats
        if risk_id.startswith("AIR."):
            # Extract the number part
            match = re.match(r"AIR\.(\d+)", risk_id)
            if match:
                number = int(match.group(1))
                return f"AIR.{number:03d}"  # Pad to 3 digits
        elif risk_id.startswith("AIR"):
            # Handle AIR1, AIR2, etc.
            match = re.match(r"AIR(\d+)", risk_id)
            if match:
                number = int(match.group(1))
                return f"AIR.{number:03d}"
        elif risk_id.isdigit():
            # Handle just numbers
            number = int(risk_id)
            return f"AIR.{number:03d}"

        # If we get here, the format is not recognized
        if self.enforce_strict_format:
            logger.warning(f"Invalid risk ID format: {risk_id}")
            return None
        else:
            # Try to extract any number and create AIR.XXX format
            numbers = re.findall(r"\d+", risk_id)
            if numbers:
                number = int(numbers[0])
                return f"AIR.{number:03d}"

        return None

    def normalize_control_id(self, control_id: str) -> Optional[str]:
        """
        Normalize a control ID to the standard format.

        Args:
            control_id: Raw control ID string

        Returns:
            Normalized control ID, or None if invalid
        """
        if not control_id:
            return None

        # Handle both string and numeric inputs (e.g., from Excel)
        if isinstance(control_id, (int, float)):
            control_id = str(control_id)
        elif not isinstance(control_id, str):
            return None

        # Clean the input
        control_id = str(control_id).strip()

        # Control IDs should start with AI and have a pattern like AIGPC.1
        if re.match(r"^AI[A-Z]{2,4}\.\d+$", control_id):
            return control_id

        if self.enforce_strict_format:
            logger.warning(f"Invalid control ID format: {control_id}")
            return None

        return control_id

    def normalize_question_id(self, question_id: str) -> Optional[str]:
        """
        Normalize a question ID to the standard format.

        Args:
            question_id: Raw question ID string

        Returns:
            Normalized question ID, or None if invalid
        """
        if not question_id:
            return None

        # Handle both string and numeric inputs (e.g., from Excel)
        if isinstance(question_id, (int, float)):
            question_id = str(question_id)
        elif not isinstance(question_id, str):
            return None

        # Clean the input
        question_id = str(question_id).strip()

        # Handle various question ID formats:
        # - OA1.1, CRA1.1, CREMIR1.1, etc. (prefix + number + subnumber)
        # - Q1, Q2, etc. (simple Q format)
        # - 1.1, 2.1, etc. (simple number.subnumber format)
        # - Just numbers

        # Check if it's already in a valid format (prefix + number + subnumber)
        if re.match(r"^[A-Z]{2,6}\d+\.\d+$", question_id):
            return question_id

        # Check if it's in Q format
        if re.match(r"^Q\d+$", question_id):
            return question_id

        # Check if it's in simple number.subnumber format (like 1.1, 2.1)
        if re.match(r"^\d+\.\d+$", question_id):
            return f"Q{question_id}"

        # Try to extract numbers and create a valid format
        numbers = re.findall(r"\d+", question_id)
        if numbers:
            # If we have two numbers, assume it's prefix.number.subnumber
            if len(numbers) >= 2:
                # Try to extract prefix from the original string
                prefix_match = re.match(r"^([A-Z]{2,6})", question_id)
                if prefix_match:
                    prefix = prefix_match.group(1)
                    return f"{prefix}{numbers[0]}.{numbers[1]}"
                else:
                    # Fallback to Q format with subnumber
                    return f"Q{numbers[0]}.{numbers[1]}"
            else:
                # Single number, use Q format
                return f"Q{numbers[0]}"

        if self.enforce_strict_format:
            logger.warning(f"Invalid question ID format: {question_id}")
            return None

        return question_id

    def create_id_mapping(self, old_ids: List[str], new_ids: List[str]) -> Dict[str, str]:
        """
        Create a mapping between old and new ID formats.

        Args:
            old_ids: List of old format IDs
            new_ids: List of new format IDs

        Returns:
            Dictionary mapping old IDs to new IDs
        """
        mapping = {}

        # Sort both lists to ensure consistent mapping
        old_sorted = sorted(old_ids)
        new_sorted = sorted(new_ids)

        # Create mapping based on position
        for i, old_id in enumerate(old_sorted):
            if i < len(new_sorted):
                mapping[old_id] = new_sorted[i]

        return mapping

    def validate_id_format(self, entity_id: str, entity_type: str) -> bool:
        """
        Validate that an ID matches the expected format for its entity type.

        Args:
            entity_id: ID to validate
            entity_type: Type of entity (risk, control, question)

        Returns:
            True if ID format is valid, False otherwise
        """
        if entity_type not in self.ID_PATTERNS:
            logger.warning(f"Unknown entity type: {entity_type}")
            return False

        pattern = self.ID_PATTERNS[entity_type]
        return bool(re.match(pattern, entity_id))

    def extract_id_number(self, entity_id: str, entity_type: str) -> Optional[int]:
        """
        Extract the numeric part from an entity ID.

        Args:
            entity_id: ID to extract number from
            entity_type: Type of entity (risk, control, question)

        Returns:
            Numeric part of the ID, or None if not found
        """
        if entity_type not in self.ID_PATTERNS:
            return None

        pattern = self.ID_PATTERNS[entity_type]
        match = re.match(pattern, entity_id)

        if match:
            return int(match.group(1))

        return None

    def normalize_mapping_ids(
        self, mappings: List[Dict[str, str]], id_field: str, entity_type: str
    ) -> List[Dict[str, str]]:
        """
        Normalize IDs in a list of mapping dictionaries.

        Args:
            mappings: List of mapping dictionaries
            id_field: Name of the field containing the ID
            entity_type: Type of entity (risk, control, question)

        Returns:
            List of mappings with normalized IDs
        """
        normalized_mappings = []

        for mapping in mappings:
            if id_field in mapping:
                original_id = mapping[id_field]

                if entity_type == "risk":
                    normalized_id = self.normalize_risk_id(original_id)
                elif entity_type == "control":
                    normalized_id = self.normalize_control_id(original_id)
                elif entity_type == "question":
                    normalized_id = self.normalize_question_id(original_id)
                else:
                    normalized_id = original_id

                if normalized_id:
                    normalized_mapping = mapping.copy()
                    normalized_mapping[id_field] = normalized_id
                    normalized_mappings.append(normalized_mapping)
                else:
                    logger.warning(f"Skipping mapping with invalid {entity_type} ID: {original_id}")

        return normalized_mappings

    def get_id_migration_report(self, old_ids: List[str], new_ids: List[str]) -> Dict[str, any]:
        """
        Generate a report on ID migration between old and new formats.

        Args:
            old_ids: List of old format IDs
            new_ids: List of new format IDs

        Returns:
            Dictionary containing migration statistics and issues
        """
        mapping = self.create_id_mapping(old_ids, new_ids)

        # Find unmapped IDs
        unmapped_old = [id for id in old_ids if id not in mapping]
        unmapped_new = [id for id in new_ids if id not in mapping.values()]

        return {
            "total_old_ids": len(old_ids),
            "total_new_ids": len(new_ids),
            "mapped_ids": len(mapping),
            "unmapped_old_ids": unmapped_old,
            "unmapped_new_ids": unmapped_new,
            "mapping": mapping,
            "migration_success_rate": (
                len(mapping) / max(len(old_ids), len(new_ids)) if max(len(old_ids), len(new_ids)) > 0 else 0
            ),
        }
