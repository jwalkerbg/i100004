from typing import Dict, Any  # Import only the necessary types
import json
from jsonschema import validate, ValidationError
import os

# Step 1: Define default values (hardcoded in the module)
DEFAULT_CONFIG = {
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': 'guest',
        'password': 'guest',
        'client_id': 'mqttx_93919c20',
        'mac_address': '11:22:33:44:55:66',
        "timeout": 15.0
    },
    'device': {
        'name': 'UnknownDevice',
        'protocol': 'ttyUSB0',
        'timeout': 30
    },
    'verbose': False
}

# Define the JSON schema for the configuration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "mqtt": {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                "username": {"type": "string"},
                "password": {"type": "string"},
                "client_id": {"type": "string"},
                "mac_address": {"type": "string"},
                "timeout": {"type": "number"}
            },
            "required": ["host", "port"]
        },
        "device": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "string"},
                "timeout": {"type": "integer", "minimum": 1, "maximum": 600}
            },
            "required": ["name"]
        },
        "verbose": {"type": "boolean"}
    },
    "required": ["mqtt", "device"],
    "additionalProperties": False
}

def load_config(file_path='config.json'):
    """Load the configuration from a JSON file, handle errors if the file is missing or invalid."""
    if not os.path.exists(file_path):
        print(f"Configuration file {file_path} not found, using default values.")
        return {}

    try:
        with open(file_path, 'r') as file:
            config = json.load(file)

        # Step 2: Validate the loaded config against the schema
        validate(instance=config, schema=CONFIG_SCHEMA)
        return config

    except FileNotFoundError:
        print(f"Configuration file {file_path} not found, using default values.")
        return {}

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format in {file_path}: {e}")

    except ValidationError as e:
        raise ValueError(f"Configuration validation error in {file_path}: {e.message}")

    except Exception as e:
        raise RuntimeError(f"Failed to load configuration from {file_path}: {e}")

def merge_configs(defaults, config_file, config_cli):
    """Merge default config, file config, and CLI config with precedence to CLI > file > default."""
    config = defaults.copy()  # Start with defaults

    # Merge config.json into defaults
    deep_update(config,config_file)

    # Handle MQTT CLI overrides
    if config_cli.mqtt_host:
        config['mqtt']['host'] = config_cli.mqtt_host
    if config_cli.mqtt_port:
        config['mqtt']['port'] = config_cli.mqtt_port
    if config_cli.mqtt_username:
        config['mqtt']['username'] = config_cli.mqtt_username
    if config_cli.mqtt_password:
        config['mqtt']['password'] = config_cli.mqtt_password
    if config_cli.mqtt_client_id:
        config['mqtt']['client_id'] = config_cli.mqtt_client_id
    if config_cli.mqtt_mac_address:
        config['mqtt']['mac_address'] = config_cli.mqtt_mac_address
    if config_cli.mqtt_timeout:
        config['mqtt']['timeout'] = config_cli.mqtt_timeout

    # Handle Device CLI overrides
    if config_cli.device_name:
        config['device']['name'] = config_cli.device_name
    if config_cli.device_port:
        config['device']['port'] = config_cli.device_port
    if config_cli.device_timeout:
        config['device']['timeout'] = config_cli.device_timeout

    # Handle general options
    if config_cli.verbose is not None:
        config['verbose'] = config_cli.verbose

    return config

def deep_update(config: Dict[str, Any], config_file: Dict[str, Any]) -> None:
    """
    Recursively updates a dictionary (`config`) with the contents of another dictionary (`config_file`).
    It performs a deep merge, meaning that if a key contains a nested dictionary in both `config`
    and `config_file`, the nested dictionaries are merged instead of replaced.

    Parameters:
    - config (Dict[str, Any]): The original dictionary to be updated.
    - config_file (Dict[str, Any]): The dictionary containing updated values.

    Returns:
    - None: The update is done in place, so the `config` dictionary is modified directly.
    """
    for key, value in config_file.items():
        if isinstance(value, dict) and key in config and isinstance(config[key], dict):
            # If both values are dictionaries, recurse to merge deeply
            deep_update(config[key], value)
        else:
            # Otherwise, update the key with the new value from config_file
            config[key] = value
