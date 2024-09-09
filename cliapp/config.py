import json
from jsonschema import validate, ValidationError
import os

# Step 1: Define default values (hardcoded in the module)
DEFAULT_CONFIG = {
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': 'guest',
        'password': 'guest'
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
                "password": {"type": "string"}
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
    config.update(config_file)

    # Handle MQTT CLI overrides
    if config_cli.mqtt_host:
        config['mqtt']['host'] = config_cli.mqtt_host
    if config_cli.mqtt_port:
        config['mqtt']['port'] = config_cli.mqtt_port
    if config_cli.mqtt_username:
        config['mqtt']['username'] = config_cli.mqtt_username
    if config_cli.mqtt_password:
        config['mqtt']['password'] = config_cli.mqtt_password

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
