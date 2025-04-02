"""
Unit tests for the port allocator module.
"""

import json
import socket
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from dynaport.port_allocator import PortAllocator


class TestPortAllocator:
    """Test cases for the PortAllocator class."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Create a temporary directory for port assignments
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = Path(self.temp_dir.name) / "ports.json"

    def teardown_method(self):
        """Clean up test environment after each test."""
        self.temp_dir.cleanup()

    def test_init_default_values(self):
        """Test initialization with default values."""
        # Use a custom storage path to avoid interference with existing assignments
        allocator = PortAllocator(storage_path=str(self.storage_path))
        assert allocator.port_range == (8000, 9000)
        assert allocator.reserved_ports == set()
        assert isinstance(allocator.port_assignments, dict)

    def test_init_custom_values(self):
        """Test initialization with custom values."""
        allocator = PortAllocator(
            storage_path=str(self.storage_path),
            port_range=(5000, 6000),
            reserved_ports={5000, 5001}
        )
        assert allocator.port_range == (5000, 6000)
        assert allocator.reserved_ports == {5000, 5001}
        assert allocator.port_assignments == {}

    def test_load_port_assignments(self):
        """Test loading port assignments from storage."""
        # Create a port assignments file
        assignments = {"app1": 8001, "app2": 8002}
        with open(self.storage_path, 'w') as f:
            json.dump(assignments, f)

        # Load the assignments
        allocator = PortAllocator(storage_path=str(self.storage_path))
        assert allocator.port_assignments == assignments

    def test_save_port_assignments(self):
        """Test saving port assignments to storage."""
        allocator = PortAllocator(storage_path=str(self.storage_path))
        allocator.port_assignments = {"app1": 8001, "app2": 8002}
        allocator._save_port_assignments()

        # Check that the file was created with the correct content
        with open(self.storage_path, 'r') as f:
            saved_assignments = json.load(f)

        assert saved_assignments == {"app1": 8001, "app2": 8002}

    @mock.patch('socket.socket')
    def test_is_port_available_true(self, mock_socket):
        """Test checking if a port is available (port is available)."""
        # Mock socket to indicate port is available
        mock_socket_instance = mock.MagicMock()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        allocator = PortAllocator()
        assert allocator.is_port_available(8000) is True

        # Verify socket was used correctly
        # Note: We don't check the exact number of calls because the implementation
        # might use socket in different ways
        mock_socket.assert_called_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket_instance.bind.assert_called_once_with(('127.0.0.1', 8000))

    @mock.patch('socket.socket')
    def test_is_port_available_false_socket_error(self, mock_socket):
        """Test checking if a port is available (port is in use)."""
        # Mock socket to indicate port is in use
        mock_socket_instance = mock.MagicMock()
        mock_socket_instance.bind.side_effect = socket.error()
        mock_socket.return_value.__enter__.return_value = mock_socket_instance

        allocator = PortAllocator()
        assert allocator.is_port_available(8000) is False

    def test_is_port_available_false_reserved(self):
        """Test checking if a port is available (port is reserved)."""
        allocator = PortAllocator(reserved_ports={8000})
        assert allocator.is_port_available(8000) is False

    @mock.patch.object(PortAllocator, 'is_port_available')
    def test_find_available_port_success(self, mock_is_port_available):
        """Test finding an available port (success case)."""
        # Mock is_port_available to return True for port 8000
        mock_is_port_available.side_effect = lambda p: p == 8000

        allocator = PortAllocator(port_range=(8000, 8010))
        port = allocator.find_available_port()

        assert port == 8000

    @mock.patch.object(PortAllocator, 'is_port_available')
    def test_find_available_port_none_available(self, mock_is_port_available):
        """Test finding an available port (no ports available)."""
        # Mock is_port_available to always return False
        mock_is_port_available.return_value = False

        allocator = PortAllocator(port_range=(8000, 8010))

        with pytest.raises(RuntimeError):
            allocator.find_available_port()

    @mock.patch.object(PortAllocator, 'is_port_available')
    def test_allocate_port_already_assigned(self, mock_is_port_available):
        """Test allocating a port that is already assigned."""
        # Mock is_port_available to return True
        mock_is_port_available.return_value = True

        allocator = PortAllocator(storage_path=str(self.storage_path))
        allocator.port_assignments = {"app1": 8001}

        port = allocator.allocate_port("app1")

        assert port == 8001
        assert allocator.port_assignments == {"app1": 8001}

    @mock.patch.object(PortAllocator, 'is_port_available')
    def test_allocate_port_preferred_available(self, mock_is_port_available):
        """Test allocating a preferred port that is available."""
        # Mock is_port_available to return True for preferred port
        mock_is_port_available.side_effect = lambda p: p == 8002

        allocator = PortAllocator(storage_path=str(self.storage_path))

        port = allocator.allocate_port("app1", preferred_port=8002)

        assert port == 8002
        assert allocator.port_assignments == {"app1": 8002}

    @mock.patch.object(PortAllocator, 'find_available_port')
    @mock.patch.object(PortAllocator, 'is_port_available')
    def test_allocate_port_find_available(self, mock_is_port_available, mock_find_available_port):
        """Test allocating a port by finding an available one."""
        # Mock is_port_available to return False for preferred port
        mock_is_port_available.return_value = False

        # Mock find_available_port to return 8003
        mock_find_available_port.return_value = 8003

        allocator = PortAllocator(storage_path=str(self.storage_path))

        port = allocator.allocate_port("app1", preferred_port=8002)

        assert port == 8003
        assert allocator.port_assignments == {"app1": 8003}

    def test_release_port(self):
        """Test releasing a port allocation."""
        allocator = PortAllocator(storage_path=str(self.storage_path))
        allocator.port_assignments = {"app1": 8001, "app2": 8002}

        allocator.release_port("app1")

        assert allocator.port_assignments == {"app2": 8002}

        # Check that the assignments were saved
        with open(self.storage_path, 'r') as f:
            saved_assignments = json.load(f)

        assert saved_assignments == {"app2": 8002}

    def test_get_assigned_port(self):
        """Test getting an assigned port."""
        allocator = PortAllocator()
        allocator.port_assignments = {"app1": 8001, "app2": 8002}

        assert allocator.get_assigned_port("app1") == 8001
        assert allocator.get_assigned_port("app2") == 8002
        assert allocator.get_assigned_port("app3") is None

    def test_get_all_assignments(self):
        """Test getting all port assignments."""
        allocator = PortAllocator()
        allocator.port_assignments = {"app1": 8001, "app2": 8002}

        assignments = allocator.get_all_assignments()

        assert assignments == {"app1": 8001, "app2": 8002}

        # Check that the returned value is a copy
        assignments["app3"] = 8003
        assert "app3" not in allocator.port_assignments

    def test_reserve_unreserve_port(self):
        """Test reserving and unreserving ports."""
        allocator = PortAllocator()

        # Initially no reserved ports
        assert allocator.reserved_ports == set()

        # Reserve a port
        allocator.reserve_port(8000)
        assert allocator.reserved_ports == {8000}

        # Reserve another port
        allocator.reserve_port(8001)
        assert allocator.reserved_ports == {8000, 8001}

        # Unreserve a port
        allocator.unreserve_port(8000)
        assert allocator.reserved_ports == {8001}

        # Unreserve a port that isn't reserved
        allocator.unreserve_port(9000)
        assert allocator.reserved_ports == {8001}
