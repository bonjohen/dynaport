"""
Unit tests for the configuration manager module.
"""

import os
import yaml
import tempfile
from pathlib import Path
from unittest import mock

import pytest

from dynaport.config_manager import ConfigManager


class TestConfigManager:
    """Test cases for the ConfigManager class."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Create a temporary directory for configuration files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        self.temp_dir.cleanup()
    
    def test_init_default_values(self):
        """Test initialization with default values."""
        with mock.patch.object(ConfigManager, '_ensure_default_config'):
            config_manager = ConfigManager()
            assert config_manager.environment == "development"
            assert config_manager.config == {}
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        with mock.patch.object(ConfigManager, '_ensure_default_config'):
            config_manager = ConfigManager(
                config_dir=str(self.config_dir),
                environment="production"
            )
            assert config_manager.environment == "production"
            assert config_manager.config_dir == self.config_dir
            assert config_manager.config == {}
    
    def test_ensure_default_config(self):
        """Test creating default configuration."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        # Check that the default config file was created
        default_config_path = self.config_dir / "default.yaml"
        assert default_config_path.exists()
        
        # Check the content of the default config
        with open(default_config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "port_allocator" in config
        assert "port_range" in config["port_allocator"]
        assert "service_registry" in config
        assert "logging" in config
    
    def test_load_config_existing_file(self):
        """Test loading configuration from an existing file."""
        # Create a test config file
        test_config = {
            "test": {
                "value1": "foo",
                "value2": 42
            }
        }
        
        test_config_path = self.config_dir / "test.yaml"
        with open(test_config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        # Load the config
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        loaded_config = config_manager._load_config("test")
        
        assert loaded_config == test_config
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from a nonexistent file."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        loaded_config = config_manager._load_config("nonexistent")
        
        assert loaded_config == {}
    
    def test_merge_config(self):
        """Test merging configuration dictionaries."""
        base_config = {
            "a": 1,
            "b": {
                "c": 2,
                "d": 3
            },
            "e": [4, 5]
        }
        
        override_config = {
            "a": 10,
            "b": {
                "c": 20,
                "f": 30
            },
            "g": 40
        }
        
        expected_result = {
            "a": 10,
            "b": {
                "c": 20,
                "d": 3,
                "f": 30
            },
            "e": [4, 5],
            "g": 40
        }
        
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        config_manager._merge_config(base_config, override_config)
        
        assert base_config == expected_result
    
    def test_get_app_config_base_only(self):
        """Test getting application configuration with only base config."""
        # Create base config
        base_config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }
        
        base_config_path = self.config_dir / "default.yaml"
        with open(base_config_path, 'w') as f:
            yaml.dump(base_config, f)
        
        # Get app config
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        app_config = config_manager.get_app_config("test-app")
        
        assert app_config == base_config
    
    def test_get_app_config_with_app_specific(self):
        """Test getting application configuration with app-specific config."""
        # Create base config
        base_config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }
        
        base_config_path = self.config_dir / "default.yaml"
        with open(base_config_path, 'w') as f:
            yaml.dump(base_config, f)
        
        # Create app-specific config
        app_config = {
            "port_allocator": {
                "port_range": [5000, 6000]
            },
            "app_specific": {
                "setting": "value"
            }
        }
        
        app_config_path = self.config_dir / "app_test-app.yaml"
        with open(app_config_path, 'w') as f:
            yaml.dump(app_config, f)
        
        # Get app config
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        result = config_manager.get_app_config("test-app")
        
        expected_result = {
            "port_allocator": {
                "port_range": [5000, 6000]
            },
            "app_specific": {
                "setting": "value"
            }
        }
        
        assert result == expected_result
    
    def test_get_app_config_with_env_specific(self):
        """Test getting application configuration with environment-specific config."""
        # Create base config
        base_config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }
        
        base_config_path = self.config_dir / "default.yaml"
        with open(base_config_path, 'w') as f:
            yaml.dump(base_config, f)
        
        # Create environment-specific config
        env_config = {
            "port_allocator": {
                "port_range": [7000, 8000]
            }
        }
        
        env_config_path = self.config_dir / "production.yaml"
        with open(env_config_path, 'w') as f:
            yaml.dump(env_config, f)
        
        # Create app-specific config
        app_config = {
            "app_specific": {
                "setting": "value"
            }
        }
        
        app_config_path = self.config_dir / "app_test-app.yaml"
        with open(app_config_path, 'w') as f:
            yaml.dump(app_config, f)
        
        # Create environment-specific app config
        env_app_config = {
            "app_specific": {
                "setting": "production-value"
            }
        }
        
        env_app_config_path = self.config_dir / "app_test-app_production.yaml"
        with open(env_app_config_path, 'w') as f:
            yaml.dump(env_app_config, f)
        
        # Get app config
        config_manager = ConfigManager(
            config_dir=str(self.config_dir),
            environment="production"
        )
        result = config_manager.get_app_config("test-app")
        
        expected_result = {
            "port_allocator": {
                "port_range": [7000, 8000]
            },
            "app_specific": {
                "setting": "production-value"
            }
        }
        
        assert result == expected_result
    
    def test_get_app_config_with_instance_specific(self):
        """Test getting application configuration with instance-specific config."""
        # Create base config
        base_config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }
        
        base_config_path = self.config_dir / "default.yaml"
        with open(base_config_path, 'w') as f:
            yaml.dump(base_config, f)
        
        # Create app-specific config
        app_config = {
            "app_specific": {
                "setting": "value"
            }
        }
        
        app_config_path = self.config_dir / "app_test-app.yaml"
        with open(app_config_path, 'w') as f:
            yaml.dump(app_config, f)
        
        # Create instance-specific config
        instance_config = {
            "instance_specific": {
                "setting": "instance-value"
            }
        }
        
        instance_config_path = self.config_dir / "instance_test-app_instance1.yaml"
        with open(instance_config_path, 'w') as f:
            yaml.dump(instance_config, f)
        
        # Get app config
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        result = config_manager.get_app_config("test-app", "instance1")
        
        expected_result = {
            "port_allocator": {
                "port_range": [8000, 9000]
            },
            "app_specific": {
                "setting": "value"
            },
            "instance_specific": {
                "setting": "instance-value"
            }
        }
        
        assert result == expected_result
    
    def test_save_app_config(self):
        """Test saving application configuration."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        app_config = {
            "port_allocator": {
                "port_range": [5000, 6000]
            },
            "app_specific": {
                "setting": "value"
            }
        }
        
        # Save app config
        config_manager.save_app_config("test-app", app_config)
        
        # Check that the file was created
        app_config_path = self.config_dir / "app_test-app.yaml"
        assert app_config_path.exists()
        
        # Check the content of the file
        with open(app_config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config == app_config
    
    def test_save_app_config_with_instance(self):
        """Test saving application configuration with instance ID."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        
        app_config = {
            "instance_specific": {
                "setting": "instance-value"
            }
        }
        
        # Save app config
        config_manager.save_app_config(
            "test-app",
            app_config,
            instance_id="instance1"
        )
        
        # Check that the file was created
        instance_config_path = self.config_dir / "instance_test-app_instance1.yaml"
        assert instance_config_path.exists()
        
        # Check the content of the file
        with open(instance_config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config == app_config
    
    def test_save_app_config_environment_specific(self):
        """Test saving environment-specific application configuration."""
        config_manager = ConfigManager(
            config_dir=str(self.config_dir),
            environment="production"
        )
        
        app_config = {
            "app_specific": {
                "setting": "production-value"
            }
        }
        
        # Save app config
        config_manager.save_app_config(
            "test-app",
            app_config,
            environment_specific=True
        )
        
        # Check that the file was created
        env_app_config_path = self.config_dir / "app_test-app_production.yaml"
        assert env_app_config_path.exists()
        
        # Check the content of the file
        with open(env_app_config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config == app_config
    
    def test_get_config_value(self):
        """Test getting a specific configuration value."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        config_manager.config = {
            "port_allocator": {
                "port_range": [8000, 9000],
                "reserved_ports": [8080, 8888]
            },
            "service_registry": {
                "discovery_port": 7000
            }
        }
        
        # Get existing values
        assert config_manager.get_config_value("port_allocator.port_range") == [8000, 9000]
        assert config_manager.get_config_value("service_registry.discovery_port") == 7000
        
        # Get nonexistent value with default
        assert config_manager.get_config_value("nonexistent", "default") == "default"
        assert config_manager.get_config_value("port_allocator.nonexistent", 42) == 42
    
    def test_set_config_value(self):
        """Test setting a specific configuration value."""
        config_manager = ConfigManager(config_dir=str(self.config_dir))
        config_manager.config = {
            "port_allocator": {
                "port_range": [8000, 9000]
            }
        }
        
        # Set an existing value
        config_manager.set_config_value("port_allocator.port_range", [5000, 6000])
        assert config_manager.config["port_allocator"]["port_range"] == [5000, 6000]
        
        # Set a new value in an existing section
        config_manager.set_config_value("port_allocator.reserved_ports", [8080])
        assert config_manager.config["port_allocator"]["reserved_ports"] == [8080]
        
        # Set a value in a new section
        config_manager.set_config_value("new_section.new_value", "test")
        assert config_manager.config["new_section"]["new_value"] == "test"
