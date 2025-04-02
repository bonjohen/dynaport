"""
Framework-agnostic demonstration of DynaPort.

This script demonstrates how to use DynaPort's core functionality
without any framework-specific adapters.
"""

import time
import threading
import subprocess
import sys
from typing import Optional

from dynaport.core.port_allocator import PortAllocator
from dynaport.core.service_registry import ServiceRegistry, ServiceInfo
from dynaport.core.config_manager import ConfigManager


def run_http_server(port: int, stop_event: threading.Event) -> None:
    """
    Run a simple HTTP server on the specified port.
    
    Args:
        port: Port to listen on
        stop_event: Event to signal when to stop the server
    """
    # Use Python's built-in HTTP server
    import http.server
    import socketserver
    
    # Create a simple request handler
    class SimpleHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "healthy"}')
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'<html><body><h1>Hello from DynaPort!</h1>')
                self.wfile.write(f'<p>Running on port {port}</p>'.encode('utf-8'))
                self.wfile.write(b'</body></html>')
        
        def log_message(self, format, *args):
            # Customize logging
            print(f"[HTTP Server] {args[0]} {args[1]} {args[2]}")
    
    # Create and configure the server
    handler = SimpleHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    # Set a timeout so we can check the stop event
    httpd.timeout = 1
    
    print(f"HTTP server running on port {port}")
    print(f"Visit http://localhost:{port} in your browser")
    
    # Serve until the stop event is set
    while not stop_event.is_set():
        httpd.handle_request()
    
    # Close the server
    httpd.server_close()
    print("HTTP server stopped")


def main() -> None:
    """Run the demonstration."""
    print("DynaPort Framework-Agnostic Demonstration")
    print("----------------------------------------")
    
    # Create core components
    allocator = PortAllocator()
    registry = ServiceRegistry()
    config_manager = ConfigManager()
    
    # Get application ID from command line or use default
    app_id = sys.argv[1] if len(sys.argv) > 1 else "demo-app"
    instance_id = "default"
    
    # Allocate a port
    print(f"Allocating port for {app_id}...")
    port = allocator.allocate_port(f"{app_id}:{instance_id}")
    print(f"Allocated port: {port}")
    
    # Register the service
    print("Registering service...")
    service = ServiceInfo(
        app_id=app_id,
        instance_id=instance_id,
        name="Framework-Agnostic Demo",
        port=port,
        health_endpoint="/health",
        health_check_type="http",
        status="starting",
        technology="python",
        metadata={"demo": True}
    )
    
    registry.register_service(service)
    
    try:
        # Create a stop event
        stop_event = threading.Event()
        
        # Update service status
        registry.update_service_status(app_id, instance_id, "running")
        
        # Run the HTTP server in a separate thread
        server_thread = threading.Thread(
            target=run_http_server,
            args=(port, stop_event)
        )
        server_thread.daemon = True
        server_thread.start()
        
        # Show service information
        print("\nService Information:")
        print(f"  App ID: {app_id}")
        print(f"  Instance ID: {instance_id}")
        print(f"  Port: {port}")
        print(f"  URL: http://localhost:{port}")
        print(f"  Health: http://localhost:{port}/health")
        
        # Show other registered services
        print("\nOther Registered Services:")
        other_services = [s for s in registry.get_all_services() 
                         if s.service_id != f"{app_id}:{instance_id}"]
        
        if other_services:
            for service in other_services:
                print(f"  {service.name} ({service.app_id}:{service.instance_id})")
                print(f"    URL: {service.url}")
                print(f"    Status: {service.status}")
                print(f"    Health: {service.health_status}")
        else:
            print("  No other services registered")
        
        print("\nPress Ctrl+C to stop the server...")
        
        # Wait for user to press Ctrl+C
        try:
            while True:
                time.sleep(1)
                
                # Periodically check service health
                registry._check_service_health(service)
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
