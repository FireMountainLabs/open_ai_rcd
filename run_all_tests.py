#!/usr/bin/env python3
"""
Test runner script for all services in the dashboard_zero project.
This script runs tests for each service individually to avoid conftest.py conflicts.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_tests_for_service(service_name, service_path):
    """Run tests for a specific service."""
    print(f"\n{'=' * 60}")
    print(f"Running tests for {service_name}")
    print(f"{'=' * 60}")

    # Change to service directory
    original_dir = os.getcwd()
    os.chdir(service_path)

    try:
        # Run pytest for this service
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/",
                "-v",
                "--tb=short",
                "--color=yes",
            ],
            capture_output=False,
        )

        return result.returncode == 0

    except Exception as e:
        print(f"Error running tests for {service_name}: {e}")
        return False
    finally:
        os.chdir(original_dir)


def main():
    """Run tests for all services."""
    project_root = Path(__file__).parent

    # Define services and their test directories
    services = [
        ("Dashboard Service", project_root / "dashboard-service"),
        ("Data Processing Service", project_root / "data-processing-service"),
        ("Database Service", project_root / "database-service"),
    ]

    print("Dashboard Zero - Multi-Service Test Runner")
    print("=" * 60)
    print("Running tests for each service individually to avoid conflicts...")

    results = {}
    all_passed = True

    for service_name, service_path in services:
        if service_path.exists() and (service_path / "tests").exists():
            success = run_tests_for_service(service_name, service_path)
            results[service_name] = success
            if not success:
                all_passed = False
        else:
            print(f"Skipping {service_name} - no tests directory found")
            results[service_name] = None

    # Print summary
    print(f"\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")

    for service_name, success in results.items():
        if success is None:
            status = "SKIPPED"
        elif success:
            status = "PASSED"
        else:
            status = "FAILED"
        print(f"{service_name:<25} : {status}")

    if all_passed:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
