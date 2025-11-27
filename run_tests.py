#!/usr/bin/env python3
"""
Test runner script for Simple Contacts application.
Provides convenient commands for running different types of tests.
"""

import sys
import subprocess
import argparse


def run_command(command, description):
    """Run a command and handle output"""
    print(f"\n🧪 {description}")
    print("=" * 50)

    try:
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Test runner for Simple Contacts")
    parser.add_argument("--quick", "-q", action="store_true",
                        help="Run quick tests only (no integration tests)")
    parser.add_argument("--coverage", "-c", action="store_true",
                        help="Run tests with coverage report")
    parser.add_argument("--integration", "-i", action="store_true",
                        help="Run integration tests only")
    parser.add_argument("--unit", "-u", action="store_true",
                        help="Run unit tests only")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose output")

    args = parser.parse_args()

    # Base pytest command
    pytest_cmd = "python -m pytest"

    # Add verbosity
    if args.verbose:
        pytest_cmd += " -v"

    # Add coverage if requested
    if args.coverage:
        pytest_cmd += " --cov=. --cov-report=term-missing --cov-report=html"

    # Determine which tests to run
    if args.quick:
        pytest_cmd += ' -m "not slow" tests/test_routes.py tests/test_models.py'
        description = "Quick Tests (Routes & Models)"
    elif args.integration:
        pytest_cmd += " tests/test_integration.py"
        description = "Integration Tests"
    elif args.unit:
        pytest_cmd += " tests/test_routes.py tests/test_models.py"
        description = "Unit Tests"
    else:
        pytest_cmd += " tests/"
        description = "All Tests"

    print("🚀 Simple Contacts Test Runner")
    print("=" * 50)
    print(f"Running: {description}")
    print(f"Command: {pytest_cmd}")

    # Run the tests
    success = run_command(pytest_cmd, description)

    if success:
        print("\n🎉 All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
