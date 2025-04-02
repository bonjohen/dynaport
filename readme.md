# DynaPort - Framework-Agnostic Dynamic Port Management System

A Python-based system for managing concurrent applications with automatic port allocation and configuration management. DynaPort works with any application or framework that needs network ports.

## Features
- Automatic port detection and allocation
- Persistent port assignments
- Configuration management for multiple environments
- Service discovery and health monitoring
- Web interface for service management
- Command-line tools for port management
- Framework-agnostic core functionality
- Adapters for popular frameworks (Flask, Django, FastAPI)
- Support for non-Python applications via CLI

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

### Framework-Agnostic Usage

```python
from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo

# Create a port allocator
allocator = PortAllocator()

# Allocate a port for your application
app_id = "my-app"
instance_id = "default"
port = allocator.allocate_port(f"{app_id}:{instance_id}")

print(f"Allocated port {port} for {app_id}")

# Register the service (optional)
registry = ServiceRegistry()
service = ServiceInfo(
    app_id=app_id,
    instance_id=instance_id,
    name="My Application",
    port=port,
    health_check_type="tcp"  # or "http", "command", "custom"
)
registry.register_service(service)

# Use the port in your application
try:
    # Start your application on the allocated port
    # ...

    # Update service status
    registry.update_service_status(app_id, instance_id, "running")

    # Wait for your application to finish
    # ...
finally:
    # Clean up
    registry.update_service_status(app_id, instance_id, "stopped")
    registry.unregister_service(app_id, instance_id)
    allocator.release_port(f"{app_id}:{instance_id}")
```

### Using with Flask

```python
from flask import Flask, jsonify
from dynaport.adapters.flask_adapter import DynaPortFlask

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

### Using with Node.js

```javascript
const express = require('express');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);
const app = express();

// Add routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy' });
});

async function main() {
  // Use DynaPort CLI to allocate a port
  const { stdout } = await execAsync('dynaport port allocate nodejs-app');
  const portMatch = stdout.match(/PORT=(\d+)/);
  const port = portMatch[1];

  // Register the service
  await execAsync(
    `dynaport service register nodejs-app ${port} ` +
    `--name "Node.js App" --health-endpoint /health --technology nodejs`
  );

  // Start the server
  app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
    exec('dynaport service status nodejs-app running');
  });
}

main();
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

# Register a service with a specific technology
dynaport service register nodejs-app 3000 --technology nodejs --health-check-type tcp

# List all registered services
dynaport service list

# List services by technology
dynaport service list --technology flask

# List available adapters
dynaport adapter list

# Get information about an adapter
dynaport adapter info flask
```

## Examples

Check out the `examples` directory for more examples:

- `generic_app.py`: Framework-agnostic usage with a simple socket server
- `nodejs_example`: Using DynaPort with a Node.js Express application
- `simple_app.py`: Basic Flask application with DynaPort
- `factory_app.py`: Using the Flask application factory pattern
- `multi_instance.py`: Running multiple instances of the same application
- `service_discovery.py`: Using service discovery to find and communicate with other services

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.