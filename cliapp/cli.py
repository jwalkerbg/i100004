import argparse

from cliapp.core import run_app
from cliapp.config import load_config, merge_configs, DEFAULT_CONFIG

def parse_args():
    """Parse command-line arguments, including --verbose and --no-verbose, storing them in one variable."""
    parser = argparse.ArgumentParser(description='My CLI App with Config File and Overrides')

    # Add mutually exclusive group for --verbose and --no-verbose, storing result in 'verbose'
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('--verbose', dest='verbose', action='store_const', const=True, help='Enable verbose mode')
    verbosity_group.add_argument('--no-verbose', dest='verbose', action='store_const', const=False, help='Disable verbose mode')

    # Other arguments
    parser.add_argument('--name', type=str, help='Name to greet')
    parser.add_argument('--timeout', type=int, help='Set timeout in seconds')

    return parser.parse_args()
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
