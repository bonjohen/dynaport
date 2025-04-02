"""
Test script to verify the DynaPort installation.

This script tests the basic functionality of DynaPort by:
1. Allocating a port
2. Creating a simple Flask application
3. Running the application on the allocated port
4. Verifying that the application is accessible
"""

import sys
import time
import threading
import requests
from flask import Flask, jsonify

from dynaport.core.port_allocator import PortAllocator
from dynaport.adapters.flask_adapter import DynaPortFlask


def create_test_app():
    """Create a simple test Flask application."""
    app = Flask(__name__)

    @app.route('/')
    def index():  # pylint: disable=unused-variable
        return jsonify({
            "message": "DynaPort test successful!",
            "status": "ok"
        })

    return app


def run_test_app(app, port, ready_event):
    """Run the test application in a separate thread."""
    def run():
        # Use the port from the app's config if not specified
        actual_port = port or app.config.get('PORT', 5000)
        app.run(host='127.0.0.1', port=actual_port)

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()

    # Wait for the application to start
    max_attempts = 10
    for _ in range(max_attempts):
        try:
            # Use the port from the app's config if not specified
            actual_port = port or app.config.get('PORT', 5000)
            response = requests.get(f"http://127.0.0.1:{actual_port}/")
            if response.status_code == 200:
                ready_event.set()
                break
        except requests.RequestException:
            pass

        time.sleep(0.5)

    return thread


def test_port_allocation():
    """Test port allocation."""
    print("Testing port allocation...")

    allocator = PortAllocator()
    port = allocator.find_available_port()

    print(f"Found available port: {port}")

    # Allocate the port for a test application
    app_id = "dynaport-test"
    allocated_port = allocator.allocate_port(app_id, port)

    print(f"Allocated port {allocated_port} for {app_id}")

    # Verify the port is allocated
    assigned_port = allocator.get_assigned_port(app_id)
    assert assigned_port == allocated_port, f"Expected port {allocated_port}, got {assigned_port}"

    print("Port allocation test passed!")

    # Release the port
    allocator.release_port(app_id)

    # Use the allocated port for the next test
    if allocated_port is None:
        allocated_port = 8000

    # Store the port for use in other tests
    test_port_allocation.port = allocated_port

    # Don't return a value (use assert instead)
    assert allocated_port > 0, "Port should be a positive number"


def test_flask_integration():
    """Test Flask integration."""
    print("Testing Flask integration...")

    # Get the port from the previous test
    port = getattr(test_port_allocation, 'port', None)

    # Create a Flask application
    app = create_test_app()

    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="dynaport-test",
        name="DynaPort Test App",
        preferred_port=port
    )

    # Wrap the Flask app with DynaPort
    dynaport.wrap_app(app)

    # Verify the port was allocated
    if port is not None:
        assert dynaport.port == port, f"Expected port {port}, got {dynaport.port}"
    else:
        assert dynaport.port > 0, f"Expected a positive port number, got {dynaport.port}"

    # Start the application
    ready_event = threading.Event()
    _ = run_test_app(app, port, ready_event)  # We don't need the thread object

    # Wait for the application to start
    if not ready_event.wait(timeout=5):
        print("Error: Application failed to start")
        sys.exit(1)

    # Test the application
    try:
        # Use the port from the app's config
        actual_port = dynaport.port
        response = requests.get(f"http://127.0.0.1:{actual_port}/")
        assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"

        data = response.json()
        assert data["message"] == "DynaPort test successful!", f"Unexpected message: {data['message']}"
        assert data["status"] == "ok", f"Unexpected status: {data['status']}"

        print("Flask integration test passed!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        # Clean up
        dynaport.shutdown()


def main():
    """Run the installation tests."""
    print("Testing DynaPort installation...")

    try:
        # Test port allocation
        port = test_port_allocation()

        # Test Flask integration
        test_flask_integration(port)

        print("\nAll tests passed! DynaPort is installed correctly.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
