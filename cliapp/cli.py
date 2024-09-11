import argparse

from cliapp.core import run_app
from cliapp.config import load_config, merge_configs, DEFAULT_CONFIG
from cliapp.logger_module import logger, string_handler

def parse_args():
    """Parse command-line arguments, including nested options for mqtt and device."""
    parser = argparse.ArgumentParser(description='My CLI App with Config File and Overrides')

    # MQTT options
    parser.add_argument('--mqtt-host', type=str, help='MQTT host to connect to')
    parser.add_argument('--mqtt-port', type=int, help='MQTT port')
    parser.add_argument('--mqtt-username', type=str, help='MQTT username')
    parser.add_argument('--mqtt-password', type=str, help='MQTT password')
    parser.add_argument('--mqtt-client-id', type=str, help="MQTT Client ID, used by the broker")
    parser.add_argument("--mqtt-mac-address", type=str, help="MAC address to use in MQTT topics. This is the MAC address of the device to work with.")
    parser.add_argument("--mqtt-timeout", type=float, help="Timeout to wait connection or other activity in MQTT handler.")
    parser.add_argument("--mqtt-lp", type=int, dest='long_payload', help="Determines threshold of long payloads. When they are longer that this value, a short string is logged instead of real payloads. --verbose makes real payloads to be logged always.")

    # Device options
    parser.add_argument('--device-name', type=str, help='Name of the device under test')
    parser.add_argument('--device-port', type=str, help='Port used to connect to the device (e.g., ttyUSB0)')
    parser.add_argument('--device-timeout', type=int, help='Device connection timeout in seconds')

    # Other general options can still be added
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument('--verbose', dest='verbose', action='store_const', const=True, help='Enable verbose mode')
    verbosity_group.add_argument('--no-verbose', dest='verbose', action='store_const', const=False, help='Disable verbose mode')

    return parser.parse_args()

def main():
    """Main entry point of the CLI."""

    # Step 0: Log the beginning
    logger.info("cliapp beginning")

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

    # Step 6: Final message
    logger.info("cliapp end")

if __name__ == "__main__":
    main()
