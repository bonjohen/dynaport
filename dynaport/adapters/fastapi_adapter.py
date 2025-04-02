"""
FastAPI adapter for DynaPort.

This module provides functionality for integrating DynaPort with FastAPI applications,
including automatic port configuration and service registration.
"""

import os
import sys
from typing import Optional, Dict, Any, Callable, List, Union, TypeVar, cast

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo
from dynaport.core.config_manager import ConfigManager
from dynaport.adapters.base import DynaPortAdapter


# Type variable for FastAPI application
T = TypeVar('T')


class DynaPortFastAPI(DynaPortAdapter[T]):
    """
    FastAPI adapter for DynaPort.
    
    This class provides functionality for integrating DynaPort with FastAPI applications,
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
        Initialize the DynaPort FastAPI adapter.
        
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
            technology="fastapi"
        )
    
    def wrap_app(self, app: T) -> T:
        """
        Wrap a FastAPI application with DynaPort functionality.
        
        Args:
            app: FastAPI application to wrap
            
        Returns:
            The same FastAPI application with DynaPort functionality added
        """
        self.app = app
        
        # Add health endpoint
        self.add_health_endpoint()
        
        # Add DynaPort info endpoint
        self._add_dynaport_info(app)
        
        # Store DynaPort instance in app
        setattr(app, 'dynaport', self)
        
        # Update service status
        self.service_registry.update_service_status(
            app_id=self.app_id,
            instance_id=self.instance_id,
            status="running"
        )
        
        return app
    
    def add_health_endpoint(self) -> None:
        """
        Add a health check endpoint to the FastAPI application.
        
        This method adds a health check endpoint to the FastAPI application
        that returns a JSON response with the application's status.
        """
        if self.app is None:
            raise ValueError("No FastAPI application provided")
            
        try:
            # Import FastAPI modules
            from fastapi import FastAPI
            
            # Ensure app is a FastAPI instance
            if not isinstance(self.app, FastAPI):
                raise ValueError("Application is not a FastAPI instance")
                
            # Remove leading slash if present
            endpoint = self.health_endpoint
            if endpoint and endpoint.startswith('/'):
                endpoint = endpoint[1:]
            
            # Add health check endpoint
            @self.app.get(f"/{endpoint}")
            def health_check():
                """Health check endpoint."""
                return {
                    "status": "healthy",
                    "app_id": self.app_id,
                    "instance_id": self.instance_id,
                    "port": self.port
                }
        except ImportError:
            print("FastAPI is not installed. Please install FastAPI to use this adapter.")
    
    def _add_dynaport_info(self, app: T) -> None:
        """
        Add DynaPort info endpoint to the FastAPI application.
        
        Args:
            app: FastAPI application to add the endpoint to
        """
        try:
            # Import FastAPI modules
            from fastapi import FastAPI
            
            # Ensure app is a FastAPI instance
            if not isinstance(app, FastAPI):
                return
                
            # Add DynaPort info endpoint
            @app.get("/dynaport/info")
            def dynaport_info():
                """DynaPort information endpoint."""
                return {
                    "app_id": self.app_id,
                    "instance_id": self.instance_id,
                    "name": self.name,
                    "port": self.port,
                    "dependencies": self.dependencies,
                    "metadata": self.metadata,
                    "technology": self.technology
                }
        except ImportError:
            pass
    
    def run_app(self, **kwargs) -> None:
        """
        Run the FastAPI application with the allocated port.
        
        Args:
            **kwargs: Additional arguments to pass to uvicorn.run()
        """
        if self.app is None:
            raise ValueError("No FastAPI application provided")
        
        try:
            # Import uvicorn
            import uvicorn
            
            # Update kwargs with our port
            kwargs['host'] = kwargs.get('host', '0.0.0.0')
            kwargs['port'] = self.port
            
            # Run the app
            uvicorn.run(self.app, **kwargs)
        except ImportError:
            print("Uvicorn is not installed. Please install uvicorn to run FastAPI applications.")
            sys.exit(1)
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
    Create a FastAPI application with DynaPort integration.
    
    Args:
        app_id: Unique identifier for the application
        app_factory: Factory function that creates a FastAPI application
        instance_id: Unique identifier for this instance (auto-generated if None)
        name: Human-readable name for the application
        preferred_port: Preferred port for the application
        health_endpoint: Endpoint for health checks
        dependencies: List of service IDs this application depends on
        metadata: Additional metadata for the application
        **factory_kwargs: Additional arguments to pass to app_factory
        
    Returns:
        FastAPI application with DynaPort integration
    """
    # Create DynaPort integration
    dynaport = DynaPortFastAPI(
        app_id=app_id,
        instance_id=instance_id,
        name=name,
        preferred_port=preferred_port,
        health_endpoint=health_endpoint,
        dependencies=dependencies,
        metadata=metadata
    )
    
    # Create FastAPI application
    app = app_factory(**factory_kwargs)
    
    # Wrap application with DynaPort
    return dynaport.wrap_app(app)
