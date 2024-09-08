import json
from jsonschema import validate, ValidationError
import os

# Step 1: Define default values (hardcoded in the module)
DEFAULT_CONFIG = {
    'name': 'DefaultUser',
    'verbose': False,
    'timeout': 30
}

# Define the JSON schema for the configuration
CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "verbose": {"type": "boolean"},
        "timeout": {"type": "integer", "minimum": 1, "maximum": 600}
    },
    "required": ["name"],
    "additionalProperties": False  # No additional properties are allowed
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

    # Override defaults with values from config.json
    config.update(config_file)

    # Override with command-line arguments (if provided)
    if config_cli.name:
        config['name'] = config_cli.name
    if config_cli.verbose:
        config['verbose'] = config_cli.verbose
    if config_cli.timeout:
        config['timeout'] = config_cli.timeout

    return config
