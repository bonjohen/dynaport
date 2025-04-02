"""
Flask adapter for DynaPort.

This module provides functionality for integrating DynaPort with Flask applications,
including automatic port configuration and service registration.
"""

import os
import sys
from typing import Optional, Dict, Any, Callable, List, Union, TypeVar, cast

from flask import Flask, Blueprint, request, jsonify, current_app

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo
from dynaport.core.config_manager import ConfigManager
from dynaport.adapters.base import DynaPortAdapter


# Type variable for Flask application factory functions
T = TypeVar('T', bound=Flask)


class DynaPortFlask(DynaPortAdapter[Flask]):
    """
    Flask adapter for DynaPort.
    
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
        Initialize the DynaPort Flask adapter.
        
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
        super().__init__(
            app_id=app_id,
            instance_id=instance_id,
            name=name,
            port_allocator=port_allocator,
            service_registry=service_registry,
            config_manager=config_manager,
            preferred_port=preferred_port,
            health_endpoint=health_endpoint,
            dependencies=dependencies,
            metadata=metadata,
            technology="flask"
        )
    
    def wrap_app(self, app: Flask) -> Flask:
        """
        Wrap a Flask application with DynaPort functionality.
        
        Args:
            app: Flask application to wrap
            
        Returns:
            The same Flask application with DynaPort functionality added
        """
        self.app = app
        
        # Add health endpoint
        self.add_health_endpoint()
        
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
    
    def add_health_endpoint(self) -> None:
        """
        Add a health check endpoint to the Flask application.
        
        This method adds a health check endpoint to the Flask application
        that returns a JSON response with the application's status.
        """
        if self.app is None:
            raise ValueError("No Flask application provided")
            
        # Remove leading slash if present
        endpoint = self.health_endpoint
        if endpoint and endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        @self.app.route(f"/{endpoint}")
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
                "metadata": self.metadata,
                "technology": self.technology
            })
        
        app.register_blueprint(bp)
    
    def run_app(self, **kwargs) -> None:
        """
        Run the Flask application with the allocated port.
        
        Args:
            **kwargs: Additional arguments to pass to app.run()
        """
        if self.app is None:
            raise ValueError("No Flask application provided")
        
        # Update kwargs with our port
        kwargs['port'] = self.port
        if 'host' not in kwargs:
            kwargs['host'] = '0.0.0.0'
        
        try:
            self.app.run(**kwargs)
        finally:
            # Update service status when app stops
            self.service_registry.update_service_status(
                app_id=self.app_id,
                instance_id=self.instance_id,
                status="stopped"
            )


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
    return cast(T, dynaport.wrap_app(app))
