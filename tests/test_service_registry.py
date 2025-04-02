"""
Unit tests for the service registry module.
"""

import json
import time
import tempfile
from pathlib import Path
from unittest import mock

import pytest
import requests

from dynaport.service_registry import ServiceRegistry, ServiceInfo


class TestServiceInfo:
    """Test cases for the ServiceInfo class."""

    def test_init_default_values(self):
        """Test initialization with default values."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000
        )

        assert service.app_id == "test-app"
        assert service.instance_id == "instance1"
        assert service.name == "Test App"
        assert service.port == 8000
        assert service.host == "127.0.0.1"
        assert service.status == "unknown"
        assert service.health_endpoint is None
        assert service.last_health_check is None
        assert service.health_status == "unknown"
        assert service.dependencies == []
        assert service.metadata == {}

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            host="localhost",
            status="running",
            health_endpoint="/health",
            last_health_check=123456789.0,
            health_status="healthy",
            dependencies=["dep1", "dep2"],
            metadata={"key": "value"}
        )

        assert service.app_id == "test-app"
        assert service.instance_id == "instance1"
        assert service.name == "Test App"
        assert service.port == 8000
        assert service.host == "localhost"
        assert service.status == "running"
        assert service.health_endpoint == "/health"
        assert service.last_health_check == 123456789.0
        assert service.health_status == "healthy"
        assert service.dependencies == ["dep1", "dep2"]
        assert service.metadata == {"key": "value"}

    def test_to_dict(self):
        """Test conversion to dictionary."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health",
            dependencies=["dep1"],
            metadata={"key": "value"}
        )

        service_dict = service.to_dict()

        assert service_dict["app_id"] == "test-app"
        assert service_dict["instance_id"] == "instance1"
        assert service_dict["name"] == "Test App"
        assert service_dict["port"] == 8000
        assert service_dict["health_endpoint"] == "/health"
        assert service_dict["dependencies"] == ["dep1"]
        assert service_dict["metadata"] == {"key": "value"}

    def test_from_dict(self):
        """Test creation from dictionary."""
        service_dict = {
            "app_id": "test-app",
            "instance_id": "instance1",
            "name": "Test App",
            "port": 8000,
            "host": "localhost",
            "status": "running",
            "health_endpoint": "/health",
            "last_health_check": 123456789.0,
            "health_status": "healthy",
            "dependencies": ["dep1", "dep2"],
            "metadata": {"key": "value"}
        }

        service = ServiceInfo.from_dict(service_dict)

        assert service.app_id == "test-app"
        assert service.instance_id == "instance1"
        assert service.name == "Test App"
        assert service.port == 8000
        assert service.host == "localhost"
        assert service.status == "running"
        assert service.health_endpoint == "/health"
        assert service.last_health_check == 123456789.0
        assert service.health_status == "healthy"
        assert service.dependencies == ["dep1", "dep2"]
        assert service.metadata == {"key": "value"}

    def test_service_id(self):
        """Test service ID property."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000
        )

        assert service.service_id == "test-app:instance1"

    def test_url(self):
        """Test URL property."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            host="localhost"
        )

        assert service.url == "http://localhost:8000"


class TestServiceRegistry:
    """Test cases for the ServiceRegistry class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a temporary directory for service registry data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "services.json"

        # Mock the health check thread
        self.mock_thread_patcher = mock.patch('threading.Thread')
        self.mock_thread = self.mock_thread_patcher.start()

        # Create registry with mocked thread
        self.registry = ServiceRegistry(
            storage_path=str(self.storage_path),
            health_check_interval=60
        )

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.mock_thread_patcher.stop()
        self.temp_dir.cleanup()

    def test_init_default_values(self):
        """Test initialization with default values."""
        with mock.patch('threading.Thread'):
            with mock.patch.object(ServiceRegistry, '_load_services'):
                registry = ServiceRegistry(storage_path=str(self.storage_path))
                assert isinstance(registry.services, dict)
                assert registry.health_check_interval == 60

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with mock.patch('threading.Thread'):
            registry = ServiceRegistry(
                storage_path=str(self.storage_path),
                health_check_interval=30
            )
            assert registry.storage_path == self.storage_path
            assert registry.health_check_interval == 30

    def test_load_services(self):
        """Test loading services from storage."""
        # Create a services file
        services_data = [
            {
                "app_id": "app1",
                "instance_id": "instance1",
                "name": "App 1",
                "port": 8001,
                "host": "127.0.0.1",
                "status": "running"
            },
            {
                "app_id": "app2",
                "instance_id": "instance1",
                "name": "App 2",
                "port": 8002,
                "host": "127.0.0.1",
                "status": "stopped"
            }
        ]

        with open(self.storage_path, 'w') as f:
            json.dump(services_data, f)

        # Load the services
        self.registry._load_services()

        assert len(self.registry.services) == 2
        assert "app1:instance1" in self.registry.services
        assert "app2:instance1" in self.registry.services
        assert self.registry.services["app1:instance1"].name == "App 1"
        assert self.registry.services["app2:instance1"].name == "App 2"

    def test_save_services(self):
        """Test saving services to storage."""
        # Add some services
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2
        }

        # Save the services
        self.registry._save_services()

        # Check that the file was created with the correct content
        with open(self.storage_path, 'r') as f:
            saved_services = json.load(f)

        assert len(saved_services) == 2
        assert saved_services[0]["app_id"] == "app1"
        assert saved_services[1]["app_id"] == "app2"

    def test_register_service(self):
        """Test registering a service."""
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000
        )

        self.registry.register_service(service)

        assert "test-app:instance1" in self.registry.services
        assert self.registry.services["test-app:instance1"] is service

        # Check that the service was saved
        assert self.storage_path.exists()

    def test_unregister_service(self):
        """Test unregistering a service."""
        # Register a service
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000
        )

        self.registry.services = {service.service_id: service}

        # Unregister the service
        self.registry.unregister_service("test-app", "instance1")

        assert "test-app:instance1" not in self.registry.services

        # Check that the services were saved
        assert self.storage_path.exists()

    def test_get_service(self):
        """Test getting a specific service."""
        # Register some services
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2
        }

        # Get a service
        result = self.registry.get_service("app1", "instance1")

        assert result is service1

        # Get a nonexistent service
        result = self.registry.get_service("nonexistent", "instance1")

        assert result is None

    def test_get_all_services(self):
        """Test getting all services."""
        # Register some services
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2
        }

        # Get all services
        result = self.registry.get_all_services()

        assert len(result) == 2
        assert service1 in result
        assert service2 in result

    def test_get_services_by_app(self):
        """Test getting services for a specific application."""
        # Register some services
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1 Instance 1",
            port=8001
        )

        service2 = ServiceInfo(
            app_id="app1",
            instance_id="instance2",
            name="App 1 Instance 2",
            port=8002
        )

        service3 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8003
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2,
            service3.service_id: service3
        }

        # Get services for app1
        result = self.registry.get_services_by_app("app1")

        assert len(result) == 2
        assert service1 in result
        assert service2 in result
        assert service3 not in result

        # Get services for app2
        result = self.registry.get_services_by_app("app2")

        assert len(result) == 1
        assert service3 in result

        # Get services for nonexistent app
        result = self.registry.get_services_by_app("nonexistent")

        assert len(result) == 0

    def test_update_service_status(self):
        """Test updating service status."""
        # Register a service
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            status="unknown"
        )

        self.registry.services = {service.service_id: service}

        # Update the status
        self.registry.update_service_status("test-app", "instance1", "running")

        assert self.registry.services["test-app:instance1"].status == "running"

        # Check that the services were saved
        assert self.storage_path.exists()

    @mock.patch('requests.get')
    def test_check_service_health_healthy(self, mock_get):
        """Test checking service health (healthy case)."""
        # Mock the response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Create a service with a health endpoint
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health"
        )

        # Check the health
        self.registry._check_service_health(service)

        assert service.health_status == "healthy"
        assert service.last_health_check is not None

        # Verify the request was made correctly
        mock_get.assert_called_once_with("http://127.0.0.1:8000/health", timeout=5)

    @mock.patch('requests.get')
    def test_check_service_health_unhealthy(self, mock_get):
        """Test checking service health (unhealthy case)."""
        # Mock the response
        mock_response = mock.MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        # Create a service with a health endpoint
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health"
        )

        # Check the health
        self.registry._check_service_health(service)

        assert service.health_status == "unhealthy"
        assert service.last_health_check is not None

    @mock.patch('requests.get')
    def test_check_service_health_exception(self, mock_get):
        """Test checking service health (exception case)."""
        # Mock the response to raise an exception
        mock_get.side_effect = requests.RequestException("Connection error")

        # Create a service with a health endpoint
        service = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health"
        )

        # Check the health
        self.registry._check_service_health(service)

        assert service.health_status == "unhealthy"
        assert service.last_health_check is not None

    def test_get_dependency_order_no_dependencies(self):
        """Test getting dependency order with no dependencies."""
        # Register some services with no dependencies
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2
        }

        # Get dependency order
        result = self.registry.get_dependency_order()

        assert len(result) == 1
        assert len(result[0]) == 2
        assert "app1:instance1" in result[0]
        assert "app2:instance1" in result[0]

    def test_get_dependency_order_with_dependencies(self):
        """Test getting dependency order with dependencies."""
        # Register some services with dependencies
        service1 = ServiceInfo(
            app_id="app1",
            instance_id="instance1",
            name="App 1",
            port=8001,
            dependencies=[]
        )

        service2 = ServiceInfo(
            app_id="app2",
            instance_id="instance1",
            name="App 2",
            port=8002,
            dependencies=["app1:instance1"]
        )

        service3 = ServiceInfo(
            app_id="app3",
            instance_id="instance1",
            name="App 3",
            port=8003,
            dependencies=["app2:instance1"]
        )

        service4 = ServiceInfo(
            app_id="app4",
            instance_id="instance1",
            name="App 4",
            port=8004,
            dependencies=["app1:instance1"]
        )

        self.registry.services = {
            service1.service_id: service1,
            service2.service_id: service2,
            service3.service_id: service3,
            service4.service_id: service4
        }

        # Get dependency order
        result = self.registry.get_dependency_order()

        assert len(result) == 3
        assert "app1:instance1" in result[0]
        assert "app2:instance1" in result[1]
        assert "app4:instance1" in result[1]
        assert "app3:instance1" in result[2]

    def test_close(self):
        """Test closing the registry."""
        # Mock the health check thread
        self.registry.health_check_thread = mock.MagicMock()
        self.registry.health_check_thread.is_alive.return_value = True

        # Close the registry
        self.registry.close()

        # Verify the thread was stopped
        assert self.registry.stop_health_check.is_set()
        self.registry.health_check_thread.join.assert_called_once_with(timeout=1)
