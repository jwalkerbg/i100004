# cliapp/core.py

import time
from cliapp.mqtt_handler import MQTTHandler
from cliapp.logger_module import logger, string_handler
from cliapp.ms_protocol import CommandProtocol
from cliapp.mqtt_dispatcher import MQTTDispatcher

def run_app(config):
    """Run the application with the given configuration."""

    # Print verbose mode status
    if config.get('verbose'):
        log_configuration(config)

    #mqtt_config = config['mqtt']
    #device_config = config['device']
    ms_protocol = CommandProtocol(master_mac="1234567890A1", slave_mac="F412FACEF2E8", command_timeout=10)
    mqtt_dispatcher = MQTTDispatcher(protocol=ms_protocol)

    try:
        mqtt_handler = MQTTHandler(config=config,message_handler=mqtt_dispatcher)
        ms_protocol.define_mqtt_handler(mqtt_handler)   # needed for publishing commands
    except Exception as e:
        logger.error(f"Cannot create MQTTHandler object: {e}")
        mqtt_handler.exit_threads()
        return

    try:
        res = mqtt_handler.connect()
        if not res:
            mqtt_handler.exit_threads()
            return
    except Exception as e:
        logger.error(f"Cannot connect to the MQTT broker: {e}")
        mqtt_handler.exit_threads()
        return

    subscribe_topic = "@/1234567890A1/RSP/ASCIIHEX"
    try:
        res = mqtt_handler.subscribe(subscribe_topic)
        if not res:
            mqtt_handler.exit_threads()
            return
    except Exception as e:
        logger.error(f"Cannot subscribe to the MQTT broker: {e}")
        mqtt_handler.exit_threads()
        return

    payl = '{"cid":129,"client":"1234567890A1","command":"SR","data":""}'
    try:
        while True:
            # Simulate doing some work (replace this with actual logic)
            mqtt_handler.publish_message(f"@/{config['mqtt']['mac_address']}/CMD/ASCIIHEX",payl)
            time.sleep(5)  # Sleep to avoid busy-waiting
    except KeyboardInterrupt:
        # Graceful exit on Ctrl-C
        ms_protocol.queue_cmd.put((None, None))
        mqtt_handler.disconnect_and_exit()
        logger.warning("Application stopped by user (Ctrl-C). Exiting...")

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
    logger.info(f"  MAC address: {mqtt_config.get('mac_address', 'N/A')}")
    logger.info(f"  Timeout: {mqtt_config.get('timeout', 'N/A')}")
    logger.info(f"  Long payloads threshold: {mqtt_config.get('long_payload', 'N/A')}")

    # Device configuration
    device_config = config['device']
    logger.info(f"Device Configuration:")
    logger.info(f"  Device Name: {device_config['name']}")
    logger.info(f"  Timeout: {device_config['timeout']} seconds")
    logger.info(f"  Port: {device_config['port']}")

    logger.info("Application started with the above configuration...")
