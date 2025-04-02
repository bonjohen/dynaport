"""
Test DynaPort installation.

This script runs a simple test to verify that DynaPort is installed correctly.
"""

import sys
import subprocess


def main():
    """Run the DynaPort installation test."""
    print("Testing DynaPort installation...")
    
    try:
        subprocess.run(
            [sys.executable, "tests/test_installation.py"],
            check=True
        )
    except subprocess.CalledProcessError:
        print("Installation test failed")
        sys.exit(1)
    
    print("Installation test passed!")


if __name__ == "__main__":
    main()
