# DynaPort - Dynamic Port Management System

A Python-based system for managing concurrent Flask applications with automatic port allocation and configuration management.

## Features
- Automatic port detection and allocation
- Persistent port assignments
- Configuration management for multiple environments
- Service discovery and health monitoring
- Web interface for service management
- Command-line tools for port management

## Requirements
See [requirements.md](requirements.md) for detailed project requirements.

## Installation

```bash
# Install from source
git clone https://github.com/example/dynaport.git
cd dynaport
pip install -e .

# Or install directly from PyPI (when available)
pip install dynaport
```

## Quick Start

### Basic Usage with Flask

```python
from flask import Flask, jsonify
from dynaport.flask_integration import DynaPortFlask

# Create a Flask application
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "Hello from DynaPort!",
        "port": app.config.get('PORT', 'unknown')
    })

if __name__ == '__main__':
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="my-app",
        name="My Application"
    )

    # Wrap the Flask app with DynaPort
    dynaport.wrap_app(app)

    # Run the app on the allocated port
    print(f"Running on port {dynaport.port}")
    dynaport.run_app(debug=True)
```

### Command-Line Interface

DynaPort provides a command-line interface for managing ports and services:

```bash
# Allocate a port for an application
dynaport port allocate my-app

# Get the port allocated to an application
dynaport port get my-app

# List all port allocations
dynaport port list

# Register a service
dynaport service register my-app 8000 --name "My Application" --health-endpoint /health

# List all registered services
dynaport service list
```

## Examples

Check out the `examples` directory for more examples:

- `simple_app.py`: Basic Flask application with DynaPort
- `factory_app.py`: Using the Flask application factory pattern
- `multi_instance.py`: Running multiple instances of the same application
- `service_discovery.py`: Using service discovery to find and communicate with other services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.