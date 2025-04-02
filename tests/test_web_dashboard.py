"""
Unit tests for the web dashboard module.
"""

import json
from unittest import mock

import pytest
from flask import Flask, jsonify, request

from dynaport.web_dashboard import create_dashboard_app
from dynaport.port_allocator import PortAllocator
from dynaport.service_registry import ServiceRegistry, ServiceInfo
from dynaport.config_manager import ConfigManager


class TestWebDashboard:
    """Test cases for the web dashboard."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Mock dependencies
        self.mock_port_allocator = mock.MagicMock(spec=PortAllocator)
        self.mock_service_registry = mock.MagicMock(spec=ServiceRegistry)
        self.mock_config_manager = mock.MagicMock(spec=ConfigManager)

        # Configure mocks
        self.mock_port_allocator.get_all_assignments.return_value = {
            "app1:instance1": 8001,
            "app2:instance1": 8002
        }

        self.mock_port_allocator.is_port_available.side_effect = lambda p: p == 8001

        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001,
            status="running",
            health_status="healthy"
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002,
            status="stopped",
            health_status="unknown"
        )

        self.mock_service_registry.get_all_services.return_value = [service1, service2]

        self.mock_config_manager.config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }

        # Mock template and static directory creation
        self.mock_mkdir_patcher = mock.patch('pathlib.Path.mkdir')
        self.mock_mkdir = self.mock_mkdir_patcher.start()

        # Mock template creation
        self.mock_create_templates_patcher = mock.patch('dynaport.web_dashboard._create_templates')
        self.mock_create_templates = self.mock_create_templates_patcher.start()

        # Mock static file creation
        self.mock_create_static_files_patcher = mock.patch('dynaport.web_dashboard._create_static_files')
        self.mock_create_static_files = self.mock_create_static_files_patcher.start()

        # Mock DynaPortFlask
        self.mock_dynaport_flask_patcher = mock.patch('dynaport.web_dashboard.DynaPortFlask')
        self.mock_dynaport_flask_class = self.mock_dynaport_flask_patcher.start()
        self.mock_dynaport_flask = mock.MagicMock()

        # Create a Flask app with the API routes
        app = Flask(__name__)

        @app.route('/api/services')
        def api_services():
            return jsonify({
                "services": [service.to_dict() for service in self.mock_service_registry.get_all_services()]
            })

        @app.route('/api/ports')
        def api_ports():
            assignments = self.mock_port_allocator.get_all_assignments()
            return jsonify({
                "assignments": {
                    app_id: {
                        "port": port,
                        "available": self.mock_port_allocator.is_port_available(port)
                    }
                    for app_id, port in assignments.items()
                }
            })

        @app.route('/api/config')
        def api_config():
            return jsonify({
                "config": self.mock_config_manager.config
            })

        @app.route('/api/service/<app_id>/<instance_id>/status', methods=['POST'])
        def api_update_service_status(app_id, instance_id):
            data = request.json
            if data and 'status' in data:
                self.mock_service_registry.update_service_status(app_id, instance_id, data['status'])
                return jsonify({"success": True})
            return jsonify({"success": False, "error": "No status provided"}), 400

        @app.route('/api/port/release/<app_id>', methods=['POST'])
        def api_release_port(app_id):
            self.mock_port_allocator.release_port(app_id)
            return jsonify({"success": True})

        @app.route('/api/service/unregister/<app_id>/<instance_id>', methods=['POST'])
        def api_unregister_service(app_id, instance_id):
            self.mock_service_registry.unregister_service(app_id, instance_id)
            return jsonify({"success": True})

        self.mock_dynaport_flask.wrap_app.return_value = app
        self.mock_dynaport_flask_class.return_value = self.mock_dynaport_flask

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.mock_mkdir_patcher.stop()
        self.mock_create_templates_patcher.stop()
        self.mock_create_static_files_patcher.stop()
        self.mock_dynaport_flask_patcher.stop()

    def test_create_dashboard_app(self):
        """Test creating the dashboard app."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager,
            preferred_port=7000
        )

        # Verify DynaPortFlask was created correctly
        self.mock_dynaport_flask_class.assert_called_once_with(
            app_id="dynaport-dashboard",
            name="DynaPort Dashboard",
            preferred_port=7000,
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager,
            metadata={"description": "DynaPort monitoring dashboard"}
        )

        # Verify app was wrapped
        self.mock_dynaport_flask.wrap_app.assert_called_once()

        # Verify result
        assert isinstance(app, Flask)

    def test_api_services(self):
        """Test the API endpoint for services data."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.get('/api/services')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "services" in data
            assert len(data["services"]) == 2
            assert data["services"][0]["app_id"] == "app1"
            assert data["services"][1]["app_id"] == "app2"

    def test_api_ports(self):
        """Test the API endpoint for port allocation data."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.get('/api/ports')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "assignments" in data
            assert "app1:instance1" in data["assignments"]
            assert "app2:instance1" in data["assignments"]
            assert data["assignments"]["app1:instance1"]["port"] == 8001
            assert data["assignments"]["app1:instance1"]["available"] is True
            assert data["assignments"]["app2:instance1"]["port"] == 8002
            assert data["assignments"]["app2:instance1"]["available"] is False

    def test_api_config(self):
        """Test the API endpoint for configuration data."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.get('/api/config')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert "config" in data
            assert "port_allocator" in data["config"]
            assert "port_range" in data["config"]["port_allocator"]
            assert data["config"]["port_allocator"]["port_range"] == [8000, 9000]

    def test_api_update_service_status(self):
        """Test the API endpoint to update service status."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.post(
                '/api/service/app1/instance1/status',
                json={"status": "stopped"}
            )
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["success"] is True

            # Verify service status was updated
            self.mock_service_registry.update_service_status.assert_called_once_with(
                "app1",
                "instance1",
                "stopped"
            )

    def test_api_release_port(self):
        """Test the API endpoint to release a port."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.post('/api/port/release/app1:instance1')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["success"] is True

            # Verify port was released
            self.mock_port_allocator.release_port.assert_called_once_with(
                "app1:instance1"
            )

    def test_api_unregister_service(self):
        """Test the API endpoint to unregister a service."""
        # Create the dashboard app
        app = create_dashboard_app(
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )

        # Test the API endpoint
        with app.test_client() as client:
            response = client.post('/api/service/unregister/app1/instance1')
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["success"] is True

            # Verify service was unregistered
            self.mock_service_registry.unregister_service.assert_called_once_with(
                "app1",
                "instance1"
            )
