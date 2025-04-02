# DynaPort: Dynamic Port Management for Flask Applications

## Introduction

Modern web development often involves running multiple services simultaneously during development. Flask developers frequently encounter the frustrating "Address already in use" error when trying to run multiple applications on the same port. This leads to a poor development experience, requiring manual port management, frequent application restarts, and difficulty maintaining consistent port assignments across development sessions.

DynaPort solves these challenges by providing an intelligent port management system specifically designed for Flask applications. This document explains why you should use DynaPort and provides a comprehensive guide on how to integrate it into your development workflow.

## Why Use DynaPort?

### The Problem

When developing Flask applications, you often face these common challenges:

1. **Port Conflicts**: Running multiple Flask applications simultaneously leads to port conflicts
2. **Manual Port Management**: Developers must manually assign different ports to each application
3. **Inconsistent Port Assignments**: Port assignments change between development sessions
4. **Service Discovery Complexity**: Applications that need to communicate with each other require manual configuration
5. **Configuration Management**: Managing different configurations for development, testing, and production environments
6. **Health Monitoring**: Lack of visibility into which services are running and their health status

### The Solution: DynaPort

DynaPort addresses these challenges with a comprehensive set of features:

1. **Automatic Port Allocation**: Intelligently assigns available ports to applications
2. **Persistent Port Assignments**: Maintains consistent port assignments across restarts
3. **Configuration Management**: Handles environment-specific and instance-specific configurations
4. **Service Registry**: Provides service discovery capabilities for inter-service communication
5. **Health Monitoring**: Tracks service health and status
6. **Web Dashboard**: Offers a visual interface for monitoring and managing services
7. **Command-Line Interface**: Enables scripting and automation of port management tasks

### Key Benefits

- **Improved Developer Experience**: No more port conflicts or manual port management
- **Increased Productivity**: Less time spent on configuration, more time on development
- **Better Collaboration**: Consistent port assignments across team members
- **Enhanced Visibility**: Clear overview of running services and their status
- **Simplified Microservices Development**: Easier service discovery and communication
- **Flexible Configuration**: Support for different environments and instances

## How to Use DynaPort

### Installation

```bash
# Install from PyPI (when available)
pip install dynaport

# Or install from source
git clone https://github.com/example/dynaport.git
cd dynaport
pip install -e .
```

### Basic Integration with Flask

The simplest way to use DynaPort is to integrate it with your existing Flask application:

```python
from flask import Flask, jsonify
from dynaport.flask_integration import DynaPortFlask

# Create your Flask application as usual
app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({
        "message": "Hello from my app!",
        "port": app.config.get('PORT')
    })

if __name__ == '__main__':
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="my-app",           # Unique identifier for your app
        name="My Application"      # Human-readable name
    )
    
    # Wrap your Flask app with DynaPort
    dynaport.wrap_app(app)
    
    # Run the app on the allocated port
    print(f"Running on port {dynaport.port}")
    dynaport.run_app(debug=True)
```

With this simple integration, DynaPort will:
1. Automatically allocate an available port
2. Register the service in its registry
3. Add health check endpoints
4. Run the Flask app on the allocated port

### Using the Application Factory Pattern

If you're using Flask's application factory pattern:

```python
from flask import Flask, jsonify
from dynaport.flask_integration import create_dynaport_app

def create_app(config=None):
    """Create and configure a Flask application."""
    app = Flask(__name__)
    
    if config:
        app.config.from_mapping(config)
    
    @app.route('/')
    def index():
        return jsonify({
            "message": "Hello from my app!",
            "port": app.config.get('PORT')
        })
    
    return app

if __name__ == '__main__':
    # Create Flask app with DynaPort integration
    app = create_dynaport_app(
        app_id="factory-app",
        app_factory=create_app,
        name="Factory Pattern App"
    )
    
    # Access the DynaPort instance
    dynaport = app.dynaport
    
    # Run the app
    print(f"Running on port {dynaport.port}")
    dynaport.run_app(debug=True)
```

### Advanced Features

#### Port Preferences and Reservations

You can specify preferred ports or reserve specific ports:

```python
# Specify a preferred port (will use if available)
dynaport = DynaPortFlask(
    app_id="my-app",
    preferred_port=8080
)

# Reserve specific ports (prevent automatic allocation)
from dynaport.port_allocator import PortAllocator
allocator = PortAllocator()
allocator.reserve_port(8080)  # Reserve port 8080
```

#### Multiple Instances of the Same Application

Run multiple instances of the same application with different configurations:

```python
# First instance
dynaport1 = DynaPortFlask(
    app_id="my-app",
    instance_id="instance1",
    name="My App (Instance 1)"
)

# Second instance
dynaport2 = DynaPortFlask(
    app_id="my-app",
    instance_id="instance2",
    name="My App (Instance 2)"
)
```

#### Service Discovery

Use DynaPort for service discovery between your applications:

```python
from dynaport.service_registry import ServiceRegistry

# Create a service registry
registry = ServiceRegistry()

# Get a specific service
service = registry.get_service("user-service", "default")

# Access service information
if service and service.health_status == "healthy":
    # Make a request to the service
    import requests
    response = requests.get(f"{service.url}/api/users")
```

#### Service Dependencies

Specify dependencies between services:

```python
# Create DynaPort integration with dependencies
dynaport = DynaPortFlask(
    app_id="order-service",
    name="Order Service",
    dependencies=["user-service:default", "product-service:default"]
)
```

#### Health Checks

DynaPort automatically adds a basic health check endpoint, but you can customize it:

```python
@app.route('/custom-health')
def custom_health():
    # Perform custom health checks
    database_healthy = check_database_connection()
    cache_healthy = check_cache_connection()
    
    if database_healthy and cache_healthy:
        return jsonify({"status": "healthy"})
    else:
        return jsonify({
            "status": "unhealthy",
            "database": database_healthy,
            "cache": cache_healthy
        }), 503

# Specify custom health endpoint
dynaport = DynaPortFlask(
    app_id="my-app",
    health_endpoint="/custom-health"
)
```

### Using the Command-Line Interface

DynaPort provides a powerful command-line interface for managing ports and services:

#### Port Management

```bash
# Allocate a port for an application
dynaport port allocate my-app

# Get the port allocated to an application
dynaport port get my-app

# List all port allocations
dynaport port list

# Check if a port is available
dynaport port check 8080

# Find an available port
dynaport port find

# Release a port allocation
dynaport port release my-app
```

#### Service Management

```bash
# Register a service
dynaport service register my-app 8080 --name "My Application"

# List all registered services
dynaport service list

# Get information about a specific service
dynaport service get my-app

# Update the status of a service
dynaport service status my-app running

# Check the health of a service
dynaport service health my-app

# Unregister a service
dynaport service unregister my-app
```

#### Configuration Management

```bash
# Get a configuration value
dynaport config get port_allocator.port_range

# Set a configuration value
dynaport config set port_allocator.port_range "[5000, 6000]" --json

# List all configuration
dynaport config list
```

### Using the Web Dashboard

DynaPort includes a web dashboard for monitoring and managing services:

```bash
# Start the dashboard
python -m dynaport.web_dashboard

# Or use the provided script
python run_dashboard.py
```

The dashboard provides:
1. A list of all registered services with their status
2. Port allocation information
3. Configuration settings
4. Actions to manage services (stop, unregister)
5. Actions to manage ports (release)

## Real-World Use Cases

### Local Development of Microservices

When developing a microservices architecture locally, DynaPort simplifies the process:

```python
# User Service
dynaport = DynaPortFlask(
    app_id="user-service",
    name="User Service"
)

# Product Service
dynaport = DynaPortFlask(
    app_id="product-service",
    name="Product Service"
)

# Order Service (depends on User and Product services)
dynaport = DynaPortFlask(
    app_id="order-service",
    name="Order Service",
    dependencies=["user-service:default", "product-service:default"]
)
```

### Testing Multiple Configurations

Test different configurations of the same application:

```python
# Development instance
dynaport_dev = DynaPortFlask(
    app_id="my-app",
    instance_id="development",
    name="My App (Development)"
)

# Testing instance
dynaport_test = DynaPortFlask(
    app_id="my-app",
    instance_id="testing",
    name="My App (Testing)"
)

# Production-like instance
dynaport_prod = DynaPortFlask(
    app_id="my-app",
    instance_id="production",
    name="My App (Production)"
)
```

### Team Collaboration

Ensure consistent port assignments across team members:

```python
# Each team member uses the same app_id
dynaport = DynaPortFlask(
    app_id="team-project",
    name="Team Project"
)

# The port will be consistently assigned across different machines
```

## Best Practices

1. **Use unique app_id values** for different applications
2. **Use instance_id values** when running multiple instances of the same application
3. **Implement health checks** to enable proper service discovery
4. **Use the service registry** for service discovery instead of hardcoding URLs
5. **Specify dependencies** to document and enforce service relationships
6. **Use the web dashboard** for monitoring and troubleshooting
7. **Use the CLI** for scripting and automation

## Conclusion

DynaPort transforms the Flask development experience by eliminating port conflicts and providing powerful tools for service management. By automating port allocation, enabling service discovery, and offering comprehensive monitoring capabilities, DynaPort allows developers to focus on building great applications rather than managing infrastructure details.

Whether you're working on a single Flask application or a complex microservices architecture, DynaPort simplifies your development workflow and enhances collaboration within your team.

## Additional Resources

- [GitHub Repository](https://github.com/example/dynaport)
- [API Documentation](https://dynaport.readthedocs.io/)
- [Example Projects](https://github.com/example/dynaport/tree/main/examples)
