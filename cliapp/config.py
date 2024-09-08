import json

def load_config(file_path='config.json'):
    """Load the configuration from a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def override_config(config, args):
    """Override the config with command-line arguments if provided."""
    if args.name:
        config['name'] = args.name
    if args.verbose:
        config['verbose'] = args.verbose
    return config
