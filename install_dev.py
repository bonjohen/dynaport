"""
Install DynaPort in development mode.

This script installs the DynaPort package in development mode,
making it available for use in the current Python environment.
"""

import sys
import subprocess


def main():
    """Install DynaPort in development mode."""
    print("Installing DynaPort in development mode...")

    try:
        # Install package in development mode
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            check=True
        )

        # Install test dependencies
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )

        print("Installation successful!")
        print("You can now use DynaPort in your Python environment.")
        print("Run 'python run_examples.py' to try the examples.")
        print("Run 'python run_dashboard.py' to start the web dashboard.")
        print("Run 'python -m pytest' to run the tests.")
        print("\nFramework-agnostic usage:")
        print("  dynaport port allocate my-app")
        print("  dynaport service list")
        print("  dynaport adapter list")
    except subprocess.CalledProcessError:
        print("Installation failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
