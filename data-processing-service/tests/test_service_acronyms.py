"""
Test cases for service acronym functionality.

Tests the service name to acronym mapping and question ID generation
with acronyms to ensure consistency and correctness.
"""

from utils.service_acronyms import (
    ACRONYM_TO_SERVICE,
    SERVICE_ACRONYMS,
    get_service_acronym,
    get_service_from_acronym,
    normalize_service_name_for_id,
    validate_acronym_mapping,
)


class TestServiceAcronyms:
    """Test cases for service acronym functionality."""

    def test_service_acronym_mapping_completeness(self):
        """Test that all expected services have acronyms."""
        expected_services = [
            "Operational Assurance",
            "Cyber Risk Architecture",
            "CREM Platform & Automation",
            "IAM Engineering",
            "Security Threat Testing",
            "Technical Security Solutions",
            "Risk Engineering",
            "CREM Incident Response",
            "Security Risk Management",
            "IAM Operations",
        ]

        for service in expected_services:
            assert (
                service in SERVICE_ACRONYMS
            ), f"Service '{service}' missing from acronym mapping"
            acronym = SERVICE_ACRONYMS[service]
            assert acronym, f"Empty acronym for service '{service}'"
            assert isinstance(acronym, str), f"Acronym for '{service}' should be string"

    def test_acronym_uniqueness(self):
        """Test that all acronyms are unique."""
        acronyms = list(SERVICE_ACRONYMS.values())
        unique_acronyms = set(acronyms)

        assert len(acronyms) == len(
            unique_acronyms
        ), f"Duplicate acronyms found: {acronyms}"

        # Check for specific expected acronyms
        expected_acronyms = [
            "OA",
            "CRA",
            "CPA",
            "IAM",
            "STT",
            "TSS",
            "RE",
            "CIR",
            "SRM",
            "IAMO",
        ]
        for expected in expected_acronyms:
            assert expected in acronyms, f"Expected acronym '{expected}' not found"

    def test_acronym_format_validation(self):
        """Test that all acronyms follow proper format rules."""
        validation_results = validate_acronym_mapping()

        assert validation_results["all_unique"], "Acronyms should be unique"
        assert validation_results["all_uppercase"], "Acronyms should be uppercase"
        assert validation_results["no_spaces"], "Acronyms should not contain spaces"
        assert validation_results[
            "alphanumeric_only"
        ], "Acronyms should contain only alphanumeric characters"
        assert validation_results["all_valid"], "All validation checks should pass"

    def test_get_service_acronym(self):
        """Test the get_service_acronym function."""
        # Test known mappings
        assert get_service_acronym("Cyber Risk Architecture") == "CRA"
        assert get_service_acronym("Operational Assurance") == "OA"
        assert get_service_acronym("CREM Platform & Automation") == "CPA"

        # Test unknown service (should return as-is)
        unknown_service = "Unknown Service"
        assert get_service_acronym(unknown_service) == unknown_service

    def test_get_service_from_acronym(self):
        """Test the get_service_from_acronym function."""
        # Test known acronyms
        assert get_service_from_acronym("CRA") == "Cyber Risk Architecture"
        assert get_service_from_acronym("OA") == "Operational Assurance"
        assert get_service_from_acronym("CPA") == "CREM Platform & Automation"

        # Test unknown acronym (should return as-is)
        unknown_acronym = "UNK"
        assert get_service_from_acronym(unknown_acronym) == unknown_acronym

    def test_normalize_service_name_for_id(self):
        """Test the normalize_service_name_for_id function."""
        # Test known services
        assert normalize_service_name_for_id("Cyber Risk Architecture") == "CRA"
        assert normalize_service_name_for_id("Operational Assurance") == "OA"
        assert normalize_service_name_for_id("CREM Platform & Automation") == "CPA"

        # Test services with special characters
        assert normalize_service_name_for_id("IAM Engineering") == "IAM"
        assert normalize_service_name_for_id("Security Threat Testing") == "STT"

        # Test unknown service (should return normalized version)
        unknown_service = "Test Service 123"
        result = normalize_service_name_for_id(unknown_service)
        assert result == "TESTSERVICE123"  # Should be uppercase and alphanumeric only

    def test_reverse_mapping_consistency(self):
        """Test that reverse mapping is consistent."""
        for service, acronym in SERVICE_ACRONYMS.items():
            assert (
                ACRONYM_TO_SERVICE[acronym] == service
            ), f"Reverse mapping inconsistent for {acronym}"

        for acronym, service in ACRONYM_TO_SERVICE.items():
            assert (
                SERVICE_ACRONYMS[service] == acronym
            ), f"Forward mapping inconsistent for {service}"

    def test_acronym_length_reasonable(self):
        """Test that acronyms are reasonably short."""
        for service, acronym in SERVICE_ACRONYMS.items():
            assert len(acronym) <= 5, f"Acronym '{acronym}' for '{service}' is too long"
            assert (
                len(acronym) >= 2
            ), f"Acronym '{acronym}' for '{service}' is too short"

    def test_special_characters_handling(self):
        """Test handling of special characters in service names."""
        # Test services with ampersands
        assert normalize_service_name_for_id("CREM Platform & Automation") == "CPA"

        # Test services with spaces
        assert normalize_service_name_for_id("Cyber Risk Architecture") == "CRA"

        # Test services with multiple words
        assert normalize_service_name_for_id("Technical Security Solutions") == "TSS"

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test empty string
        assert normalize_service_name_for_id("") == ""

        # Test None (should handle gracefully)
        try:
            result = normalize_service_name_for_id(None)
            # Should either return empty string or raise appropriate exception
            assert result == "" or result is None
        except (TypeError, AttributeError):
            # This is acceptable behavior
            pass

        # Test very long service name (should return normalized version)
        long_service = "A" * 100
        result = normalize_service_name_for_id(long_service)
        # Should return the full normalized string (not truncated)
        assert result == "A" * 100

    def test_question_id_generation_samples(self):
        """Test sample question ID generation with acronyms."""
        test_cases = [
            ("Cyber Risk Architecture", "6.1", "Q.CRA.6.1"),
            ("Operational Assurance", "1.1", "Q.OA.1.1"),
            ("CREM Platform & Automation", "2.3", "Q.CPA.2.3"),
            ("IAM Engineering", "4.5", "Q.IAM.4.5"),
            ("Security Threat Testing", "3.2", "Q.STT.3.2"),
        ]

        for service_name, question_number, expected_id in test_cases:
            acronym = normalize_service_name_for_id(service_name)
            actual_id = f"Q.{acronym}.{question_number}"
            assert actual_id == expected_id, f"Expected {expected_id}, got {actual_id}"

    def test_acronym_collision_prevention(self):
        """Test that acronyms prevent ID collisions."""
        # Generate question IDs for all services with same question number
        question_number = "1.1"
        generated_ids = []

        for service_name in SERVICE_ACRONYMS.keys():
            acronym = normalize_service_name_for_id(service_name)
            question_id = f"Q.{acronym}.{question_number}"
            generated_ids.append(question_id)

        # All IDs should be unique
        assert len(generated_ids) == len(
            set(generated_ids)
        ), "Question IDs should be unique across services"

        # Verify no duplicates
        duplicates = [id for id in generated_ids if generated_ids.count(id) > 1]
        assert not duplicates, f"Duplicate question IDs found: {duplicates}"

    def test_backwards_compatibility(self):
        """Test that the acronym system maintains backwards compatibility."""
        # Test that we can still generate question IDs
        service_name = "Cyber Risk Architecture"
        question_number = "6.1"

        acronym = normalize_service_name_for_id(service_name)
        question_id = f"Q.{acronym}.{question_number}"

        # Should generate a valid question ID
        assert question_id.startswith("Q.")
        assert "." in question_id
        # Question number "6.1" contains a dot, so split will have 4 parts: Q, CRA, 6, 1
        assert (
            len(question_id.split(".")) == 4
        )  # Q.{acronym}.{number} where number is "6.1"

    def test_acronym_mapping_coverage(self):
        """Test that all services in the Excel file are covered."""
        # These are the actual sheet names from the Excel file
        excel_sheet_names = [
            "Operational Assurance",
            "Cyber Risk Architecture",
            "CREM Platform & Automation",
            "IAM Engineering",
            "Security Threat Testing",
            "Technical Security Solutions",
            "Risk Engineering",
            "CREM Incident Response",
            "Security Risk Management",
            "IAM Operations",
        ]

        for sheet_name in excel_sheet_names:
            acronym = get_service_acronym(sheet_name)
            assert acronym != sheet_name, f"No acronym mapping for '{sheet_name}'"
            assert (
                acronym in SERVICE_ACRONYMS.values()
            ), f"Acronym '{acronym}' not in mapping for '{sheet_name}'"
