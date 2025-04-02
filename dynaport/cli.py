"""
Command-line interface for DynaPort.

This module provides a command-line interface for managing DynaPort
port allocations, service registry, and configuration.
"""

import os
import sys
import json
import click
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List

from .port_allocator import PortAllocator
from .service_registry import ServiceRegistry, ServiceInfo
from .config_manager import ConfigManager


@click.group()
@click.version_option()
def main():
    """DynaPort - Dynamic Port Management for Flask Applications."""
    pass


@main.group()
def port():
    """Manage port allocations."""
    pass


@port.command("allocate")
@click.argument("app_id", required=True)
@click.option("--preferred", "-p", type=int, help="Preferred port to allocate")
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def port_allocate(app_id: str, preferred: Optional[int], instance: Optional[str]):
    """Allocate a port for an application."""
    instance_id = instance or "default"
    allocator = PortAllocator()
    
    full_id = f"{app_id}:{instance_id}"
    port = allocator.allocate_port(full_id, preferred)
    
    click.echo(f"Allocated port {port} for {app_id} (instance: {instance_id})")
    click.echo(f"PORT={port}")


@port.command("release")
@click.argument("app_id", required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def port_release(app_id: str, instance: Optional[str]):
    """Release a port allocation for an application."""
    instance_id = instance or "default"
    allocator = PortAllocator()
    
    full_id = f"{app_id}:{instance_id}"
    allocator.release_port(full_id)
    
    click.echo(f"Released port for {app_id} (instance: {instance_id})")


@port.command("get")
@click.argument("app_id", required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def port_get(app_id: str, instance: Optional[str]):
    """Get the port allocated to an application."""
    instance_id = instance or "default"
    allocator = PortAllocator()
    
    full_id = f"{app_id}:{instance_id}"
    port = allocator.get_assigned_port(full_id)
    
    if port:
        click.echo(f"Port {port} is assigned to {app_id} (instance: {instance_id})")
        click.echo(f"PORT={port}")
    else:
        click.echo(f"No port assigned to {app_id} (instance: {instance_id})")
        sys.exit(1)


@port.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def port_list(json_output: bool):
    """List all port allocations."""
    allocator = PortAllocator()
    assignments = allocator.get_all_assignments()
    
    if json_output:
        click.echo(json.dumps(assignments, indent=2))
    else:
        if not assignments:
            click.echo("No port allocations found")
            return
            
        click.echo("Port allocations:")
        for app_id, port in assignments.items():
            click.echo(f"  {app_id}: {port}")


@port.command("check")
@click.argument("port", type=int, required=True)
def port_check(port: int):
    """Check if a port is available."""
    allocator = PortAllocator()
    available = allocator.is_port_available(port)
    
    if available:
        click.echo(f"Port {port} is available")
    else:
        click.echo(f"Port {port} is not available")
        sys.exit(1)


@port.command("find")
def port_find():
    """Find an available port."""
    allocator = PortAllocator()
    try:
        port = allocator.find_available_port()
        click.echo(f"Found available port: {port}")
        click.echo(f"PORT={port}")
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.group()
def service():
    """Manage service registry."""
    pass


@service.command("register")
@click.argument("app_id", required=True)
@click.argument("port", type=int, required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
@click.option("--name", "-n", help="Human-readable name for the service")
@click.option("--health-endpoint", help="Health check endpoint (e.g., /health)")
@click.option("--dependency", "-d", multiple=True, help="Service dependencies")
@click.option("--metadata", help="JSON metadata for the service")
def service_register(
    app_id: str,
    port: int,
    instance: Optional[str],
    name: Optional[str],
    health_endpoint: Optional[str],
    dependency: List[str],
    metadata: Optional[str]
):
    """Register a service with the registry."""
    instance_id = instance or "default"
    registry = ServiceRegistry()
    
    # Parse metadata if provided
    meta_dict = {}
    if metadata:
        try:
            meta_dict = json.loads(metadata)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON metadata", err=True)
            sys.exit(1)
    
    service = ServiceInfo(
        app_id=app_id,
        instance_id=instance_id,
        name=name or app_id,
        port=port,
        health_endpoint=health_endpoint,
        dependencies=list(dependency),
        metadata=meta_dict,
        status="running"
    )
    
    registry.register_service(service)
    click.echo(f"Registered service {app_id} (instance: {instance_id}) on port {port}")


@service.command("unregister")
@click.argument("app_id", required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def service_unregister(app_id: str, instance: Optional[str]):
    """Unregister a service from the registry."""
    instance_id = instance or "default"
    registry = ServiceRegistry()
    
    registry.unregister_service(app_id, instance_id)
    click.echo(f"Unregistered service {app_id} (instance: {instance_id})")


@service.command("list")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
@click.option("--app", help="Filter by application ID")
def service_list(json_output: bool, app: Optional[str]):
    """List all registered services."""
    registry = ServiceRegistry()
    
    if app:
        services = registry.get_services_by_app(app)
    else:
        services = registry.get_all_services()
    
    if json_output:
        services_data = [service.to_dict() for service in services]
        click.echo(json.dumps(services_data, indent=2))
    else:
        if not services:
            click.echo("No services registered")
            return
            
        click.echo("Registered services:")
        for service in services:
            click.echo(f"  {service.app_id} (instance: {service.instance_id}):")
            click.echo(f"    Name: {service.name}")
            click.echo(f"    URL: {service.url}")
            click.echo(f"    Status: {service.status}")
            click.echo(f"    Health: {service.health_status}")
            if service.dependencies:
                click.echo(f"    Dependencies: {', '.join(service.dependencies)}")


@service.command("get")
@click.argument("app_id", required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
@click.option("--json", "json_output", is_flag=True, help="Output in JSON format")
def service_get(app_id: str, instance: Optional[str], json_output: bool):
    """Get information about a specific service."""
    instance_id = instance or "default"
    registry = ServiceRegistry()
    
    service = registry.get_service(app_id, instance_id)
    
    if not service:
        click.echo(f"Service {app_id} (instance: {instance_id}) not found", err=True)
        sys.exit(1)
    
    if json_output:
        click.echo(json.dumps(service.to_dict(), indent=2))
    else:
        click.echo(f"Service: {service.app_id} (instance: {service.instance_id})")
        click.echo(f"  Name: {service.name}")
        click.echo(f"  URL: {service.url}")
        click.echo(f"  Status: {service.status}")
        click.echo(f"  Health: {service.health_status}")
        if service.dependencies:
            click.echo(f"  Dependencies: {', '.join(service.dependencies)}")
        if service.metadata:
            click.echo("  Metadata:")
            for key, value in service.metadata.items():
                click.echo(f"    {key}: {value}")


@service.command("status")
@click.argument("app_id", required=True)
@click.argument("status", type=click.Choice(["unknown", "starting", "running", "stopped", "error"]))
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def service_status(app_id: str, status: str, instance: Optional[str]):
    """Update the status of a service."""
    instance_id = instance or "default"
    registry = ServiceRegistry()
    
    registry.update_service_status(app_id, instance_id, status)
    click.echo(f"Updated status of {app_id} (instance: {instance_id}) to {status}")


@service.command("health")
@click.argument("app_id", required=True)
@click.option("--instance", "-i", help="Instance ID (defaults to 'default')")
def service_health(app_id: str, instance: Optional[str]):
    """Check the health of a service."""
    instance_id = instance or "default"
    registry = ServiceRegistry()
    
    service = registry.get_service(app_id, instance_id)
    
    if not service:
        click.echo(f"Service {app_id} (instance: {instance_id}) not found", err=True)
        sys.exit(1)
    
    if not service.health_endpoint:
        click.echo(f"Service {app_id} has no health endpoint configured", err=True)
        sys.exit(1)
    
    registry._check_service_health(service)
    
    click.echo(f"Health status: {service.health_status}")
    if service.health_status == "unhealthy":
        sys.exit(1)


@main.group()
def config():
    """Manage configuration."""
    pass


@config.command("get")
@click.argument("key_path", required=True)
@click.option("--app", help="Application ID for app-specific config")
@click.option("--instance", help="Instance ID for instance-specific config")
@click.option("--env", "-e", help="Environment (defaults to 'development')")
def config_get(
    key_path: str,
    app: Optional[str],
    instance: Optional[str],
    env: Optional[str]
):
    """Get a configuration value."""
    config_manager = ConfigManager(environment=env or "development")
    
    if app:
        app_config = config_manager.get_app_config(app, instance)
        
        # Navigate to the requested key
        keys = key_path.split('.')
        value = app_config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                click.echo(f"Key '{key_path}' not found in configuration", err=True)
                sys.exit(1)
        
        if isinstance(value, (dict, list)):
            click.echo(yaml.dump(value, default_flow_style=False))
        else:
            click.echo(value)
    else:
        value = config_manager.get_config_value(key_path)
        
        if value is None:
            click.echo(f"Key '{key_path}' not found in configuration", err=True)
            sys.exit(1)
        
        if isinstance(value, (dict, list)):
            click.echo(yaml.dump(value, default_flow_style=False))
        else:
            click.echo(value)


@config.command("set")
@click.argument("key_path", required=True)
@click.argument("value", required=True)
@click.option("--app", help="Application ID for app-specific config")
@click.option("--instance", help="Instance ID for instance-specific config")
@click.option("--env", "-e", help="Environment (defaults to 'development')")
@click.option("--json", "json_value", is_flag=True, help="Parse value as JSON")
def config_set(
    key_path: str,
    value: str,
    app: Optional[str],
    instance: Optional[str],
    env: Optional[str],
    json_value: bool
):
    """Set a configuration value."""
    config_manager = ConfigManager(environment=env or "development")
    
    # Parse value
    if json_value:
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            click.echo("Error: Invalid JSON value", err=True)
            sys.exit(1)
    else:
        # Try to convert to appropriate type
        if value.lower() == "true":
            parsed_value = True
        elif value.lower() == "false":
            parsed_value = False
        elif value.isdigit():
            parsed_value = int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            parsed_value = float(value)
        else:
            parsed_value = value
    
    if app:
        # Get current app config
        app_config = config_manager.get_app_config(app, instance)
        
        # Navigate to the parent of the target key
        keys = key_path.split('.')
        current = app_config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the value
        current[keys[-1]] = parsed_value
        
        # Save the updated config
        config_manager.save_app_config(
            app_id=app,
            config=app_config,
            instance_id=instance,
            environment_specific=(env is not None)
        )
    else:
        config_manager.set_config_value(key_path, parsed_value)
    
    click.echo(f"Set {key_path} = {parsed_value}")


@config.command("list")
@click.option("--app", help="Application ID for app-specific config")
@click.option("--instance", help="Instance ID for instance-specific config")
@click.option("--env", "-e", help="Environment (defaults to 'development')")
def config_list(
    app: Optional[str],
    instance: Optional[str],
    env: Optional[str]
):
    """List configuration values."""
    config_manager = ConfigManager(environment=env or "development")
    
    if app:
        app_config = config_manager.get_app_config(app, instance)
        click.echo(yaml.dump(app_config, default_flow_style=False))
    else:
        click.echo(yaml.dump(config_manager.config, default_flow_style=False))


if __name__ == "__main__":
    main()
