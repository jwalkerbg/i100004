import argparse

from cliapp.core import run_app
from cliapp.config import load_config, override_config

def parse_args(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description='cliapp CLI')
    parser.add_argument('--name', type=str, help='Name to greet')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose mode')
    return parser.parse_args(args)

def main():
    """Main entry point of the CLI."""
    # Step 1: Load the default configuration from config.json
    config = load_config()

    # Step 2: Parse command-line arguments
    args = parse_args()

    # Step 3: Override configuration with command-line arguments if provided
    config = override_config(config, args)

    # Step 4: Run the application using the final configuration
    run_app(config)

if __name__ == "__main__":
    main()
