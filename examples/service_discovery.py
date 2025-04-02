"""
Service discovery example using DynaPort.

This example demonstrates how to use DynaPort's service discovery capabilities
to find and communicate with other services.
"""

import requests
from flask import Flask, jsonify, request
from dynaport.flask_integration import DynaPortFlask
from dynaport.service_registry import ServiceRegistry


# Create a Flask application
app = Flask(__name__)

# Create service registry
registry = ServiceRegistry()

@app.route('/')
def index():
    """Index route."""
    return jsonify({
        "message": "Service Discovery Example",
        "port": app.config.get('PORT', 'unknown'),
        "available_services": [
            {
                "id": service.service_id,
                "name": service.name,
                "url": service.url,
                "status": service.status,
                "health": service.health_status
            }
            for service in registry.get_all_services()
        ]
    })

@app.route('/api/services')
def list_services():
    """List all registered services."""
    return jsonify({
        "services": [service.to_dict() for service in registry.get_all_services()]
    })

@app.route('/api/services/<app_id>')
def get_services_by_app(app_id):
    """Get services for a specific application."""
    services = registry.get_services_by_app(app_id)
    return jsonify({
        "services": [service.to_dict() for service in services]
    })

@app.route('/api/proxy/<app_id>/<path:endpoint>')
def proxy_request(app_id, endpoint):
    """Proxy a request to another service."""
    # Get the first available instance of the app
    services = registry.get_services_by_app(app_id)
    
    if not services:
        return jsonify({"error": f"No services found for {app_id}"}), 404
    
    # Use the first healthy service
    service = next(
        (s for s in services if s.health_status == "healthy"),
        services[0]  # Fall back to first service if none are healthy
    )
    
    # Forward the request
    try:
        url = f"{service.url}/{endpoint}"
        response = requests.get(
            url,
            params=request.args,
            headers={k: v for k, v in request.headers if k != 'Host'},
            timeout=5
        )
        
        return jsonify({
            "service": service.name,
            "url": url,
            "status_code": response.status_code,
            "data": response.json() if response.headers.get('content-type') == 'application/json' else None
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="service-discovery",
        name="Service Discovery Example",
        preferred_port=7000,
        service_registry=registry,
        metadata={"description": "Service discovery example"}
    )
    
    # Wrap the Flask app with DynaPort
    dynaport.wrap_app(app)
    
    # Run the app
    print(f"Running on port {dynaport.port}")
    print(f"Visit http://localhost:{dynaport.port} to see available services")
    dynaport.run_app(debug=True)
