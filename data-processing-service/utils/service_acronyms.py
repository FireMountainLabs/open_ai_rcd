"""
Service Name to Acronym Mapping

Provides mapping from full service/managing role names to their acronyms
for use in question ID generation.
"""

from typing import Dict

# Mapping from full service names to acronyms
SERVICE_ACRONYMS: Dict[str, str] = {
    "Operational Assurance": "OA",
    "Cyber Risk Architecture": "CRA",
    "CREM Platform & Automation": "CPA",
    "IAM Engineering": "IAM",
    "Security Threat Testing": "STT",
    "Technical Security Solutions": "TSS",
    "Risk Engineering": "RE",
    "CREM Incident Response": "CIR",
    "Security Risk Management": "SRM",
    "IAM Operations": "IAMO",
}

# Reverse mapping for validation
ACRONYM_TO_SERVICE: Dict[str, str] = {v: k for k, v in SERVICE_ACRONYMS.items()}


def get_service_acronym(service_name: str) -> str:
    """
    Get the acronym for a service name.

    Args:
        service_name: Full service name (e.g., "Cyber Risk Architecture")

    Returns:
        Service acronym (e.g., "CRA")
    """
    return SERVICE_ACRONYMS.get(service_name, service_name)


def get_service_from_acronym(acronym: str) -> str:
    """
    Get the full service name from an acronym.

    Args:
        acronym: Service acronym (e.g., "CRA")

    Returns:
        Full service name (e.g., "Cyber Risk Architecture")
    """
    return ACRONYM_TO_SERVICE.get(acronym, acronym)


def normalize_service_name_for_id(service_name: str) -> str:
    """
    Normalize a service name for use in question IDs.

    Args:
        service_name: Full service name

    Returns:
        Normalized acronym for use in IDs
    """
    # Get the acronym
    acronym = get_service_acronym(service_name)

    # Ensure it's uppercase and contains only letters/numbers
    normalized = "".join(c for c in acronym.upper() if c.isalnum())

    return normalized


def validate_acronym_mapping() -> Dict[str, bool]:
    """
    Validate that all acronyms are unique and properly formatted.

    Returns:
        Dictionary with validation results
    """
    results = {
        "all_unique": len(SERVICE_ACRONYMS.values()) == len(set(SERVICE_ACRONYMS.values())),
        "all_uppercase": all(acronym.isupper() for acronym in SERVICE_ACRONYMS.values()),
        "no_spaces": all(" " not in acronym for acronym in SERVICE_ACRONYMS.values()),
        "alphanumeric_only": all(acronym.isalnum() for acronym in SERVICE_ACRONYMS.values()),
    }

    results["all_valid"] = all(results.values())

    return results


if __name__ == "__main__":
    # Test the mapping
    print("Service Name to Acronym Mapping:")
    print("=" * 40)
    for service, acronym in SERVICE_ACRONYMS.items():
        print(f"{service:30} → {acronym}")

    print("\nValidation Results:")
    print("=" * 40)
    validation = validate_acronym_mapping()
    for check, result in validation.items():
        status = "✅" if result else "❌"
        print(f"{check:20} {status}")

    print("\nSample Question ID Generation:")
    print("=" * 40)
    test_services = [
        "Cyber Risk Architecture",
        "Operational Assurance",
        "CREM Platform & Automation",
    ]
    for service in test_services:
        acronym = normalize_service_name_for_id(service)
        sample_id = f"Q.{acronym}.1.1"
        print(f"{service:30} → {sample_id}")
