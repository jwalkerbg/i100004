import json

# Step 1: Define default values (hardcoded in the module)
DEFAULT_CONFIG = {
    'name': 'DefaultUser',
    'verbose': False,
    'timeout': 30
}

def load_config(file_path='config.json'):
    """Load the configuration from a JSON file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        # If config.json is missing, return an empty dictionary
        return {}

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
