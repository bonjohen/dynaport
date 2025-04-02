"""
Flask application factory example using DynaPort.

This example demonstrates how to use DynaPort with the Flask application factory pattern.
"""

from flask import Flask, jsonify, Blueprint
from dynaport.flask_integration import create_dynaport_app


def create_app(config=None):
    """Create and configure a Flask application."""
    app = Flask(__name__)
    
    # Apply configuration
    app.config.from_mapping(
        SECRET_KEY='dev',
    )
    
    if config:
        app.config.from_mapping(config)
    
    # Register blueprints
    from blueprints import api_bp
    app.register_blueprint(api_bp)
    
    @app.route('/')
    def index():
        """Index route."""
        return jsonify({
            "message": "Hello from DynaPort Factory App!",
            "port": app.config.get('PORT', 'unknown')
        })
    
    return app


# Create a blueprint for demonstration
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/data')
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
    # Create Flask app with DynaPort integration
    app = create_dynaport_app(
        app_id="factory-app",
        app_factory=create_app,
        name="Factory Pattern App",
        preferred_port=8081,
        metadata={"description": "An example using the Flask application factory pattern"}
    )
    
    # Access the DynaPort instance
    dynaport = app.dynaport
    
    # Run the app
    print(f"Running on port {dynaport.port}")
    dynaport.run_app(debug=True)
