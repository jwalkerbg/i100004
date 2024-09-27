import os
from typing import Dict, Any  # Import only the necessary types
import json
from jsonschema import validate, ValidationError
from mqttms.logger_module import logger, string_handler

# Step 1: Define default values (hardcoded in the module)
DEFAULT_CONFIG = {
    'mqtt': {
        'host': 'localhost',
        'port': 1883,
        'username': 'guest',
        'password': 'guest',
        'client_id': 'mqttx_93919c20',
        "timeout": 15.0,
        "long_payload": 25
    },
    'ms': {
        'client_mac': '1234567890A1',
        'server_mac': 'F412FACEF2E8',
        'cmd_topic': '@/server_mac/CMD/format',
        'rsp_topic': '@/client_mac/RSP/format',
        'timeout': 5.0
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
                "timeout": {"type": "number"},
                "long_payload": {"type": "integer", "minimum": 10, "maximum": 32768}
            },
            "required": ["host", "port"]
        },
        "ms": {
            "type": "object",
            "properties": {
                "client_mac": {"type": "string"},
                "server_mac": {"type": "string"},
                "cmd_topic": {"type": "string"},
                "rsp_topic": {"type": "string"},
                "timeout": {"type": "number"}
            },
            "required": ["client_mac", "server_mac", "cmd_topic", "rsp_topic", "timeout"]
        },
        "verbose": {"type": "boolean"}
    },
    "required": ["mqtt", "ms"],
    "additionalProperties": False
}

def load_config(file_path: str='config.json'):
    # Convert None to default value of 'config.json'
    if file_path is None:
        logger.info(f"CFG: Using default '{file_path}'")
        file_path = 'config.json'

    """Load the configuration from a JSON file, handle errors if the file is missing or invalid."""
    if not os.path.exists(file_path):
        logger.warning(f"CFG: Configuration file {file_path} not found, using default values.")
        return {}

    try:
        with open(file_path, 'r') as file:
            config = json.load(file)

        # Step 2: Validate the loaded config against the schema
        validate(instance=config, schema=CONFIG_SCHEMA)
        return config   # no exception, valid configuration file

    except FileNotFoundError:
        logger.warning(f"CFG: Configuration file {file_path} not found, using default values.")
        return {}

    except json.JSONDecodeError as e:
        raise ValueError(f"CFG: Invalid JSON format in {file_path}: {e}")

    except ValidationError as e:
        raise ValueError(f"CFG: Configuration validation error in {file_path}: {e.message}")

    except Exception as e:
        raise RuntimeError(f"CFG: Failed to load configuration from {file_path}: {e}")

def merge_configs(defaults, config_file, config_cli=None):
    """Merge default config, file config, and CLI config with precedence to CLI > file > default."""
    config = defaults.copy()  # Start with defaults

    # Merge config.json into defaults
    deep_update(config,config_file)

    # Handle MQTT CLI overrides
    if config_cli:
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
        if config_cli.mqtt_timeout:
            config['mqtt']['timeout'] = config_cli.mqtt_timeout
        if config_cli.long_payload:
            config['mqtt']['long_payload'] = config_cli.long_payload

        # handle ms protocol overrides
        if config_cli.ms_client_mac:
            config['ms']['client_mac'] = config_cli.ms_client_mac
        if config_cli.ms_server_mac:
            config['ms']['server_mac'] = config_cli.ms_server_mac
        if config_cli.ms_cmd_topic:
            config['ms']['cmd_topic'] = config_cli.ms_cmd_topic
        if config_cli.ms_rsp_topic:
            config['ms']['rsp_topic'] = config_cli.ms_rsp_topic
        if config_cli.ms_timeout:
            config['ms']['timeout'] = config_cli.ms_timeout

        # Handle general options
        if config_cli.verbose is not None:
            config['verbose'] = config_cli.verbose

    # Print verbose mode status
    if config.get('verbose'):
        log_configuration(config)

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

def log_configuration(config):
    logger.info("Running in verbose mode.")
    logger.info(f"Final Configuration: {config}")

    # MQTT configuration
    mqtt_config = config['mqtt']
    logger.info(f"MQTT Configuration:")
    logger.info(f"  Host: {mqtt_config['host']}")
    logger.info(f"  Port: {mqtt_config['port']}")
    logger.info(f"  Username: {mqtt_config.get('username', 'N/A')}")
    logger.info(f"  Password: {mqtt_config.get('password', 'N/A')}")
    logger.info(f"  Client ID: {mqtt_config.get('client_id', 'N/A')}")
    logger.info(f"  Timeout: {mqtt_config.get('timeout', 'N/A')}")
    logger.info(f"  Long payloads threshold: {mqtt_config.get('long_payload', 'N/A')}")

    ms_config = config['ms']
    logger.info(f"MS Configuration")
    logger.info(f"  Client (master) MAC: {ms_config.get('client_mac', 'N/A')}")
    logger.info(f"  Server (slave) MAC:  {ms_config.get('server_mac', 'N/A')}")
    logger.info(f"  Command topic:  {ms_config.get('cmd_topic', 'N/A')}")
    logger.info(f"  Response topic: {ms_config.get('rsp_topic', 'N/A')}")
    logger.info(f"  MS protocol timeout: {ms_config.get('timeout', 'N/A')}")

    logger.info("Application started with the above configuration...")
