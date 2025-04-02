"""
Run DynaPort tests.

This script runs the DynaPort test suite using pytest.
"""

import os
import sys
import subprocess


def main():
    """Run the DynaPort tests."""
    print("Running DynaPort tests...")
    
    # Run pytest with coverage
    try:
        subprocess.run(
            [sys.executable, "-m", "pytest", "--cov=dynaport", "--cov-report=term"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("Tests failed")
        sys.exit(1)
    
    print("All tests passed!")


if __name__ == "__main__":
    main()
