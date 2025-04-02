"""
Simple Flask application example using DynaPort.

This example demonstrates how to use DynaPort with a basic Flask application.
"""

from flask import Flask, jsonify
from dynaport.flask_integration import DynaPortFlask

# Create a basic Flask application
app = Flask(__name__)

@app.route('/')
def index():
    """Simple index route."""
    return jsonify({
        "message": "Hello from DynaPort!",
        "port": app.config.get('PORT', 'unknown')
    })

@app.route('/api/data')
def api_data():
    """Example API endpoint."""
    return jsonify({
        "data": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
    })

if __name__ == '__main__':
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="simple-app",
        name="Simple Example App",
        preferred_port=8080,  # Will try this port first
        metadata={"description": "A simple example Flask application"}
    )
    
    # Wrap the Flask app with DynaPort
    dynaport.wrap_app(app)
    
    # Run the app on the allocated port
    print(f"Running on port {dynaport.port}")
    dynaport.run_app(debug=True)
