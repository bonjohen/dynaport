"""
Service registry module for DynaPort.

This module provides framework-agnostic functionality for registering, discovering,
and monitoring services running in the DynaPort ecosystem.
"""

import json
import time
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Set, Tuple, Union
from dataclasses import dataclass, asdict, field


@dataclass
class ServiceInfo:
    """Information about a registered service."""
    
    app_id: str
    instance_id: str
    name: str
    port: int
    host: str = "127.0.0.1"
    status: str = "unknown"  # unknown, starting, running, stopped, error
    health_endpoint: Optional[str] = None
    last_health_check: Optional[float] = None
    health_status: str = "unknown"  # unknown, healthy, unhealthy
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # New fields for framework-agnostic approach
    technology: Optional[str] = None  # e.g., "flask", "django", "express", "spring", etc.
    health_check_type: str = "http"  # http, tcp, command, custom
    health_check_command: Optional[str] = None  # For command-based health checks
    health_check_custom: Optional[Dict[str, Any]] = field(default_factory=dict)  # For custom health checks
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ServiceInfo':
        """Create from dictionary representation."""
        return cls(**data)
    
    @property
    def service_id(self) -> str:
        """Get the unique service ID."""
        return f"{self.app_id}:{self.instance_id}"
    
    @property
    def url(self) -> str:
        """Get the base URL for the service."""
        return f"http://{self.host}:{self.port}"


class ServiceRegistry:
    """
    Registry for services running in the DynaPort ecosystem.
    
    This class handles service registration, discovery, and health monitoring.
    It is completely framework-agnostic and can be used with any type of service.
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        health_check_interval: int = 60
    ):
        """
        Initialize the service registry.
        
        Args:
            storage_path: Path to store service registry data.
                          Defaults to ~/.dynaport/services.json
            health_check_interval: Interval in seconds between health checks
        """
        if storage_path is None:
            home_dir = Path.home()
            self.storage_dir = home_dir / ".dynaport"
            self.storage_dir.mkdir(exist_ok=True)
            self.storage_path = self.storage_dir / "services.json"
        else:
            self.storage_path = Path(storage_path)
            self.storage_dir = self.storage_path.parent
            self.storage_dir.mkdir(exist_ok=True)
        
        self.services: Dict[str, ServiceInfo] = {}
        self.health_check_interval = health_check_interval
        self.health_check_thread: Optional[threading.Thread] = None
        self.stop_health_check = threading.Event()
        
        # Load existing services
        self._load_services()
        
        # Start health check thread
        self._start_health_check_thread()
    
    def _load_services(self) -> None:
        """Load services from storage."""
        if not self.storage_path.exists():
            return
        
        try:
            with open(self.storage_path, 'r') as f:
                services_data = json.load(f)
                
            for service_data in services_data:
                service = ServiceInfo.from_dict(service_data)
                self.services[service.service_id] = service
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    
    def _save_services(self) -> None:
        """Save services to storage."""
        services_data = [service.to_dict() for service in self.services.values()]
        
        with open(self.storage_path, 'w') as f:
            json.dump(services_data, f, indent=2)
    
    def _start_health_check_thread(self) -> None:
        """Start the health check thread."""
        if self.health_check_thread is not None and self.health_check_thread.is_alive():
            return
            
        self.stop_health_check.clear()
        self.health_check_thread = threading.Thread(
            target=self._health_check_worker,
            daemon=True
        )
        self.health_check_thread.start()
    
    def _health_check_worker(self) -> None:
        """Worker thread for performing health checks."""
        while not self.stop_health_check.is_set():
            self._check_all_services_health()
            self.stop_health_check.wait(self.health_check_interval)
    
    def _check_all_services_health(self) -> None:
        """Check the health of all registered services."""
        for service_id, service in list(self.services.items()):
            try:
                self._check_service_health(service)
            except Exception as e:
                service.health_status = "unhealthy"
                service.last_health_check = time.time()
    
    def _check_service_health(self, service: ServiceInfo) -> None:
        """
        Check the health of a specific service.
        
        Args:
            service: Service to check
        """
        # Skip if no health check is configured
        if not service.health_endpoint and service.health_check_type != "tcp" and not service.health_check_command:
            return
            
        service.last_health_check = time.time()
        
        # Perform health check based on type
        if service.health_check_type == "http":
            self._check_http_health(service)
        elif service.health_check_type == "tcp":
            self._check_tcp_health(service)
        elif service.health_check_type == "command":
            self._check_command_health(service)
        elif service.health_check_type == "custom":
            self._check_custom_health(service)
    
    def _check_http_health(self, service: ServiceInfo) -> None:
        """
        Check health using HTTP endpoint.
        
        Args:
            service: Service to check
        """
        if not service.health_endpoint:
            service.health_status = "unknown"
            return
            
        try:
            health_url = f"{service.url}{service.health_endpoint}"
            response = requests.get(health_url, timeout=5)
            
            if response.status_code == 200:
                service.health_status = "healthy"
            else:
                service.health_status = "unhealthy"
        except requests.RequestException:
            service.health_status = "unhealthy"
    
    def _check_tcp_health(self, service: ServiceInfo) -> None:
        """
        Check health using TCP connection.
        
        Args:
            service: Service to check
        """
        import socket
        
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex((service.host, service.port))
                if result == 0:
                    service.health_status = "healthy"
                else:
                    service.health_status = "unhealthy"
        except (socket.error, OSError):
            service.health_status = "unhealthy"
    
    def _check_command_health(self, service: ServiceInfo) -> None:
        """
        Check health using command execution.
        
        Args:
            service: Service to check
        """
        if not service.health_check_command:
            service.health_status = "unknown"
            return
            
        import subprocess
        
        try:
            # Replace placeholders in command
            command = service.health_check_command
            command = command.replace("{host}", service.host)
            command = command.replace("{port}", str(service.port))
            
            # Run the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                service.health_status = "healthy"
            else:
                service.health_status = "unhealthy"
        except (subprocess.SubprocessError, OSError):
            service.health_status = "unhealthy"
    
    def _check_custom_health(self, service: ServiceInfo) -> None:
        """
        Check health using custom logic.
        
        Args:
            service: Service to check
        """
        # Custom health checks are implemented by adapters
        # This is just a placeholder
        service.health_status = "unknown"
    
    def register_service(self, service: ServiceInfo) -> None:
        """
        Register a service with the registry.
        
        Args:
            service: Service information to register
        """
        self.services[service.service_id] = service
        self._save_services()
    
    def unregister_service(self, app_id: str, instance_id: str) -> None:
        """
        Unregister a service from the registry.
        
        Args:
            app_id: Application ID
            instance_id: Instance ID
        """
        service_id = f"{app_id}:{instance_id}"
        if service_id in self.services:
            del self.services[service_id]
            self._save_services()
    
    def get_service(self, app_id: str, instance_id: str) -> Optional[ServiceInfo]:
        """
        Get information about a specific service.
        
        Args:
            app_id: Application ID
            instance_id: Instance ID
            
        Returns:
            Service information, or None if not found
        """
        service_id = f"{app_id}:{instance_id}"
        return self.services.get(service_id)
    
    def get_all_services(self) -> List[ServiceInfo]:
        """
        Get information about all registered services.
        
        Returns:
            List of all registered services
        """
        return list(self.services.values())
    
    def get_services_by_app(self, app_id: str) -> List[ServiceInfo]:
        """
        Get all services for a specific application.
        
        Args:
            app_id: Application ID
            
        Returns:
            List of services for the application
        """
        return [
            service for service in self.services.values()
            if service.app_id == app_id
        ]
    
    def get_services_by_technology(self, technology: str) -> List[ServiceInfo]:
        """
        Get all services using a specific technology.
        
        Args:
            technology: Technology name (e.g., "flask", "django", "express")
            
        Returns:
            List of services using the specified technology
        """
        return [
            service for service in self.services.values()
            if service.technology == technology
        ]
    
    def update_service_status(
        self, 
        app_id: str, 
        instance_id: str, 
        status: str
    ) -> None:
        """
        Update the status of a service.
        
        Args:
            app_id: Application ID
            instance_id: Instance ID
            status: New status (unknown, starting, running, stopped, error)
        """
        service_id = f"{app_id}:{instance_id}"
        if service_id in self.services:
            self.services[service_id].status = status
            self._save_services()
    
    def get_dependency_order(self) -> List[Set[str]]:
        """
        Get the dependency order for starting services.
        
        Returns:
            List of sets of service IDs, where each set contains services
            that can be started in parallel
        """
        # Build dependency graph
        graph: Dict[str, Set[str]] = {}
        reverse_graph: Dict[str, Set[str]] = {}
        
        for service_id, service in self.services.items():
            graph[service_id] = set()
            
            for dep in service.dependencies:
                graph[service_id].add(dep)
                
                if dep not in reverse_graph:
                    reverse_graph[dep] = set()
                    
                reverse_graph[dep].add(service_id)
        
        # Topological sort
        result: List[Set[str]] = []
        no_deps = {
            service_id for service_id in graph
            if not graph[service_id]
        }
        
        while no_deps:
            result.append(no_deps)
            
            next_no_deps = set()
            for service_id in no_deps:
                if service_id in reverse_graph:
                    for dependent in reverse_graph[service_id]:
                        graph[dependent].remove(service_id)
                        if not graph[dependent]:
                            next_no_deps.add(dependent)
            
            no_deps = next_no_deps
        
        return result
    
    def close(self) -> None:
        """Clean up resources used by the registry."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.stop_health_check.set()
            self.health_check_thread.join(timeout=1)
        
        self._save_services()
