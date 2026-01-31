#!/usr/bin/env python3
"""
Test runner for Database Service.

Automated test execution and reporting utilities.
"""

import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any


class DatabaseServiceTestRunner:
    """Test runner for database service tests."""

    def __init__(self, test_dir: Path = None):
        self.test_dir = test_dir or Path(__file__).parent
        self.results = {}

    def run_unit_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run unit tests."""
        print("Running unit tests...")
        cmd = ["python", "-m", "pytest", str(self.test_dir / "test_endpoints.py")]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "unit",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_integration_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run integration tests."""
        print("Running integration tests...")
        cmd = ["python", "-m", "pytest", str(self.test_dir / "test_integration.py")]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "integration",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_e2e_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run end-to-end tests."""
        print("Running end-to-end tests...")
        cmd = ["python", "-m", "pytest", str(self.test_dir / "test_e2e.py")]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "e2e",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_all_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run all tests."""
        print("Running all tests...")
        cmd = ["python", "-m", "pytest", str(self.test_dir)]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "all",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_coverage_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run tests with coverage reporting."""
        print("Running tests with coverage...")
        cmd = [
            "python",
            "-m",
            "pytest",
            "--cov=/home/fml/dashboard_zero/database-service",
            "--cov-report=html",
            "--cov-report=term",
            str(self.test_dir),
        ]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "coverage",
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_specific_test(
        self, test_name: str, verbose: bool = False
    ) -> Dict[str, Any]:
        """Run a specific test."""
        print(f"Running specific test: {test_name}")
        cmd = ["python", "-m", "pytest", f"{self.test_dir}::{test_name}"]
        if verbose:
            cmd.append("-v")

        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()

        return {
            "type": "specific",
            "test_name": test_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "duration": end_time - start_time,
            "success": result.returncode == 0,
        }

    def run_tests_by_type(
        self, test_type: str, verbose: bool = False
    ) -> Dict[str, Any]:
        """Run tests by type."""
        if test_type == "unit":
            return self.run_unit_tests(verbose)
        elif test_type == "integration":
            return self.run_integration_tests(verbose)
        elif test_type == "e2e":
            return self.run_e2e_tests(verbose)
        elif test_type == "all":
            return self.run_all_tests(verbose)
        elif test_type == "coverage":
            return self.run_coverage_tests(verbose)
        else:
            raise ValueError(f"Unknown test type: {test_type}")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a test report."""
        report = []
        report.append("=" * 60)
        report.append("DATABASE SERVICE TEST REPORT")
        report.append("=" * 60)
        report.append(f"Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        total_tests = 0
        passed_tests = 0
        total_duration = 0

        for test_type, result in results.items():
            if isinstance(result, dict) and "type" in result:
                report.append(f"Test Type: {result['type'].upper()}")
                report.append(f"Status: {'PASSED' if result['success'] else 'FAILED'}")
                report.append(f"Duration: {result['duration']:.2f}s")
                report.append(f"Return Code: {result['returncode']}")

                if result["stdout"]:
                    report.append("Output:")
                    report.append(result["stdout"])

                if result["stderr"]:
                    report.append("Errors:")
                    report.append(result["stderr"])

                report.append("-" * 40)

                total_tests += 1
                if result["success"]:
                    passed_tests += 1
                total_duration += result["duration"]

        report.append("SUMMARY:")
        report.append(f"Total Test Suites: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {total_tests - passed_tests}")
        report.append(f"Total Duration: {total_duration:.2f}s")
        report.append(
            f"Success Rate: {(passed_tests / total_tests * 100):.1f}%"
            if total_tests > 0
            else "N/A"
        )

        return "\n".join(report)

    def save_report(self, report: str, filename: str = None) -> Path:
        """Save test report to file."""
        if filename is None:
            filename = f"test_report_{int(time.time())}.txt"

        report_path = self.test_dir / filename
        with open(report_path, "w") as f:
            f.write(report)

        print(f"Test report saved to: {report_path}")
        return report_path

    def run_and_report(
        self, test_types: List[str], verbose: bool = False, save: bool = True
    ) -> Dict[str, Any]:
        """Run tests and generate report."""
        results = {}

        for test_type in test_types:
            print(f"\n{'=' * 20} {test_type.upper()} TESTS {'=' * 20}")
            try:
                result = self.run_tests_by_type(test_type, verbose)
                results[test_type] = result

                if result["success"]:
                    print(f"✅ {test_type.upper()} tests PASSED")
                else:
                    print(f"❌ {test_type.upper()} tests FAILED")
                    print(f"Return code: {result['returncode']}")
                    if result["stderr"]:
                        print(f"Error output: {result['stderr']}")

            except Exception as e:
                print(f"❌ Error running {test_type} tests: {e}")
                results[test_type] = {
                    "type": test_type,
                    "success": False,
                    "error": str(e),
                    "duration": 0,
                }

        # Generate and save report
        report = self.generate_report(results)
        print("\n" + report)

        if save:
            self.save_report(report)

        return results


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Database Service Test Runner")
    parser.add_argument(
        "--type",
        choices=["unit", "integration", "e2e", "all", "coverage"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--no-save", action="store_true", help="Don't save report to file"
    )
    parser.add_argument("--test-name", help="Run specific test by name")
    parser.add_argument(
        "--types",
        nargs="+",
        choices=["unit", "integration", "e2e", "all", "coverage"],
        help="Run multiple test types",
    )

    args = parser.parse_args()

    runner = DatabaseServiceTestRunner()

    if args.test_name:
        # Run specific test
        result = runner.run_specific_test(args.test_name, args.verbose)
        print(f"Test result: {'PASSED' if result['success'] else 'FAILED'}")
        if not result["success"] and result["stderr"]:
            print(f"Error: {result['stderr']}")
        sys.exit(0 if result["success"] else 1)

    if args.types:
        # Run multiple test types
        results = runner.run_and_report(args.types, args.verbose, not args.no_save)
        all_passed = all(result.get("success", False) for result in results.values())
        sys.exit(0 if all_passed else 1)
    else:
        # Run single test type
        result = runner.run_tests_by_type(args.type, args.verbose)
        print(f"Test result: {'PASSED' if result['success'] else 'FAILED'}")
        if not result["success"] and result["stderr"]:
            print(f"Error: {result['stderr']}")
        sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
