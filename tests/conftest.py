"""
Pytest configuration and fixtures.
"""

import os
import tempfile
from pathlib import Path

import pytest
from flask import Flask

from dynaport.port_allocator import PortAllocator
from dynaport.service_registry import ServiceRegistry
from dynaport.config_manager import ConfigManager
from dynaport.flask_integration import DynaPortFlask


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def port_allocator(temp_dir):
    """Create a PortAllocator instance for tests."""
    storage_path = temp_dir / "ports.json"
    return PortAllocator(storage_path=str(storage_path))


@pytest.fixture
def service_registry(temp_dir):
    """Create a ServiceRegistry instance for tests."""
    storage_path = temp_dir / "services.json"
    return ServiceRegistry(storage_path=str(storage_path))


@pytest.fixture
def config_manager(temp_dir):
    """Create a ConfigManager instance for tests."""
    config_dir = temp_dir / "config"
    return ConfigManager(config_dir=str(config_dir))


@pytest.fixture
def flask_app():
    """Create a Flask application for tests."""
    app = Flask(__name__)
    
    @app.route('/test')
    def test_route():
        return {'message': 'Test route'}
    
    return app


@pytest.fixture
def dynaport_flask(port_allocator, service_registry, config_manager):
    """Create a DynaPortFlask instance for tests."""
    return DynaPortFlask(
        app_id="test-app",
        instance_id="test-instance",
        name="Test App",
        port_allocator=port_allocator,
        service_registry=service_registry,
        config_manager=config_manager
    )
