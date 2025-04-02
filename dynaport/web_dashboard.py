"""
Web dashboard for DynaPort.

This module provides a web interface for monitoring and managing
DynaPort services and port allocations.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

from flask import Flask, render_template, jsonify, request, redirect, url_for

from .port_allocator import PortAllocator
from .service_registry import ServiceRegistry, ServiceInfo
from .config_manager import ConfigManager
from .flask_integration import DynaPortFlask


def create_dashboard_app(
    port_allocator: Optional[PortAllocator] = None,
    service_registry: Optional[ServiceRegistry] = None,
    config_manager: Optional[ConfigManager] = None,
    preferred_port: int = 7000
) -> Flask:
    """
    Create a Flask application for the DynaPort dashboard.
    
    Args:
        port_allocator: Port allocator instance (created if None)
        service_registry: Service registry instance (created if None)
        config_manager: Configuration manager instance (created if None)
        preferred_port: Preferred port for the dashboard
        
    Returns:
        Flask application for the dashboard
    """
    # Create components if not provided
    port_allocator = port_allocator or PortAllocator()
    service_registry = service_registry or ServiceRegistry()
    config_manager = config_manager or ConfigManager()
    
    # Create Flask application
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static")
    )
    
    # Create templates and static directories if they don't exist
    templates_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"
    templates_dir.mkdir(exist_ok=True)
    static_dir.mkdir(exist_ok=True)
    
    # Create basic templates
    _create_templates(templates_dir)
    _create_static_files(static_dir)
    
    # Set up routes
    @app.route('/')
    def index():
        """Dashboard home page."""
        return render_template('index.html')
    
    @app.route('/api/services')
    def api_services():
        """API endpoint for services data."""
        services = service_registry.get_all_services()
        return jsonify({
            "services": [service.to_dict() for service in services]
        })
    
    @app.route('/api/ports')
    def api_ports():
        """API endpoint for port allocation data."""
        assignments = port_allocator.get_all_assignments()
        return jsonify({
            "assignments": {
                app_id: {
                    "port": port,
                    "available": port_allocator.is_port_available(port)
                }
                for app_id, port in assignments.items()
            }
        })
    
    @app.route('/api/config')
    def api_config():
        """API endpoint for configuration data."""
        return jsonify({
            "config": config_manager.config
        })
    
    @app.route('/api/service/<app_id>/<instance_id>/status', methods=['POST'])
    def api_update_service_status(app_id, instance_id):
        """API endpoint to update service status."""
        status = request.json.get('status')
        if status:
            service_registry.update_service_status(app_id, instance_id, status)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "No status provided"}), 400
    
    @app.route('/api/port/release/<app_id>', methods=['POST'])
    def api_release_port(app_id):
        """API endpoint to release a port."""
        port_allocator.release_port(app_id)
        return jsonify({"success": True})
    
    @app.route('/api/service/unregister/<app_id>/<instance_id>', methods=['POST'])
    def api_unregister_service(app_id, instance_id):
        """API endpoint to unregister a service."""
        service_registry.unregister_service(app_id, instance_id)
        return jsonify({"success": True})
    
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id="dynaport-dashboard",
        name="DynaPort Dashboard",
        preferred_port=preferred_port,
        port_allocator=port_allocator,
        service_registry=service_registry,
        config_manager=config_manager,
        metadata={"description": "DynaPort monitoring dashboard"}
    )
    
    # Wrap the Flask app with DynaPort
    return dynaport.wrap_app(app)


def _create_templates(templates_dir: Path) -> None:
    """
    Create basic templates for the dashboard.
    
    Args:
        templates_dir: Directory to create templates in
    """
    # Create base template
    base_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DynaPort Dashboard{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
    <script src="{{ url_for('static', filename='js/dashboard.js') }}" defer></script>
</head>
<body>
    <header>
        <h1>DynaPort Dashboard</h1>
        <nav>
            <ul>
                <li><a href="#services">Services</a></li>
                <li><a href="#ports">Ports</a></li>
                <li><a href="#config">Configuration</a></li>
            </ul>
        </nav>
    </header>
    
    <main>
        {% block content %}{% endblock %}
    </main>
    
    <footer>
        <p>DynaPort - Dynamic Port Management System</p>
    </footer>
</body>
</html>
"""
    
    # Create index template
    index_html = """{% extends "base.html" %}

{% block content %}
<section id="services" class="dashboard-section">
    <h2>Services</h2>
    <div class="loading">Loading services...</div>
    <div class="services-container" style="display: none;">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Name</th>
                    <th>App ID</th>
                    <th>Instance</th>
                    <th>URL</th>
                    <th>Status</th>
                    <th>Health</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="services-table-body">
                <!-- Services will be populated here -->
            </tbody>
        </table>
    </div>
</section>

<section id="ports" class="dashboard-section">
    <h2>Port Allocations</h2>
    <div class="loading">Loading port allocations...</div>
    <div class="ports-container" style="display: none;">
        <table class="data-table">
            <thead>
                <tr>
                    <th>Application ID</th>
                    <th>Port</th>
                    <th>Status</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="ports-table-body">
                <!-- Port allocations will be populated here -->
            </tbody>
        </table>
    </div>
</section>

<section id="config" class="dashboard-section">
    <h2>Configuration</h2>
    <div class="loading">Loading configuration...</div>
    <div class="config-container" style="display: none;">
        <pre id="config-display"></pre>
    </div>
</section>
{% endblock %}
"""
    
    # Write templates to files
    with open(templates_dir / "base.html", "w") as f:
        f.write(base_html)
    
    with open(templates_dir / "index.html", "w") as f:
        f.write(index_html)


def _create_static_files(static_dir: Path) -> None:
    """
    Create static files for the dashboard.
    
    Args:
        static_dir: Directory to create static files in
    """
    # Create CSS directory
    css_dir = static_dir / "css"
    css_dir.mkdir(exist_ok=True)
    
    # Create JS directory
    js_dir = static_dir / "js"
    js_dir.mkdir(exist_ok=True)
    
    # Create CSS file
    css = """/* DynaPort Dashboard Styles */

:root {
    --primary-color: #3498db;
    --secondary-color: #2c3e50;
    --success-color: #2ecc71;
    --warning-color: #f39c12;
    --danger-color: #e74c3c;
    --light-color: #ecf0f1;
    --dark-color: #34495e;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: #333;
    margin: 0;
    padding: 0;
    background-color: #f5f5f5;
}

header {
    background-color: var(--primary-color);
    color: white;
    padding: 1rem;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

header h1 {
    margin: 0;
    font-size: 1.8rem;
}

nav ul {
    list-style: none;
    padding: 0;
    margin: 1rem 0 0 0;
    display: flex;
}

nav ul li {
    margin-right: 1rem;
}

nav ul li a {
    color: white;
    text-decoration: none;
    padding: 0.5rem;
    border-radius: 4px;
    transition: background-color 0.3s;
}

nav ul li a:hover {
    background-color: rgba(255, 255, 255, 0.2);
}

main {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

.dashboard-section {
    background-color: white;
    border-radius: 8px;
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    padding: 1.5rem;
    margin-bottom: 2rem;
}

.dashboard-section h2 {
    margin-top: 0;
    color: var(--secondary-color);
    border-bottom: 2px solid var(--light-color);
    padding-bottom: 0.5rem;
}

.loading {
    text-align: center;
    padding: 2rem;
    color: #777;
}

.data-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
}

.data-table th,
.data-table td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

.data-table th {
    background-color: var(--light-color);
    font-weight: 600;
}

.data-table tr:hover {
    background-color: #f9f9f9;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
}

.status-running {
    background-color: var(--success-color);
    color: white;
}

.status-starting {
    background-color: var(--warning-color);
    color: white;
}

.status-stopped {
    background-color: var(--light-color);
    color: var(--dark-color);
}

.status-error {
    background-color: var(--danger-color);
    color: white;
}

.status-unknown {
    background-color: #bbb;
    color: white;
}

.health-healthy {
    color: var(--success-color);
}

.health-unhealthy {
    color: var(--danger-color);
}

.health-unknown {
    color: #777;
}

.btn {
    display: inline-block;
    padding: 0.4rem 0.75rem;
    border: none;
    border-radius: 4px;
    background-color: var(--primary-color);
    color: white;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.3s;
    text-decoration: none;
    margin-right: 0.5rem;
}

.btn:hover {
    background-color: #2980b9;
}

.btn-danger {
    background-color: var(--danger-color);
}

.btn-danger:hover {
    background-color: #c0392b;
}

.btn-warning {
    background-color: var(--warning-color);
}

.btn-warning:hover {
    background-color: #d35400;
}

#config-display {
    background-color: var(--light-color);
    padding: 1rem;
    border-radius: 4px;
    overflow-x: auto;
    white-space: pre-wrap;
}

footer {
    text-align: center;
    padding: 1rem;
    background-color: var(--secondary-color);
    color: white;
    margin-top: 2rem;
}
"""
    
    # Create JavaScript file
    js = """// DynaPort Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Load initial data
    loadServices();
    loadPorts();
    loadConfig();
    
    // Set up refresh interval (every 5 seconds)
    setInterval(function() {
        loadServices();
        loadPorts();
    }, 5000);
});

// Load services data
function loadServices() {
    fetch('/api/services')
        .then(response => response.json())
        .then(data => {
            const servicesContainer = document.querySelector('.services-container');
            const loadingIndicator = document.querySelector('#services .loading');
            
            if (data.services.length === 0) {
                loadingIndicator.textContent = 'No services registered';
                return;
            }
            
            const tableBody = document.getElementById('services-table-body');
            tableBody.innerHTML = '';
            
            data.services.forEach(service => {
                const row = document.createElement('tr');
                
                // Create status badge
                const statusBadge = `<span class="status-badge status-${service.status}">${service.status}</span>`;
                
                // Create health status
                const healthStatus = `<span class="health-${service.health_status}">${service.health_status}</span>`;
                
                // Create action buttons
                const actions = `
                    <button class="btn" onclick="openService('${service.url}')">Open</button>
                    <button class="btn btn-warning" onclick="updateServiceStatus('${service.app_id}', '${service.instance_id}', 'stopped')">Stop</button>
                    <button class="btn btn-danger" onclick="unregisterService('${service.app_id}', '${service.instance_id}')">Unregister</button>
                `;
                
                row.innerHTML = `
                    <td>${service.name}</td>
                    <td>${service.app_id}</td>
                    <td>${service.instance_id}</td>
                    <td><a href="${service.url}" target="_blank">${service.url}</a></td>
                    <td>${statusBadge}</td>
                    <td>${healthStatus}</td>
                    <td>${actions}</td>
                `;
                
                tableBody.appendChild(row);
            });
            
            // Show the services container and hide loading indicator
            servicesContainer.style.display = 'block';
            loadingIndicator.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading services:', error);
        });
}

// Load port allocations data
function loadPorts() {
    fetch('/api/ports')
        .then(response => response.json())
        .then(data => {
            const portsContainer = document.querySelector('.ports-container');
            const loadingIndicator = document.querySelector('#ports .loading');
            
            const assignments = data.assignments;
            const appIds = Object.keys(assignments);
            
            if (appIds.length === 0) {
                loadingIndicator.textContent = 'No port allocations';
                return;
            }
            
            const tableBody = document.getElementById('ports-table-body');
            tableBody.innerHTML = '';
            
            appIds.forEach(appId => {
                const assignment = assignments[appId];
                const row = document.createElement('tr');
                
                // Create status badge
                const statusBadge = assignment.available
                    ? '<span class="status-badge status-stopped">Available</span>'
                    : '<span class="status-badge status-running">In Use</span>';
                
                // Create action buttons
                const actions = `
                    <button class="btn btn-danger" onclick="releasePort('${appId}')">Release</button>
                `;
                
                row.innerHTML = `
                    <td>${appId}</td>
                    <td>${assignment.port}</td>
                    <td>${statusBadge}</td>
                    <td>${actions}</td>
                `;
                
                tableBody.appendChild(row);
            });
            
            // Show the ports container and hide loading indicator
            portsContainer.style.display = 'block';
            loadingIndicator.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading port allocations:', error);
        });
}

// Load configuration data
function loadConfig() {
    fetch('/api/config')
        .then(response => response.json())
        .then(data => {
            const configContainer = document.querySelector('.config-container');
            const loadingIndicator = document.querySelector('#config .loading');
            
            const configDisplay = document.getElementById('config-display');
            configDisplay.textContent = JSON.stringify(data.config, null, 2);
            
            // Show the config container and hide loading indicator
            configContainer.style.display = 'block';
            loadingIndicator.style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading configuration:', error);
        });
}

// Open a service in a new tab
function openService(url) {
    window.open(url, '_blank');
}

// Update service status
function updateServiceStatus(appId, instanceId, status) {
    fetch(`/api/service/${appId}/${instanceId}/status`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadServices();
        } else {
            alert('Failed to update service status: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error updating service status:', error);
        alert('Error updating service status');
    });
}

// Unregister a service
function unregisterService(appId, instanceId) {
    if (!confirm(`Are you sure you want to unregister ${appId} (instance: ${instanceId})?`)) {
        return;
    }
    
    fetch(`/api/service/unregister/${appId}/${instanceId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadServices();
        } else {
            alert('Failed to unregister service: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error unregistering service:', error);
        alert('Error unregistering service');
    });
}

// Release a port allocation
function releasePort(appId) {
    if (!confirm(`Are you sure you want to release the port for ${appId}?`)) {
        return;
    }
    
    fetch(`/api/port/release/${appId}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            loadPorts();
        } else {
            alert('Failed to release port: ' + (data.error || 'Unknown error'));
        }
    })
    .catch(error => {
        console.error('Error releasing port:', error);
        alert('Error releasing port');
    });
}
"""
    
    # Write static files
    with open(css_dir / "style.css", "w") as f:
        f.write(css)
    
    with open(js_dir / "dashboard.js", "w") as f:
        f.write(js)


def run_dashboard(port: int = 7000) -> None:
    """
    Run the DynaPort dashboard.
    
    Args:
        port: Port to run the dashboard on
    """
    app = create_dashboard_app(preferred_port=port)
    app.run(host='0.0.0.0', port=port, debug=True)
