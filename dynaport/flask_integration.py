"""
Flask integration module for DynaPort.

This module provides functionality for integrating DynaPort with Flask applications,
including automatic port configuration and service registration.
"""

import os
import sys
import uuid
import socket
import logging
from typing import Optional, Dict, Any, Callable, List, Union, TypeVar, cast

from flask import Flask, Blueprint, request, jsonify, current_app

from .port_allocator import PortAllocator
from .service_registry import ServiceRegistry, ServiceInfo
from .config_manager import ConfigManager


# Type variable for Flask application factory functions
T = TypeVar('T', bound=Flask)


class DynaPortFlask:
    """
    Flask integration for DynaPort.
    
    This class provides functionality for integrating DynaPort with Flask applications,
    including automatic port configuration and service registration.
    """
    
    def __init__(
        self,
        app_id: str,
        instance_id: Optional[str] = None,
        name: Optional[str] = None,
        port_allocator: Optional[PortAllocator] = None,
        service_registry: Optional[ServiceRegistry] = None,
        config_manager: Optional[ConfigManager] = None,
        preferred_port: Optional[int] = None,
        health_endpoint: str = "/health",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the DynaPort Flask integration.
        
        Args:
            app_id: Unique identifier for the application
            instance_id: Unique identifier for this instance (auto-generated if None)
            name: Human-readable name for the application
            port_allocator: Port allocator instance (created if None)
            service_registry: Service registry instance (created if None)
            config_manager: Configuration manager instance (created if None)
            preferred_port: Preferred port for the application
            health_endpoint: Endpoint for health checks
            dependencies: List of service IDs this application depends on
            metadata: Additional metadata for the application
        """
        self.app_id = app_id
        self.instance_id = instance_id or str(uuid.uuid4())
        self.name = name or app_id
        self.health_endpoint = health_endpoint
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        
        # Create or use provided components
        self.port_allocator = port_allocator or PortAllocator()
        self.service_registry = service_registry or ServiceRegistry()
        self.config_manager = config_manager or ConfigManager()
        
        # Get configuration for this app
        self.app_config = self.config_manager.get_app_config(
            app_id=self.app_id,
            instance_id=self.instance_id
        )
        
        # Allocate port
        self.port = self.port_allocator.allocate_port(
            app_id=f"{self.app_id}:{self.instance_id}",
            preferred_port=preferred_port
        )
        
        # Flask app reference (set when wrap_app is called)
        self.app: Optional[Flask] = None
        
        # Register service
        self._register_service()
    
    def _register_service(self) -> None:
        """Register this application with the service registry."""
        service = ServiceInfo(
            app_id=self.app_id,
            instance_id=self.instance_id,
            name=self.name,
            port=self.port,
            host="127.0.0.1",
            status="starting",
            health_endpoint=self.health_endpoint,
            dependencies=self.dependencies,
            metadata=self.metadata
        )
        
        self.service_registry.register_service(service)
    
    def wrap_app(self, app: T) -> T:
        """
        Wrap a Flask application with DynaPort functionality.
        
        Args:
            app: Flask application to wrap
            
        Returns:
            The same Flask application with DynaPort functionality added
        """
        self.app = app
        
        # Add health endpoint
        self._add_health_endpoint(app)
        
        # Add DynaPort blueprint
        self._add_dynaport_blueprint(app)
        
        # Store DynaPort instance in app
        app.dynaport = self  # type: ignore
        
        # Update service status
        self.service_registry.update_service_status(
            app_id=self.app_id,
            instance_id=self.instance_id,
            status="running"
        )
        
        # Set port in app config
        app.config['PORT'] = self.port
        
        return app
    
    def _add_health_endpoint(self, app: Flask) -> None:
        """
        Add a health check endpoint to the Flask application.
        
        Args:
            app: Flask application to add the endpoint to
        """
        # Remove leading slash if present
        endpoint = self.health_endpoint
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        @app.route(f"/{endpoint}")
        def health_check():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "app_id": self.app_id,
                "instance_id": self.instance_id,
                "port": self.port
            })
    
    def _add_dynaport_blueprint(self, app: Flask) -> None:
        """
        Add the DynaPort blueprint to the Flask application.
        
        Args:
            app: Flask application to add the blueprint to
        """
        bp = Blueprint('dynaport', __name__)
        
        @bp.route('/dynaport/info')
        def dynaport_info():
            """DynaPort information endpoint."""
            return jsonify({
                "app_id": self.app_id,
                "instance_id": self.instance_id,
                "name": self.name,
                "port": self.port,
                "dependencies": self.dependencies,
                "metadata": self.metadata
            })
        
        app.register_blueprint(bp)
    
    def run_app(self, app: Optional[Flask] = None, **kwargs) -> None:
        """
        Run the Flask application with the allocated port.
        
        Args:
            app: Flask application to run (uses self.app if None)
            **kwargs: Additional arguments to pass to app.run()
        """
        app = app or self.app
        if app is None:
            raise ValueError("No Flask application provided")
        
        # Update kwargs with our port
        kwargs['port'] = self.port
        if 'host' not in kwargs:
            kwargs['host'] = '0.0.0.0'
        
        try:
            app.run(**kwargs)
        finally:
            # Update service status when app stops
            self.service_registry.update_service_status(
                app_id=self.app_id,
                instance_id=self.instance_id,
                status="stopped"
            )
    
    def shutdown(self) -> None:
        """Shut down the application and clean up resources."""
        # Update service status
        self.service_registry.update_service_status(
            app_id=self.app_id,
            instance_id=self.instance_id,
            status="stopped"
        )
        
        # Release port
        self.port_allocator.release_port(f"{self.app_id}:{self.instance_id}")


def create_dynaport_app(
    app_id: str,
    app_factory: Callable[..., T],
    instance_id: Optional[str] = None,
    name: Optional[str] = None,
    preferred_port: Optional[int] = None,
    health_endpoint: str = "/health",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **factory_kwargs
) -> T:
    """
    Create a Flask application with DynaPort integration.
    
    Args:
        app_id: Unique identifier for the application
        app_factory: Factory function that creates a Flask application
        instance_id: Unique identifier for this instance (auto-generated if None)
        name: Human-readable name for the application
        preferred_port: Preferred port for the application
        health_endpoint: Endpoint for health checks
        dependencies: List of service IDs this application depends on
        metadata: Additional metadata for the application
        **factory_kwargs: Additional arguments to pass to app_factory
        
    Returns:
        Flask application with DynaPort integration
    """
    # Create DynaPort integration
    dynaport = DynaPortFlask(
        app_id=app_id,
        instance_id=instance_id,
        name=name,
        preferred_port=preferred_port,
        health_endpoint=health_endpoint,
        dependencies=dependencies,
        metadata=metadata
    )
    
    # Create Flask application
    app = app_factory(**factory_kwargs)
    
    # Wrap application with DynaPort
    return dynaport.wrap_app(app)
