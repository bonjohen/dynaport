"""
Run DynaPort examples.

This script provides a menu to run different DynaPort examples,
showcasing the framework-agnostic approach.
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
    print("  1. Framework-Agnostic HTTP Server")
    print("  2. Framework-Agnostic Socket Server")
    print("  3. Node.js Express Application")
    print("  4. Flask Simple Application")
    print("  5. Flask Application Factory Pattern")
    print("  6. Multi-Instance Application")
    print("  7. Service Discovery")
    print("  8. Web Dashboard")
    print("  0. Exit")
    print()


def run_python_example(example_script):
    """
    Run a Python example script.

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


def run_nodejs_example():
    """Run the Node.js example."""
    print("Running Node.js Express example...")
    print("-" * 60)

    try:
        # Get the directory containing the example
        example_dir = Path("examples/nodejs_example")

        if not example_dir.exists():
            print(f"Error: Example directory {example_dir} not found")
            return

        # Check if Node.js is installed
        try:
            subprocess.run(
                ["node", "--version"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            print("Error: Node.js is not installed or not in PATH")
            print("Please install Node.js to run this example")
            return

        # Check if dependencies are installed
        if not (example_dir / "node_modules").exists():
            print("Installing Node.js dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=example_dir,
                check=True
            )

        # Run the example
        process = subprocess.Popen(
            ["node", "server.js"],
            cwd=example_dir
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
    examples_dir = Path("examples")

    while True:
        print_header()
        print_menu()

        choice = input("Enter your choice (0-8): ")

        if choice == "0":
            print("Exiting...")
            break
        elif choice == "1":
            run_python_example(examples_dir / "framework_agnostic_demo.py")
        elif choice == "2":
            run_python_example(examples_dir / "generic_app.py")
        elif choice == "3":
            run_nodejs_example()
        elif choice == "4":
            run_python_example(examples_dir / "simple_app.py")
        elif choice == "5":
            run_python_example(examples_dir / "factory_app.py")
        elif choice == "6":
            run_python_example(examples_dir / "multi_instance.py")
        elif choice == "7":
            run_python_example(examples_dir / "service_discovery.py")
        elif choice == "8":
            run_python_example("run_dashboard.py")
        else:
            print("Invalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    main()
