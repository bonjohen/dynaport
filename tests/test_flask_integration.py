"""
Unit tests for the Flask integration module.
"""

import json
from unittest import mock

import pytest
from flask import Flask, jsonify

from dynaport.flask_integration import DynaPortFlask, create_dynaport_app
from dynaport.port_allocator import PortAllocator
from dynaport.service_registry import ServiceRegistry
from dynaport.config_manager import ConfigManager


class TestDynaPortFlask:
    """Test cases for the DynaPortFlask class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Mock dependencies
        self.mock_port_allocator = mock.MagicMock(spec=PortAllocator)
        self.mock_service_registry = mock.MagicMock(spec=ServiceRegistry)
        self.mock_config_manager = mock.MagicMock(spec=ConfigManager)
        
        # Configure mocks
        self.mock_port_allocator.allocate_port.return_value = 8000
        self.mock_config_manager.get_app_config.return_value = {}
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        with mock.patch('uuid.uuid4', return_value="test-uuid"):
            dynaport = DynaPortFlask(
                app_id="test-app",
                port_allocator=self.mock_port_allocator,
                service_registry=self.mock_service_registry,
                config_manager=self.mock_config_manager
            )
            
            assert dynaport.app_id == "test-app"
            assert dynaport.instance_id == "test-uuid"
            assert dynaport.name == "test-app"
            assert dynaport.health_endpoint == "/health"
            assert dynaport.dependencies == []
            assert dynaport.metadata == {}
            assert dynaport.port == 8000
            assert dynaport.app is None
            
            # Verify port allocation
            self.mock_port_allocator.allocate_port.assert_called_once_with(
                app_id="test-app:test-uuid",
                preferred_port=None
            )
            
            # Verify service registration
            self.mock_service_registry.register_service.assert_called_once()
            service = self.mock_service_registry.register_service.call_args[0][0]
            assert service.app_id == "test-app"
            assert service.instance_id == "test-uuid"
            assert service.port == 8000
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        dynaport = DynaPortFlask(
            app_id="test-app",
            instance_id="custom-instance",
            name="Custom App",
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager,
            preferred_port=8080,
            health_endpoint="/custom-health",
            dependencies=["dep1", "dep2"],
            metadata={"key": "value"}
        )
        
        assert dynaport.app_id == "test-app"
        assert dynaport.instance_id == "custom-instance"
        assert dynaport.name == "Custom App"
        assert dynaport.health_endpoint == "/custom-health"
        assert dynaport.dependencies == ["dep1", "dep2"]
        assert dynaport.metadata == {"key": "value"}
        assert dynaport.port == 8000
        
        # Verify port allocation
        self.mock_port_allocator.allocate_port.assert_called_once_with(
            app_id="test-app:custom-instance",
            preferred_port=8080
        )
        
        # Verify service registration
        self.mock_service_registry.register_service.assert_called_once()
        service = self.mock_service_registry.register_service.call_args[0][0]
        assert service.app_id == "test-app"
        assert service.instance_id == "custom-instance"
        assert service.name == "Custom App"
        assert service.port == 8000
        assert service.health_endpoint == "/custom-health"
        assert service.dependencies == ["dep1", "dep2"]
        assert service.metadata == {"key": "value"}
    
    def test_wrap_app(self):
        """Test wrapping a Flask application."""
        # Create a Flask app
        app = Flask(__name__)
        
        # Create DynaPort integration
        dynaport = DynaPortFlask(
            app_id="test-app",
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )
        
        # Wrap the app
        result = dynaport.wrap_app(app)
        
        # Verify the result
        assert result is app
        assert dynaport.app is app
        assert hasattr(app, 'dynaport')
        assert app.dynaport is dynaport
        assert app.config['PORT'] == 8000
        
        # Verify service status update
        self.mock_service_registry.update_service_status.assert_called_once_with(
            app_id="test-app",
            instance_id=dynaport.instance_id,
            status="running"
        )
        
        # Verify health endpoint was added
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["app_id"] == "test-app"
            assert data["port"] == 8000
        
        # Verify DynaPort blueprint was added
        with app.test_client() as client:
            response = client.get('/dynaport/info')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["app_id"] == "test-app"
            assert data["port"] == 8000
    
    def test_run_app(self):
        """Test running a Flask application."""
        # Create a Flask app
        app = Flask(__name__)
        
        # Mock app.run
        app.run = mock.MagicMock()
        
        # Create DynaPort integration
        dynaport = DynaPortFlask(
            app_id="test-app",
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )
        
        # Wrap the app
        dynaport.wrap_app(app)
        
        # Run the app
        dynaport.run_app(debug=True)
        
        # Verify app.run was called correctly
        app.run.assert_called_once_with(port=8000, host='0.0.0.0', debug=True)
    
    def test_run_app_exception(self):
        """Test running a Flask application with an exception."""
        # Create a Flask app
        app = Flask(__name__)
        
        # Mock app.run to raise an exception
        app.run = mock.MagicMock(side_effect=Exception("Test exception"))
        
        # Create DynaPort integration
        dynaport = DynaPortFlask(
            app_id="test-app",
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )
        
        # Wrap the app
        dynaport.wrap_app(app)
        
        # Run the app
        with pytest.raises(Exception):
            dynaport.run_app(debug=True)
        
        # Verify service status update
        self.mock_service_registry.update_service_status.assert_called_with(
            app_id="test-app",
            instance_id=dynaport.instance_id,
            status="stopped"
        )
    
    def test_shutdown(self):
        """Test shutting down the application."""
        # Create DynaPort integration
        dynaport = DynaPortFlask(
            app_id="test-app",
            instance_id="test-instance",
            port_allocator=self.mock_port_allocator,
            service_registry=self.mock_service_registry,
            config_manager=self.mock_config_manager
        )
        
        # Shutdown the app
        dynaport.shutdown()
        
        # Verify service status update
        self.mock_service_registry.update_service_status.assert_called_with(
            app_id="test-app",
            instance_id="test-instance",
            status="stopped"
        )
        
        # Verify port release
        self.mock_port_allocator.release_port.assert_called_once_with(
            "test-app:test-instance"
        )


class TestCreateDynaportApp:
    """Test cases for the create_dynaport_app function."""
    
    def test_create_dynaport_app(self):
        """Test creating a Flask application with DynaPort integration."""
        # Mock DynaPortFlask
        mock_dynaport = mock.MagicMock()
        mock_dynaport.wrap_app.return_value = "wrapped-app"
        
        # Mock DynaPortFlask constructor
        with mock.patch('dynaport.flask_integration.DynaPortFlask', return_value=mock_dynaport):
            # Create a factory function
            def app_factory(config=None):
                app = Flask(__name__)
                if config:
                    app.config.update(config)
                return app
            
            # Create the app
            result = create_dynaport_app(
                app_id="test-app",
                app_factory=app_factory,
                instance_id="test-instance",
                name="Test App",
                preferred_port=8080,
                health_endpoint="/custom-health",
                dependencies=["dep1"],
                metadata={"key": "value"},
                config={"TEST_CONFIG": True}
            )
            
            # Verify DynaPortFlask was created correctly
            from dynaport.flask_integration import DynaPortFlask
            DynaPortFlask.assert_called_once_with(
                app_id="test-app",
                instance_id="test-instance",
                name="Test App",
                preferred_port=8080,
                health_endpoint="/custom-health",
                dependencies=["dep1"],
                metadata={"key": "value"}
            )
            
            # Verify app_factory was called correctly
            mock_dynaport.wrap_app.assert_called_once()
            app = mock_dynaport.wrap_app.call_args[0][0]
            assert isinstance(app, Flask)
            assert app.config["TEST_CONFIG"] is True
            
            # Verify result
            assert result == "wrapped-app"
