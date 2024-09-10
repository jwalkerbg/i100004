# cliapp/core.py

import time
from cliapp.mqtt_handler import MQTTHandler

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
    print(f"  Client ID: {mqtt_config.get('client_id', 'N/A')}")
    print(f"  MAC address: {mqtt_config.get('mac_address', 'N/A')}")
    print(f"  Timeout: {mqtt_config.get('timeout', 'N/A')}")

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

    mqtt_handler = MQTTHandler(config)

    mqtt_handler.connect()
    mqtt_handler.connection_established.wait(mqtt_config['timeout'])

    subscribe_topic = "@/1234567890A1/RSP/ASCIIHEX"
    mqtt_handler.subscribe(subscribe_topic)
    mqtt_handler.subscription_estabilished.wait(mqtt_config['timeout'])

    payl = '{"cid":129,"client":"1234567890A1","command":"SR","data":""}'
    try:
        while True:
            # Simulate doing some work (replace this with actual logic)
            # print("Application is running... (Press Ctrl-C to exit)")
            mqtt_handler.publish_message(f"@/{config['mqtt']['mac_address']}/CMD/ASCIIHEX",payl)
            time.sleep(5)  # Sleep to avoid busy-waiting
    except KeyboardInterrupt:
        # Graceful exit on Ctrl-C

        mqtt_handler.queue_pub.put((None,None))
        mqtt_handler.mqtt_publish_thread.join()
        mqtt_handler.queue_rec.put((None,None))
        mqtt_handler.mqtt_receive_thread.join()

        print("\nApplication stopped by user (Ctrl-C). Exiting...")
