# cliapp/core.py

import time
from cliapp.mqtt_handler import MQTTHandler
from cliapp.logger_module import logger, string_handler
from cliapp.ms_protocol import CommandProtocol
from cliapp.mqtt_dispatcher import MQTTDispatcher

def run_app(config):
    """Run the application with the given configuration."""

    try:
        ms_protocol = CommandProtocol(config=config)
        mqtt_dispatcher = MQTTDispatcher(protocol=ms_protocol)
        mqtt_handler = MQTTHandler(config=config,message_handler=mqtt_dispatcher)
        ms_protocol.define_mqtt_handler(mqtt_handler)   # needed for publishing commands
    except Exception as e:
        logger.error(f"Cannot create MQTTHandler object: {e}")
        mqtt_handler.exit_threads()
        return

    # connect broker
    try:
        res = mqtt_handler.connect()
        if not res:
            mqtt_handler.exit_threads()
            return
    except Exception as e:
        logger.error(f"Cannot connect to the MQTT broker: {e}")
        mqtt_handler.exit_threads()
        return

    # subscribe for MS protocol
    try:
        res = ms_protocol.subscribe(ms_protocol.construct_rsp_topic())
        if not res:
            logger.warning(f"CORE: Not successful subscription. Giving up")
            mqtt_handler.exit_threads()
            return
    except Exception as e:
        logger.error(f"Cannot subscribe to the MQTT broker: {e}")
        gracefull_exit(ms_protocol,mqtt_handler)
        return

    payl = '{"cid":129,"client":"1234567890A1","command":"SR","data":""}'
    try:
        while True:
            # Simulate doing some work (replace this with actual logic)
            topic = ms_protocol.construct_cmd_topic()
            logger.info(f"CORE: {topic}")
            ms_protocol.put_command(topic,payl)
            ms_protocol.response_received.wait()
            logger.info(f"CORE: {ms_protocol.response}")
            ms_protocol.response_received.clear()
            time.sleep(5)  # Sleep to avoid busy-waiting
    except KeyboardInterrupt:
        # Graceful exit on Ctrl-C
        gracefull_exit(ms_protocol,mqtt_handler)
        #ms_protocol.queue_cmd.put((None, None))
        #mqtt_handler.disconnect_and_exit()
        logger.warning("Application stopped by user (Ctrl-C). Exiting...")

def gracefull_exit(protocol,mqtthandler):
        protocol.queue_cmd.put((None, None))
        mqtthandler.disconnect_and_exit()
