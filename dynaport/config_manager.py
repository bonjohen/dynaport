"""
Configuration management module for DynaPort.

This module provides functionality for managing configuration settings
for applications, environments, and instances.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union


class ConfigManager:
    """
    Manages configuration settings for DynaPort applications.
    
    This class handles loading, merging, and accessing configuration
    settings from various sources with support for inheritance and overrides.
    """
    
    def __init__(
        self,
        config_dir: Optional[str] = None,
        environment: str = "development"
    ):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files.
                        Defaults to ~/.dynaport/config
            environment: Current environment (development, testing, production)
        """
        self.environment = environment
        
        if config_dir is None:
            home_dir = Path.home()
            self.config_dir = home_dir / ".dynaport" / "config"
        else:
            self.config_dir = Path(config_dir)
            
        self.config_dir.mkdir(exist_ok=True, parents=True)
        
        # Create default config if it doesn't exist
        self._ensure_default_config()
        
        # Load the base configuration
        self.config = self._load_config("default")
        
        # Load environment-specific configuration
        env_config = self._load_config(environment)
        if env_config:
            self._merge_config(self.config, env_config)
    
    def _ensure_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        default_config_path = self.config_dir / "default.yaml"
        
        if not default_config_path.exists():
            default_config = {
                "port_allocator": {
                    "port_range": [8000, 9000],
                    "reserved_ports": []
                },
                "service_registry": {
                    "discovery_port": 7000,
                    "health_check_interval": 60
                },
                "logging": {
                    "level": "INFO",
                    "file": "~/.dynaport/logs/dynaport.log"
                }
            }
            
            with open(default_config_path, 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
    
    def _load_config(self, name: str) -> Dict[str, Any]:
        """
        Load configuration from a YAML file.
        
        Args:
            name: Name of the configuration file (without extension)
            
        Returns:
            Dictionary containing configuration settings
        """
        config_path = self.config_dir / f"{name}.yaml"
        
        if not config_path.exists():
            return {}
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, FileNotFoundError):
            return {}
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Merge override configuration into base configuration.
        
        Args:
            base: Base configuration dictionary (modified in-place)
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def get_app_config(self, app_id: str, instance_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific application and instance.
        
        Args:
            app_id: Application identifier
            instance_id: Optional instance identifier for multi-instance apps
            
        Returns:
            Dictionary containing merged configuration for the app/instance
        """
        # Start with the base configuration
        app_config = self.config.copy()
        
        # Load application-specific configuration
        app_specific = self._load_config(f"app_{app_id}")
        if app_specific:
            self._merge_config(app_config, app_specific)
        
        # Load environment-specific application configuration
        env_app_specific = self._load_config(f"app_{app_id}_{self.environment}")
        if env_app_specific:
            self._merge_config(app_config, env_app_specific)
        
        # Load instance-specific configuration if provided
        if instance_id:
            instance_specific = self._load_config(f"instance_{app_id}_{instance_id}")
            if instance_specific:
                self._merge_config(app_config, instance_specific)
                
            # Load environment-specific instance configuration
            env_instance_specific = self._load_config(
                f"instance_{app_id}_{instance_id}_{self.environment}"
            )
            if env_instance_specific:
                self._merge_config(app_config, env_instance_specific)
        
        return app_config
    
    def save_app_config(
        self, 
        app_id: str, 
        config: Dict[str, Any],
        instance_id: Optional[str] = None,
        environment_specific: bool = False
    ) -> None:
        """
        Save configuration for a specific application.
        
        Args:
            app_id: Application identifier
            config: Configuration dictionary to save
            instance_id: Optional instance identifier for multi-instance apps
            environment_specific: Whether to save as environment-specific config
        """
        if instance_id:
            if environment_specific:
                config_name = f"instance_{app_id}_{instance_id}_{self.environment}"
            else:
                config_name = f"instance_{app_id}_{instance_id}"
        else:
            if environment_specific:
                config_name = f"app_{app_id}_{self.environment}"
            else:
                config_name = f"app_{app_id}"
        
        config_path = self.config_dir / f"{config_name}.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
    
    def get_config_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a specific configuration value using dot notation.
        
        Args:
            key_path: Path to the configuration value (e.g., "port_allocator.port_range")
            default: Default value to return if the key doesn't exist
            
        Returns:
            Configuration value, or default if not found
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_config_value(self, key_path: str, value: Any) -> None:
        """
        Set a specific configuration value using dot notation.
        
        Args:
            key_path: Path to the configuration value (e.g., "port_allocator.port_range")
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        
        # Save the updated configuration
        with open(self.config_dir / f"{self.environment}.yaml", 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
