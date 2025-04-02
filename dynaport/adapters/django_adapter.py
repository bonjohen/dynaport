"""
Django adapter for DynaPort.

This module provides functionality for integrating DynaPort with Django applications,
including automatic port configuration and service registration.
"""

import os
import sys
from typing import Optional, Dict, Any, Callable, List, Union, TypeVar, cast, Tuple

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo
from dynaport.core.config_manager import ConfigManager
from dynaport.adapters.base import DynaPortAdapter


class DynaPortDjango(DynaPortAdapter[Dict[str, Any]]):
    """
    Django adapter for DynaPort.
    
    This class provides functionality for integrating DynaPort with Django applications,
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
        health_endpoint: str = "/health/",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the DynaPort Django adapter.
        
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
            technology="django"
        )
        
        # Django-specific attributes
        self.settings_module = None
        self.urls_module = None
    
    def wrap_app(self, settings_module: Dict[str, Any]) -> Dict[str, Any]:
        """
        Configure Django settings with DynaPort functionality.
        
        Args:
            settings_module: Django settings module to configure
            
        Returns:
            The same settings module with DynaPort configuration added
        """
        self.app = settings_module
        
        # Set port in settings
        settings_module['PORT'] = self.port
        
        # Update ALLOWED_HOSTS to include localhost with port
        allowed_hosts = settings_module.get('ALLOWED_HOSTS', [])
        if not isinstance(allowed_hosts, list):
            allowed_hosts = list(allowed_hosts)
        
        for host in ['localhost', '127.0.0.1']:
            if host not in allowed_hosts:
                allowed_hosts.append(host)
        
        settings_module['ALLOWED_HOSTS'] = allowed_hosts
        
        # Update service status
        self.service_registry.update_service_status(
            app_id=self.app_id,
            instance_id=self.instance_id,
            status="running"
        )
        
        return settings_module
    
    def configure_urls(self, urls_module: Any) -> None:
        """
        Configure Django URLs with DynaPort functionality.
        
        Args:
            urls_module: Django URLs module to configure
        """
        self.urls_module = urls_module
        
        # Add health endpoint
        self.add_health_endpoint()
    
    def add_health_endpoint(self) -> None:
        """
        Add a health check endpoint to the Django application.
        
        This method adds a health check endpoint to the Django application
        that returns a JSON response with the application's status.
        """
        if self.urls_module is None:
            return
            
        # Import Django modules
        try:
            from django.urls import path
            from django.http import JsonResponse
        except ImportError:
            return
        
        # Create health check view
        def health_check(request):
            return JsonResponse({
                "status": "healthy",
                "app_id": self.app_id,
                "instance_id": self.instance_id,
                "port": self.port
            })
        
        # Create DynaPort info view
        def dynaport_info(request):
            return JsonResponse({
                "app_id": self.app_id,
                "instance_id": self.instance_id,
                "name": self.name,
                "port": self.port,
                "dependencies": self.dependencies,
                "metadata": self.metadata,
                "technology": self.technology
            })
        
        # Add URLs to urlpatterns
        endpoint = self.health_endpoint
        if endpoint.startswith('/'):
            endpoint = endpoint[1:]
        
        # Get urlpatterns from urls_module
        if hasattr(self.urls_module, 'urlpatterns'):
            urlpatterns = getattr(self.urls_module, 'urlpatterns')
            
            # Add health check URL
            urlpatterns.append(path(endpoint, health_check))
            
            # Add DynaPort info URL
            urlpatterns.append(path('dynaport/info/', dynaport_info))
    
    def run_app(self, **kwargs) -> None:
        """
        Run the Django application with the allocated port.
        
        Args:
            **kwargs: Additional arguments to pass to runserver
        """
        try:
            # Import Django modules
            import django
            from django.core.management import execute_from_command_line
            
            # Build command line arguments
            argv = ['manage.py', 'runserver', f'0.0.0.0:{self.port}']
            
            # Add any additional arguments
            for key, value in kwargs.items():
                if isinstance(value, bool) and value:
                    argv.append(f'--{key}')
                else:
                    argv.append(f'--{key}={value}')
            
            # Run Django server
            execute_from_command_line(argv)
        except ImportError:
            print("Django is not installed. Please install Django to use this adapter.")
            sys.exit(1)
        finally:
            # Update service status when app stops
            self.service_registry.update_service_status(
                app_id=self.app_id,
                instance_id=self.instance_id,
                status="stopped"
            )


def configure_django(
    app_id: str,
    settings_module: Dict[str, Any],
    urls_module: Any = None,
    instance_id: Optional[str] = None,
    name: Optional[str] = None,
    preferred_port: Optional[int] = None,
    health_endpoint: str = "/health/",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], DynaPortDjango]:
    """
    Configure a Django application with DynaPort integration.
    
    Args:
        app_id: Unique identifier for the application
        settings_module: Django settings module to configure
        urls_module: Django URLs module to configure
        instance_id: Unique identifier for this instance (auto-generated if None)
        name: Human-readable name for the application
        preferred_port: Preferred port for the application
        health_endpoint: Endpoint for health checks
        dependencies: List of service IDs this application depends on
        metadata: Additional metadata for the application
        
    Returns:
        Tuple of (configured settings module, DynaPortDjango instance)
    """
    # Create DynaPort integration
    dynaport = DynaPortDjango(
        app_id=app_id,
        instance_id=instance_id,
        name=name,
        preferred_port=preferred_port,
        health_endpoint=health_endpoint,
        dependencies=dependencies,
        metadata=metadata
    )
    
    # Configure settings
    settings = dynaport.wrap_app(settings_module)
    
    # Configure URLs if provided
    if urls_module:
        dynaport.configure_urls(urls_module)
    
    return settings, dynaport
