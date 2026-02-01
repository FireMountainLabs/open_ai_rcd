#!/usr/bin/env python3
"""
Test runner for the dashboard service.

This script provides different test execution modes and can be used for
local development and CI/CD pipelines.
"""

import sys
import subprocess
import argparse
import os
from pathlib import Path


def run_tests(
    test_type="all", verbose=False, coverage=False, parallel=False, markers=None
):
    """
    Run tests with specified configuration.

    Args:
        test_type: Type of tests to run (unit, integration, e2e, all)
        verbose: Enable verbose output
        coverage: Generate coverage report
        parallel: Run tests in parallel
        markers: Specific pytest markers to run
    """
    # Get the test directory
    test_dir = Path(__file__).parent

    # Build pytest command
    cmd = ["python", "-m", "pytest"]

    # Add test directory
    cmd.append(str(test_dir))

    # Add verbosity
    if verbose:
        cmd.extend(["-v", "-s"])

    # Add coverage
    if coverage:
        cmd.extend(["--cov=../", "--cov-report=html", "--cov-report=term"])

    # Add parallel execution
    if parallel:
        cmd.extend(["-n", "auto"])

    # Add markers
    if markers:
        cmd.extend(["-m", markers])
    elif test_type != "all":
        cmd.extend(["-m", test_type])

    # Add other useful options
    cmd.extend(["--tb=short", "--strict-markers", "--disable-warnings"])

    print(f"Running command: {' '.join(cmd)}")

    # Run the tests
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Tests failed with exit code {e.returncode}")
        return e.returncode


def run_launcher_tests():
    """Run tests that require the launcher."""
    print("Running launcher-based tests...")
    print("This will start the full system using the launcher.")

    # Check if launcher exists
    launcher_path = Path(__file__).parent.parent.parent / "launch_dataviewer"
    if not launcher_path.exists():
        print(f"Error: Launcher not found at {launcher_path}")
        return 1

    # Run integration and e2e tests
    return run_tests(
        test_type="integration or e2e", verbose=True, coverage=False, parallel=False
    )


def run_unit_tests():
    """Run unit tests only."""
    print("Running unit tests...")
    return run_tests(test_type="unit", verbose=True, coverage=True, parallel=True)


def run_integration_tests():
    """Run integration tests only."""
    print("Running integration tests...")
    return run_tests(
        test_type="integration", verbose=True, coverage=False, parallel=False
    )


def run_e2e_tests():
    """Run end-to-end tests only."""
    print("Running end-to-end tests...")
    return run_tests(test_type="e2e", verbose=True, coverage=False, parallel=False)


def run_quick_tests():
    """Run quick tests (unit tests only, no launcher)."""
    print("Running quick tests (unit tests only)...")
    return run_tests(test_type="unit", verbose=True, coverage=True, parallel=True)


def run_all_tests():
    """Run all tests."""
    print("Running all tests...")
    return run_tests(test_type="all", verbose=True, coverage=True, parallel=False)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Dashboard Service Test Runner")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "launcher", "quick", "all"],
        help="Type of tests to run",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--parallel", "-p", action="store_true", help="Run tests in parallel"
    )
    parser.add_argument("--markers", "-m", help="Specific pytest markers to run")

    args = parser.parse_args()

    # Set working directory to the dashboard service directory
    os.chdir(Path(__file__).parent.parent)

    # Run tests based on type
    if args.test_type == "unit":
        return run_unit_tests()
    elif args.test_type == "integration":
        return run_integration_tests()
    elif args.test_type == "e2e":
        return run_e2e_tests()
    elif args.test_type == "launcher":
        return run_launcher_tests()
    elif args.test_type == "quick":
        return run_quick_tests()
    elif args.test_type == "all":
        return run_all_tests()
    else:
        print(f"Unknown test type: {args.test_type}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
