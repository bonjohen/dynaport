"""
Multi-instance Flask application example using DynaPort.

This example demonstrates how to run multiple instances of the same Flask application
with different configurations using DynaPort.
"""

import sys
import uuid
from flask import Flask, jsonify, request
from dynaport.flask_integration import DynaPortFlask


def create_app(instance_name, instance_id=None):
    """Create a Flask application instance."""
    app = Flask(__name__)
    
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="multi-app",
        instance_id=instance_id or str(uuid.uuid4()),
        name=f"Multi-Instance App ({instance_name})",
        metadata={"instance_name": instance_name}
    )
    
    # Wrap the Flask app with DynaPort
    dynaport.wrap_app(app)
    
    @app.route('/')
    def index():
        """Index route."""
        return jsonify({
            "message": f"Hello from {instance_name} instance!",
            "instance_id": dynaport.instance_id,
            "port": app.config.get('PORT', 'unknown')
        })
    
    @app.route('/api/data')
    def api_data():
        """Example API endpoint."""
        return jsonify({
            "instance": instance_name,
            "instance_id": dynaport.instance_id,
            "data": [
                {"id": 1, "name": f"Item 1 from {instance_name}"},
                {"id": 2, "name": f"Item 2 from {instance_name}"},
                {"id": 3, "name": f"Item 3 from {instance_name}"}
            ]
        })
    
    return app, dynaport


if __name__ == '__main__':
    # Get instance name from command line
    if len(sys.argv) > 1:
        instance_name = sys.argv[1]
    else:
        instance_name = "default"
    
    # Create app instance
    app, dynaport = create_app(instance_name)
    
    # Run the app
    print(f"Running {instance_name} instance on port {dynaport.port}")
    dynaport.run_app(debug=True)
