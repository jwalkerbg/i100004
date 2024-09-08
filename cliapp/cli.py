import argparse

from cliapp.core import run_app
from cliapp.config import load_config, merge_configs, DEFAULT_CONFIG

def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='cliapp CLI')
    parser.add_argument('--name', type=str, help='Name to greet')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode')
    parser.add_argument('--timeout', type=int, help='Set timeout in seconds')
    return parser.parse_args(args)

def main():
    """Main entry point of the CLI."""
    # Step 1: Load default values from the module
    defaults = DEFAULT_CONFIG

    # Step 2: Load the default configuration from config.json
    config_file = load_config()

    # Step 3: Parse command-line arguments
    args = parse_args()

    # Step 4: Merge default config, config.json, and command-line arguments
    final_config = merge_configs(defaults, config_file, args)

    # Step 5: Run the application using the final configuration
    run_app(final_config)

if __name__ == "__main__":
    main()
