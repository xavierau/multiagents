#!/usr/bin/env python
"""
Test runner for the MultiAgents framework.
Provides convenient commands for running different test suites.
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd: list, verbose: bool = True) -> int:
    """Run a command and return the exit code."""
    if verbose:
        print(f"Running: {' '.join(cmd)}")
        print("-" * 80)
    
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="MultiAgents test runner")
    parser.add_argument(
        "suite",
        choices=["all", "unit", "integration", "e2e", "load", "coverage", "fast"],
        help="Test suite to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Number of parallel workers"
    )
    parser.add_argument(
        "--marker", "-m",
        help="Run tests matching given mark expression"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["pytest"]
    
    # Add verbose flag
    if args.verbose:
        cmd.append("-vv")
    
    # Add failfast flag
    if args.failfast:
        cmd.append("-x")
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add custom marker
    if args.marker:
        cmd.extend(["-m", args.marker])
    
    # Configure based on test suite
    if args.suite == "all":
        # Run all tests with coverage
        cmd.extend(["tests/", "--cov=multiagents", "--cov-report=term-missing"])
        
    elif args.suite == "unit":
        # Run only unit tests
        cmd.extend(["tests/unit/", "-m", "not integration"])
        
    elif args.suite == "integration":
        # Run only integration tests
        cmd.extend(["tests/integration/", "-m", "integration"])
        
    elif args.suite == "e2e":
        # Run end-to-end tests
        cmd.extend(["tests/integration/test_end_to_end.py", "-m", "e2e"])
        
    elif args.suite == "load":
        # Run load tests using the dedicated runner
        import subprocess
        import sys
        print("Starting load test runner...")
        result = subprocess.run([
            sys.executable, "tests/load/load_test_runner.py", "benchmark"
        ])
        return result.returncode
        
    elif args.suite == "coverage":
        # Run with detailed coverage report
        cmd.extend([
            "tests/",
            "--cov=multiagents",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml:coverage.xml"
        ])
        
    elif args.suite == "fast":
        # Run fast tests only (exclude slow and integration)
        cmd.extend(["tests/", "-m", "not slow and not integration"])
    
    # Run the command
    exit_code = run_command(cmd, verbose=True)
    
    # Print coverage report location if applicable
    if args.suite in ["all", "coverage"]:
        print("\n" + "=" * 80)
        print("Coverage report generated:")
        print("  - Terminal: See above")
        print("  - HTML: htmlcov/index.html")
        if args.suite == "coverage":
            print("  - XML: coverage.xml")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())