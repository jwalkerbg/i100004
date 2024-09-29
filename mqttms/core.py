# mqttms/core.py

from typing import Dict
from mqttms.mqtt_handler import MQTTHandler
from mqttms.ms_protocol import MSProtocol
from mqttms.logger_module import logger
from mqttms.mqtt_dispatcher import MQTTDispatcher

class MQTTMS:
    def __init__(self, config:Dict, mqtt_dispatcher: MQTTDispatcher=None):
        '''
        Initialize objects
        '''

        logger.info(f"def __init__(self, config:Dict, mqtt_dispatcher: MQTTDispatcher=None):")
        # Create MQTTDispatcher object
        try:
            self.mqtt_dispatcher = None
            if mqtt_dispatcher == None:
                self.mqtt_dispatcher = MQTTDispatcher(config=config)
            else:
                self.mqtt_dispatcher = mqtt_dispatcher
        except MemoryError as e:
            raise e

        # Create MSProtocol object
        try:
            self.ms_protocol = MSProtocol(config=config)
        except MemoryError as e:
            logger.error(f"Memory error: {e}")
            raise e
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}")
            raise e
        except TypeError as e:
            logger.error(f"TypeError: {e}")
            raise e
        except ValueError as e:
            logger.error(f"ValueError: {e}")
            raise e
        except Exception as e:
            logger.error(f"Exception: {e}")
            raise e

        # Create MQTThandler
        try:
            self.mqtt_handler = MQTTHandler(config)
        except MemoryError as e:
            logger.error(f"Memory error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except RuntimeError as e:
            logger.error(f"Runtime error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except TypeError as e:
            logger.error(f"TypeError: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except ValueError as e:
            logger.error(f"ValueError error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except Exception as e:
            logger.error(f"Exception: {e}")
            self.ms_protocol.graceful_exit()
            raise e

        # Connect objects
        self.mqtt_dispatcher.define_ms_protocol(self.ms_protocol)
        self.ms_protocol.define_mqtt_handler(self.mqtt_handler)
        self.mqtt_handler.define_message_handler(self.mqtt_dispatcher)

    def connect_mqtt_broker(self) -> bool:
        logger.info(f"def connect_mqtt_broker(self) -> bool:")
        try:
            res = self.mqtt_handler.connect()
            if not res:
                self.mqtt_handler.exit_threads()
                return False
            return True
        except Exception as e:
            logger.error(f"Cannot connect to MQTT broker: {e}")
            return False

    def subscribe(self) -> bool:
        logger.info(f"def subscribe(self) -> bool:")
        try:
            res = self.ms_protocol.subscribe(self.ms_protocol.construct_rsp_topic())
            if not res:
                logger.warning(f"MQTTMS: Not successful subscription: {e}.")
                return False
            return True
        except Exception as e:
                logger.warning(f"MQTTMS: Not successful subscription: {e}.")
                return False

    def graceful_exit(self) -> None:
        logger.info(f"def graceful_exit(self) -> None:")
        if self.ms_protocol:
            self.ms_protocol.graceful_exit()
        if self.mqtt_handler:
            self.mqtt_handler.disconnect_and_exit()
