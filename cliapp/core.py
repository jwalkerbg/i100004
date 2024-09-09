# cliapp/core.py

def run_app(config):
    """Run the application with the given configuration."""

    # Print verbose mode status
    if config.get('verbose'):
        print("Running in verbose mode.")
        print(f"Final Configuration: {config}")

    # MQTT configuration
    mqtt_config = config['mqtt']
    print(f"\nMQTT Configuration:")
    print(f"  Host: {mqtt_config['host']}")
    print(f"  Port: {mqtt_config['port']}")
    print(f"  Username: {mqtt_config.get('username', 'N/A')}")
    print(f"  Password: {mqtt_config.get('password', 'N/A')}")

    # Device configuration
    device_config = config['device']
    print(f"\nDevice Configuration:")
    print(f"  Device Name: {device_config['name']}")
    print(f"  Timeout: {device_config['timeout']} seconds")
    print(f"  Port: {device_config['port']}")

    # Example of using the configuration for application logic
    # Here you would add the logic to connect to the MQTT server and communicate with the device
    # For this example, we simply print the configuration.
    print("\nApplication started with the above configuration...")
