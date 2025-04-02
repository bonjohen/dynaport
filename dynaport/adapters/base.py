"""
Base adapter interface for DynaPort.

This module defines the base adapter interface that all framework-specific
adapters must implement to integrate with DynaPort.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union, TypeVar, Generic

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo
from dynaport.core.config_manager import ConfigManager


# Type variable for application objects
T = TypeVar('T')


class DynaPortAdapter(Generic[T], ABC):
    """
    Base adapter interface for DynaPort.
    
    This abstract class defines the interface that all framework-specific
    adapters must implement to integrate with DynaPort.
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
        health_endpoint: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        technology: Optional[str] = None
    ):
        """
        Initialize the DynaPort adapter.
        
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
            technology: Technology identifier (e.g., "flask", "django", "express")
        """
        import uuid
        
        self.app_id = app_id
        self.instance_id = instance_id or str(uuid.uuid4())
        self.name = name or app_id
        self.health_endpoint = health_endpoint
        self.dependencies = dependencies or []
        self.metadata = metadata or {}
        self.technology = technology
        
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
        
        # Application reference (set when wrap_app is called)
        self.app: Optional[T] = None
        
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
            metadata=self.metadata,
            technology=self.technology
        )
        
        self.service_registry.register_service(service)
    
    @abstractmethod
    def wrap_app(self, app: T) -> T:
        """
        Wrap an application with DynaPort functionality.
        
        Args:
            app: Application to wrap
            
        Returns:
            The same application with DynaPort functionality added
        """
        pass
    
    @abstractmethod
    def run_app(self, **kwargs) -> None:
        """
        Run the application with the allocated port.
        
        Args:
            **kwargs: Additional arguments to pass to the application's run method
        """
        pass
    
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
    
    @abstractmethod
    def add_health_endpoint(self) -> None:
        """Add a health check endpoint to the application."""
        pass
