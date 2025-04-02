"""
Generic application example using DynaPort.

This example demonstrates how to use DynaPort with any application,
not just web frameworks. It shows how to allocate a port and use it
with a simple socket server.
"""

import socket
import threading
import time
import sys
from typing import Optional

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo


def run_socket_server(port: int, stop_event: threading.Event) -> None:
    """
    Run a simple socket server on the specified port.
    
    Args:
        port: Port to listen on
        stop_event: Event to signal when to stop the server
    """
    # Create a socket server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind to the port
        server_socket.bind(('0.0.0.0', port))
        server_socket.listen(5)
        server_socket.settimeout(1)  # 1 second timeout for accept
        
        print(f"Socket server running on port {port}")
        print(f"Send a message to the server using: nc localhost {port}")
        print("Type 'exit' to stop the server")
        
        # Accept connections until stop_event is set
        while not stop_event.is_set():
            try:
                client_socket, address = server_socket.accept()
                print(f"Connection from {address}")
                
                # Handle the client in a separate thread
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, address)
                )
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                # This is expected due to the timeout on accept
                pass
            except Exception as e:
                print(f"Error accepting connection: {e}")
                break
    finally:
        server_socket.close()
        print("Socket server stopped")


def handle_client(client_socket: socket.socket, address: tuple) -> None:
    """
    Handle a client connection.
    
    Args:
        client_socket: Socket for the client connection
        address: Client address
    """
    try:
        # Send welcome message
        client_socket.send(b"Welcome to DynaPort Socket Server!\n")
        client_socket.send(b"Type 'exit' to close the connection\n")
        
        # Receive data from the client
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
                
            # Convert bytes to string and strip whitespace
            message = data.decode('utf-8').strip()
            print(f"Received from {address}: {message}")
            
            # Check if the client wants to exit
            if message.lower() == 'exit':
                client_socket.send(b"Goodbye!\n")
                break
                
            # Echo the message back to the client
            response = f"Echo: {message}\n"
            client_socket.send(response.encode('utf-8'))
    except Exception as e:
        print(f"Error handling client {address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection from {address} closed")


def main() -> None:
    """Run the example."""
    # Create a port allocator
    allocator = PortAllocator()
    
    # Create a service registry
    registry = ServiceRegistry()
    
    # Allocate a port for our socket server
    app_id = "socket-server"
    instance_id = "example"
    port = allocator.allocate_port(f"{app_id}:{instance_id}")
    
    print(f"Allocated port {port} for {app_id}")
    
    # Register the service
    service = ServiceInfo(
        app_id=app_id,
        instance_id=instance_id,
        name="Socket Server Example",
        port=port,
        health_check_type="tcp",  # Use TCP health check for socket server
        status="starting",
        technology="socket",
        metadata={"example": True}
    )
    
    registry.register_service(service)
    print(f"Registered service {app_id}:{instance_id}")
    
    try:
        # Create a stop event
        stop_event = threading.Event()
        
        # Update service status
        registry.update_service_status(app_id, instance_id, "running")
        
        # Run the socket server in a separate thread
        server_thread = threading.Thread(
            target=run_socket_server,
            args=(port, stop_event)
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for user to press Ctrl+C
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            stop_event.set()
            server_thread.join(timeout=5)
    finally:
        # Update service status
        registry.update_service_status(app_id, instance_id, "stopped")
        
        # Unregister the service
        registry.unregister_service(app_id, instance_id)
        print(f"Unregistered service {app_id}:{instance_id}")
        
        # Release the port
        allocator.release_port(f"{app_id}:{instance_id}")
        print(f"Released port {port}")


if __name__ == "__main__":
    main()
