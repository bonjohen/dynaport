"""
Run DynaPort examples.

This script provides a menu to run different DynaPort examples.
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the DynaPort examples header."""
    clear_screen()
    print("=" * 60)
    print("             DynaPort Examples Runner                ")
    print("=" * 60)
    print()


def print_menu():
    """Print the examples menu."""
    print("Available examples:")
    print("  1. Simple Flask Application")
    print("  2. Flask Application Factory Pattern")
    print("  3. Multi-Instance Application")
    print("  4. Service Discovery")
    print("  5. Web Dashboard")
    print("  0. Exit")
    print()


def run_example(example_script):
    """
    Run an example script.
    
    Args:
        example_script: Path to the example script
    """
    print(f"Running {example_script}...")
    print("-" * 60)
    
    try:
        # Get the directory containing the example script
        script_dir = Path(example_script).parent
        
        # Run the example
        process = subprocess.Popen(
            [sys.executable, example_script],
            cwd=script_dir
        )
        
        # Wait for the user to press Enter to stop the example
        input("Press Enter to stop the example...")
        
        # Terminate the process
        process.terminate()
        process.wait(timeout=5)
        
    except KeyboardInterrupt:
        print("\nExample stopped by user")
    except Exception as e:
        print(f"Error running example: {e}")
    
    print("-" * 60)
    input("Press Enter to return to the menu...")


def main():
    """Run the examples menu."""
    examples_dir = Path(__file__).parent
    
    while True:
        print_header()
        print_menu()
        
        choice = input("Enter your choice (0-5): ")
        
        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            run_example(examples_dir / "simple_app.py")
        elif choice == "2":
            run_example(examples_dir / "factory_app.py")
        elif choice == "3":
            run_example(examples_dir / "multi_instance.py")
        elif choice == "4":
            run_example(examples_dir / "service_discovery.py")
        elif choice == "5":
            run_example(examples_dir / "run_dashboard.py")
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    main()
