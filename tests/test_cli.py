"""
Unit tests for the command-line interface module.
"""

import json
import tempfile
from pathlib import Path
from unittest import mock
from click.testing import CliRunner

import pytest

from dynaport.cli import main, port, service, config
from dynaport.port_allocator import PortAllocator
from dynaport.service_registry import ServiceRegistry, ServiceInfo
from dynaport.config_manager import ConfigManager


class TestPortCommands:
    """Test cases for the port commands."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.runner = CliRunner()

        # Create a temporary directory for port allocator data
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "ports.json"

        # Mock PortAllocator
        self.mock_port_allocator_patcher = mock.patch('dynaport.cli.PortAllocator')
        self.mock_port_allocator_class = self.mock_port_allocator_patcher.start()
        self.mock_port_allocator = mock.MagicMock(spec=PortAllocator)
        self.mock_port_allocator_class.return_value = self.mock_port_allocator

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.mock_port_allocator_patcher.stop()
        self.temp_dir.cleanup()

    def test_port_allocate(self):
        """Test the port allocate command."""
        # Configure mock
        self.mock_port_allocator.allocate_port.return_value = 8000

        # Run command
        result = self.runner.invoke(port, ['allocate', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        assert "Allocated port 8000 for test-app" in result.output
        assert "PORT=8000" in result.output

        # Verify mock calls
        self.mock_port_allocator.allocate_port.assert_called_once_with(
            "test-app:default",
            None
        )

    def test_port_allocate_with_instance(self):
        """Test the port allocate command with instance ID."""
        # Configure mock
        self.mock_port_allocator.allocate_port.return_value = 8000

        # Run command
        result = self.runner.invoke(port, ['allocate', 'test-app', '--instance', 'instance1'])

        # Verify result
        assert result.exit_code == 0
        assert "Allocated port 8000 for test-app (instance: instance1)" in result.output

        # Verify mock calls
        self.mock_port_allocator.allocate_port.assert_called_once_with(
            "test-app:instance1",
            None
        )

    def test_port_allocate_with_preferred(self):
        """Test the port allocate command with preferred port."""
        # Configure mock
        self.mock_port_allocator.allocate_port.return_value = 8080

        # Run command
        result = self.runner.invoke(port, ['allocate', 'test-app', '--preferred', '8080'])

        # Verify result
        assert result.exit_code == 0
        assert "Allocated port 8080 for test-app" in result.output

        # Verify mock calls
        self.mock_port_allocator.allocate_port.assert_called_once_with(
            "test-app:default",
            8080
        )

    def test_port_release(self):
        """Test the port release command."""
        # Run command
        result = self.runner.invoke(port, ['release', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        assert "Released port for test-app" in result.output

        # Verify mock calls
        self.mock_port_allocator.release_port.assert_called_once_with(
            "test-app:default"
        )

    def test_port_get_found(self):
        """Test the port get command when port is found."""
        # Configure mock
        self.mock_port_allocator.get_assigned_port.return_value = 8000

        # Run command
        result = self.runner.invoke(port, ['get', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        assert "Port 8000 is assigned to test-app" in result.output
        assert "PORT=8000" in result.output

        # Verify mock calls
        self.mock_port_allocator.get_assigned_port.assert_called_once_with(
            "test-app:default"
        )

    def test_port_get_not_found(self):
        """Test the port get command when port is not found."""
        # Configure mock
        self.mock_port_allocator.get_assigned_port.return_value = None

        # Run command
        result = self.runner.invoke(port, ['get', 'test-app'])

        # Verify result
        assert result.exit_code == 1
        assert "No port assigned to test-app" in result.output

        # Verify mock calls
        self.mock_port_allocator.get_assigned_port.assert_called_once_with(
            "test-app:default"
        )

    def test_port_list(self):
        """Test the port list command."""
        # Configure mock
        self.mock_port_allocator.get_all_assignments.return_value = {
            "app1:default": 8001,
            "app2:default": 8002
        }

        # Run command
        result = self.runner.invoke(port, ['list'])

        # Verify result
        assert result.exit_code == 0
        assert "app1:default: 8001" in result.output
        assert "app2:default: 8002" in result.output

        # Verify mock calls
        self.mock_port_allocator.get_all_assignments.assert_called_once()

    def test_port_list_json(self):
        """Test the port list command with JSON output."""
        # Configure mock
        self.mock_port_allocator.get_all_assignments.return_value = {
            "app1:default": 8001,
            "app2:default": 8002
        }

        # Run command
        result = self.runner.invoke(port, ['list', '--json'])

        # Verify result
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data == {
            "app1:default": 8001,
            "app2:default": 8002
        }

        # Verify mock calls
        self.mock_port_allocator.get_all_assignments.assert_called_once()

    def test_port_check_available(self):
        """Test the port check command when port is available."""
        # Configure mock
        self.mock_port_allocator.is_port_available.return_value = True

        # Run command
        result = self.runner.invoke(port, ['check', '8000'])

        # Verify result
        assert result.exit_code == 0
        assert "Port 8000 is available" in result.output

        # Verify mock calls
        self.mock_port_allocator.is_port_available.assert_called_once_with(8000)

    def test_port_check_not_available(self):
        """Test the port check command when port is not available."""
        # Configure mock
        self.mock_port_allocator.is_port_available.return_value = False

        # Run command
        result = self.runner.invoke(port, ['check', '8000'])

        # Verify result
        assert result.exit_code == 1
        assert "Port 8000 is not available" in result.output

        # Verify mock calls
        self.mock_port_allocator.is_port_available.assert_called_once_with(8000)

    def test_port_find(self):
        """Test the port find command."""
        # Configure mock
        self.mock_port_allocator.find_available_port.return_value = 8000

        # Run command
        result = self.runner.invoke(port, ['find'])

        # Verify result
        assert result.exit_code == 0
        assert "Found available port: 8000" in result.output
        assert "PORT=8000" in result.output

        # Verify mock calls
        self.mock_port_allocator.find_available_port.assert_called_once()

    def test_port_find_error(self):
        """Test the port find command when no ports are available."""
        # Configure mock
        self.mock_port_allocator.find_available_port.side_effect = RuntimeError(
            "No available ports found"
        )

        # Run command
        result = self.runner.invoke(port, ['find'])

        # Verify result
        assert result.exit_code == 1
        assert "Error: No available ports found" in result.output

        # Verify mock calls
        self.mock_port_allocator.find_available_port.assert_called_once()


class TestServiceCommands:
    """Test cases for the service commands."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.runner = CliRunner()

        # Mock ServiceRegistry
        self.mock_service_registry_patcher = mock.patch('dynaport.cli.ServiceRegistry')
        self.mock_service_registry_class = self.mock_service_registry_patcher.start()
        self.mock_service_registry = mock.MagicMock(spec=ServiceRegistry)
        self.mock_service_registry_class.return_value = self.mock_service_registry

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.mock_service_registry_patcher.stop()

    def test_service_register(self):
        """Test the service register command."""
        # Run command
        result = self.runner.invoke(service, [
            'register',
            'test-app',
            '8000',
            '--name', 'Test App',
            '--health-endpoint', '/health',
            '--dependency', 'dep1',
            '--dependency', 'dep2',
            '--metadata', '{"key": "value"}'
        ])

        # Verify result
        assert result.exit_code == 0
        assert "Registered service test-app (instance: default) on port 8000" in result.output

        # Verify mock calls
        self.mock_service_registry.register_service.assert_called_once()
        service_info = self.mock_service_registry.register_service.call_args[0][0]
        assert service_info.app_id == "test-app"
        assert service_info.instance_id == "default"
        assert service_info.name == "Test App"
        assert service_info.port == 8000
        assert service_info.health_endpoint == "/health"
        assert service_info.dependencies == ["dep1", "dep2"]
        assert service_info.metadata == {"key": "value"}
        assert service_info.status == "running"

    def test_service_unregister(self):
        """Test the service unregister command."""
        # Run command
        result = self.runner.invoke(service, ['unregister', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        assert "Unregistered service test-app (instance: default)" in result.output

        # Verify mock calls
        self.mock_service_registry.unregister_service.assert_called_once_with(
            "test-app",
            "default"
        )

    def test_service_list(self):
        """Test the service list command."""
        # Configure mock
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

        # Run command
        result = self.runner.invoke(service, ['list'])

        # Verify result
        assert result.exit_code == 0
        assert "app1 (instance: instance1)" in result.output
        assert "app2 (instance: instance1)" in result.output
        assert "Status: running" in result.output
        assert "Status: stopped" in result.output

        # Verify mock calls
        self.mock_service_registry.get_all_services.assert_called_once()

    def test_service_list_json(self):
        """Test the service list command with JSON output."""
        # Configure mock
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

        self.mock_service_registry.get_all_services.return_value = [service1, service2]

        # Run command
        result = self.runner.invoke(service, ['list', '--json'])

        # Verify result
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data) == 2
        assert data[0]["app_id"] == "app1"
        assert data[1]["app_id"] == "app2"

        # Verify mock calls
        self.mock_service_registry.get_all_services.assert_called_once()

    def test_service_list_by_app(self):
        """Test the service list command filtered by app."""
        # Configure mock
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

        self.mock_service_registry.get_services_by_app.return_value = [service1, service2]

        # Run command
        result = self.runner.invoke(service, ['list', '--app', 'app1'])

        # Verify result
        assert result.exit_code == 0
        assert "app1 (instance: instance1)" in result.output
        assert "app1 (instance: instance2)" in result.output

        # Verify mock calls
        self.mock_service_registry.get_services_by_app.assert_called_once_with("app1")

    def test_service_get_found(self):
        """Test the service get command when service is found."""
        # Configure mock
        service_info = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            status="running",
            health_status="healthy",
            dependencies=["dep1"],
            metadata={"key": "value"}
        )

        self.mock_service_registry.get_service.return_value = service_info

        # Run command
        result = self.runner.invoke(service, ['get', 'test-app', '--instance', 'instance1'])

        # Verify result
        assert result.exit_code == 0
        assert "Service: test-app (instance: instance1)" in result.output
        assert "Name: Test App" in result.output
        assert "Status: running" in result.output
        assert "Health: healthy" in result.output
        assert "Dependencies: dep1" in result.output
        assert "key: value" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "instance1"
        )

    def test_service_get_not_found(self):
        """Test the service get command when service is not found."""
        # Configure mock
        self.mock_service_registry.get_service.return_value = None

        # Run command
        result = self.runner.invoke(service, ['get', 'test-app'])

        # Verify result
        assert result.exit_code == 1
        assert "Service test-app (instance: default) not found" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "default"
        )

    def test_service_get_json(self):
        """Test the service get command with JSON output."""
        # Configure mock
        service_info = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000
        )

        self.mock_service_registry.get_service.return_value = service_info

        # Run command
        result = self.runner.invoke(service, ['get', 'test-app', '--instance', 'instance1', '--json'])

        # Verify result
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["app_id"] == "test-app"
        assert data["instance_id"] == "instance1"
        assert data["name"] == "Test App"
        assert data["port"] == 8000

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "instance1"
        )

    def test_service_status(self):
        """Test the service status command."""
        # Run command
        result = self.runner.invoke(service, ['status', 'test-app', 'running'])

        # Verify result
        assert result.exit_code == 0
        assert "Updated status of test-app (instance: default) to running" in result.output

        # Verify mock calls
        self.mock_service_registry.update_service_status.assert_called_once_with(
            "test-app",
            "default",
            "running"
        )

    def test_service_health_healthy(self):
        """Test the service health command when service is healthy."""
        # Configure mock
        service_info = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health",
            health_status="healthy"
        )

        self.mock_service_registry.get_service.return_value = service_info

        # Run command
        result = self.runner.invoke(service, ['health', 'test-app', '--instance', 'instance1'])

        # Verify result
        assert result.exit_code == 0
        assert "Health status: healthy" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "instance1"
        )
        self.mock_service_registry._check_service_health.assert_called_once_with(
            service_info
        )

    def test_service_health_unhealthy(self):
        """Test the service health command when service is unhealthy."""
        # Configure mock
        service_info = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint="/health",
            health_status="unhealthy"
        )

        self.mock_service_registry.get_service.return_value = service_info

        # Run command
        result = self.runner.invoke(service, ['health', 'test-app', '--instance', 'instance1'])

        # Verify result
        assert result.exit_code == 1
        assert "Health status: unhealthy" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "instance1"
        )
        self.mock_service_registry._check_service_health.assert_called_once_with(
            service_info
        )

    def test_service_health_not_found(self):
        """Test the service health command when service is not found."""
        # Configure mock
        self.mock_service_registry.get_service.return_value = None

        # Run command
        result = self.runner.invoke(service, ['health', 'test-app'])

        # Verify result
        assert result.exit_code == 1
        assert "Service test-app (instance: default) not found" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "default"
        )

    def test_service_health_no_endpoint(self):
        """Test the service health command when service has no health endpoint."""
        # Configure mock
        service_info = ServiceInfo(
            app_id="test-app",
            instance_id="instance1",
            name="Test App",
            port=8000,
            health_endpoint=None
        )

        self.mock_service_registry.get_service.return_value = service_info

        # Run command
        result = self.runner.invoke(service, ['health', 'test-app', '--instance', 'instance1'])

        # Verify result
        assert result.exit_code == 1
        assert "Service test-app has no health endpoint configured" in result.output

        # Verify mock calls
        self.mock_service_registry.get_service.assert_called_once_with(
            "test-app",
            "instance1"
        )


class TestConfigCommands:
    """Test cases for the config commands."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.runner = CliRunner()

        # Mock ConfigManager
        self.mock_config_manager_patcher = mock.patch('dynaport.cli.ConfigManager')
        self.mock_config_manager_class = self.mock_config_manager_patcher.start()
        self.mock_config_manager = mock.MagicMock(spec=ConfigManager)
        self.mock_config_manager_class.return_value = self.mock_config_manager

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.mock_config_manager_patcher.stop()

    def test_config_get_global(self):
        """Test the config get command for global config."""
        # Configure mock
        self.mock_config_manager.get_config_value.return_value = [8000, 9000]

        # Run command
        result = self.runner.invoke(config, ['get', 'port_allocator.port_range'])

        # Verify result
        assert result.exit_code == 0
        # YAML format will show lists with dashes
        assert "- 8000" in result.output
        assert "- 9000" in result.output

        # Verify mock calls
        self.mock_config_manager.get_config_value.assert_called_once_with(
            "port_allocator.port_range"
        )

    def test_config_get_app(self):
        """Test the config get command for app-specific config."""
        # Configure mock
        self.mock_config_manager.get_app_config.return_value = {
            "port_allocator": {
                "port_range": [5000, 6000]
            }
        }

        # Run command
        result = self.runner.invoke(config, ['get', 'port_allocator.port_range', '--app', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        # YAML format will show lists with dashes
        assert "- 5000" in result.output
        assert "- 6000" in result.output

        # Verify mock calls
        self.mock_config_manager.get_app_config.assert_called_once_with(
            "test-app",
            None
        )

    def test_config_get_not_found(self):
        """Test the config get command when key is not found."""
        # Configure mock
        self.mock_config_manager.get_config_value.return_value = None

        # Run command
        result = self.runner.invoke(config, ['get', 'nonexistent.key'])

        # Verify result
        assert result.exit_code == 1
        assert "Key 'nonexistent.key' not found in configuration" in result.output

        # Verify mock calls
        self.mock_config_manager.get_config_value.assert_called_once_with(
            "nonexistent.key"
        )

    def test_config_set_global(self):
        """Test the config set command for global config."""
        # Run command
        result = self.runner.invoke(config, ['set', 'port_allocator.port_range', '[5000, 6000]', '--json'])

        # Verify result
        assert result.exit_code == 0
        assert "Set port_allocator.port_range = [5000, 6000]" in result.output

        # Verify mock calls
        self.mock_config_manager.set_config_value.assert_called_once_with(
            "port_allocator.port_range",
            [5000, 6000]
        )

    def test_config_set_app(self):
        """Test the config set command for app-specific config."""
        # Configure mock
        self.mock_config_manager.get_app_config.return_value = {}

        # Run command
        result = self.runner.invoke(config, [
            'set',
            'port_allocator.port_range',
            '[5000, 6000]',
            '--app', 'test-app',
            '--json'
        ])

        # Verify result
        assert result.exit_code == 0
        assert "Set port_allocator.port_range = [5000, 6000]" in result.output

        # Verify mock calls
        self.mock_config_manager.get_app_config.assert_called_once_with(
            "test-app",
            None
        )
        self.mock_config_manager.save_app_config.assert_called_once()
        config_arg = self.mock_config_manager.save_app_config.call_args[1]["config"]
        assert config_arg["port_allocator"]["port_range"] == [5000, 6000]

    def test_config_list_global(self):
        """Test the config list command for global config."""
        # Configure mock
        self.mock_config_manager.config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            },
            "service_registry": {
                "discovery_port": 7000
            }
        }

        # Run command
        result = self.runner.invoke(config, ['list'])

        # Verify result
        assert result.exit_code == 0
        assert "port_allocator:" in result.output
        assert "port_range:" in result.output
        assert "service_registry:" in result.output

        # Verify mock calls
        # No need to verify calls since we're mocking the config property

    def test_config_list_app(self):
        """Test the config list command for app-specific config."""
        # Configure mock
        self.mock_config_manager.get_app_config.return_value = {
            "port_allocator": {
                "port_range": [5000, 6000]
            },
            "app_specific": {
                "setting": "value"
            }
        }

        # Run command
        result = self.runner.invoke(config, ['list', '--app', 'test-app'])

        # Verify result
        assert result.exit_code == 0
        assert "port_allocator:" in result.output
        assert "port_range:" in result.output
        assert "app_specific:" in result.output
        assert "setting: value" in result.output

        # Verify mock calls
        self.mock_config_manager.get_app_config.assert_called_once_with(
            "test-app",
            None
        )
