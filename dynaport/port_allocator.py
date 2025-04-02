"""
Port allocation module for DynaPort.

This module provides functionality for detecting available ports,
allocating ports to applications, and managing port assignments.
"""

import socket
import random
import json
import os
from pathlib import Path
from typing import Optional, List, Dict, Tuple, Set


class PortAllocator:
    """
    Manages port allocation and persistence for applications.
    
    This class handles the detection of available ports, allocation of ports
    to applications, and persistence of port assignments.
    """
    
    def __init__(
        self, 
        storage_path: Optional[str] = None,
        port_range: Tuple[int, int] = (8000, 9000),
        reserved_ports: Optional[Set[int]] = None
    ):
        """
        Initialize the port allocator.
        
        Args:
            storage_path: Path to store port assignments. Defaults to ~/.dynaport/ports.json
            port_range: Tuple of (min_port, max_port) for the range of ports to allocate from
            reserved_ports: Set of ports that should not be allocated automatically
        """
        self.port_range = port_range
        self.reserved_ports = reserved_ports or set()
        
        if storage_path is None:
            home_dir = Path.home()
            self.storage_dir = home_dir / ".dynaport"
            self.storage_dir.mkdir(exist_ok=True)
            self.storage_path = self.storage_dir / "ports.json"
        else:
            self.storage_path = Path(storage_path)
            self.storage_dir = self.storage_path.parent
            self.storage_dir.mkdir(exist_ok=True)
            
        self.port_assignments = self._load_port_assignments()
    
    def _load_port_assignments(self) -> Dict[str, int]:
        """
        Load port assignments from storage.
        
        Returns:
            Dictionary mapping application IDs to port numbers
        """
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_port_assignments(self) -> None:
        """Save port assignments to storage."""
        with open(self.storage_path, 'w') as f:
            json.dump(self.port_assignments, f, indent=2)
    
    def is_port_available(self, port: int) -> bool:
        """
        Check if a port is available for use.
        
        Args:
            port: Port number to check
            
        Returns:
            True if the port is available, False otherwise
        """
        if port in self.reserved_ports:
            return False
            
        try:
            # Try to bind to the port to see if it's available
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                s.bind(('127.0.0.1', port))
                return True
        except (socket.error, OSError):
            return False
    
    def find_available_port(self) -> int:
        """
        Find an available port within the configured range.
        
        Returns:
            An available port number
            
        Raises:
            RuntimeError: If no ports are available in the configured range
        """
        # First try ports that were previously assigned but might be free now
        used_ports = set(self.port_assignments.values())
        for port in used_ports:
            if self.port_range[0] <= port <= self.port_range[1] and self.is_port_available(port):
                return port
        
        # Then try random ports in the range
        available_ports = [
            p for p in range(self.port_range[0], self.port_range[1] + 1)
            if p not in self.reserved_ports and p not in used_ports
        ]
        
        random.shuffle(available_ports)
        
        for port in available_ports:
            if self.is_port_available(port):
                return port
        
        # If we get here, no ports are available
        raise RuntimeError(
            f"No available ports found in range {self.port_range[0]}-{self.port_range[1]}"
        )
    
    def allocate_port(self, app_id: str, preferred_port: Optional[int] = None) -> int:
        """
        Allocate a port for an application.
        
        Args:
            app_id: Unique identifier for the application
            preferred_port: Preferred port to allocate, if available
            
        Returns:
            Allocated port number
        """
        # If the app already has a port assigned, return it
        if app_id in self.port_assignments:
            assigned_port = self.port_assignments[app_id]
            # Verify the port is still available
            if self.is_port_available(assigned_port):
                return assigned_port
        
        # Try to allocate the preferred port if specified
        if preferred_port is not None:
            if self.port_range[0] <= preferred_port <= self.port_range[1] and \
               self.is_port_available(preferred_port):
                self.port_assignments[app_id] = preferred_port
                self._save_port_assignments()
                return preferred_port
        
        # Find an available port
        port = self.find_available_port()
        self.port_assignments[app_id] = port
        self._save_port_assignments()
        return port
    
    def release_port(self, app_id: str) -> None:
        """
        Release a port allocation for an application.
        
        Args:
            app_id: Unique identifier for the application
        """
        if app_id in self.port_assignments:
            del self.port_assignments[app_id]
            self._save_port_assignments()
    
    def get_assigned_port(self, app_id: str) -> Optional[int]:
        """
        Get the port assigned to an application.
        
        Args:
            app_id: Unique identifier for the application
            
        Returns:
            Assigned port number, or None if no port is assigned
        """
        return self.port_assignments.get(app_id)
    
    def get_all_assignments(self) -> Dict[str, int]:
        """
        Get all port assignments.
        
        Returns:
            Dictionary mapping application IDs to port numbers
        """
        return self.port_assignments.copy()
    
    def reserve_port(self, port: int) -> None:
        """
        Reserve a port so it won't be automatically allocated.
        
        Args:
            port: Port number to reserve
        """
        self.reserved_ports.add(port)
    
    def unreserve_port(self, port: int) -> None:
        """
        Remove a port from the reserved list.
        
        Args:
            port: Port number to unreserve
        """
        if port in self.reserved_ports:
            self.reserved_ports.remove(port)
