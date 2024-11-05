# mqttms/core.py

from typing import Dict
import json
from jsonschema import validate, ValidationError
from mqttms.mqtt_handler import MQTTHandler
from mqttms.ms_protocol import MSProtocol
from mqttms.logger_module import logger
from mqttms.mqtt_dispatcher import MQTTDispatcher
from mqttms.conferror import ConfigurationError

class MQTTms:

    CONFIG_SCHEMA = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "mqttms": {
                "type": "object",
                "properties": {
                    "mqtt": {
                        "type": "object",
                        "properties": {
                            "host": {"type": "string"},
                            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
                            "username": {"type": "string"},
                            "password": {"type": "string"},
                            "client_id": {"type": "string"},
                            "timeout": {"type": "number"},
                            "long_payload": {"type": "integer", "minimum": 10, "maximum": 32768}
                        },
                        "required": ["host", "port"]
                    },
                    "ms": {
                        "type": "object",
                        "properties": {
                            "client_mac": {"type": "string"},
                            "server_mac": {"type": "string"},
                            "cmd_topic": {"type": "string"},
                            "rsp_topic": {"type": "string"},
                            "timeout": {"type": "number"}
                        },
                        "required": ["client_mac", "server_mac", "cmd_topic", "rsp_topic", "timeout"]
                    }
                },
                "required": ["mqtt", "ms"],
                "additionalProperties": False
            },
            "logging": {
                "type": "object",
                "properties": {
                    "verbose": { "type": "boolean" }
                },
                "required": ["verbose"],
                "additionalProperties": False
            }
        },
        "required": ["mqttms", "logging"],
        "additionalProperties": False
    }

    def __init__(self, config:Dict, logging:Dict, mqtt_dispatcher: MQTTDispatcher=None):
        '''
        Initialize objects
        '''

        self.config = {
            "logging" : {},
            "mqttms" : {}
        }

        self.config['mqttms'].update(config)
        self.config['logging'].update(logging)
        # validate configuration
        try:
            validate(instance=self.config, schema=self.CONFIG_SCHEMA)
        except ValidationError as e:
            logger.error(f"MQTTMS: Invalid confguration. Reason: {e}")
            raise ConfigurationError

        if self.config['logging'].get('verbose', False):
            logger.info(f"MQTTms Configuration: {self.config}")

        # Create MQTTDispatcher object
        try:
            self.mqtt_dispatcher = None
            if mqtt_dispatcher == None:
                self.mqtt_dispatcher = MQTTDispatcher(config=self.config)
            else:
                self.mqtt_dispatcher = mqtt_dispatcher
        except MemoryError as e:
            raise e

        # Create MSProtocol object
        try:
            self.ms_protocol = MSProtocol(config=self.config)
        except MemoryError as e:
            logger.error(f"MQTTMS: Memory error: {e}")
            raise e
        except RuntimeError as e:
            logger.error(f"MQTTMS: Runtime error: {e}")
            raise e
        except TypeError as e:
            logger.error(f"MQTTMS: TypeError: {e}")
            raise e
        except ValueError as e:
            logger.error(f"MQTTMS: ValueError: {e}")
            raise e
        except Exception as e:
            logger.error(f"MQTTMS: Exception: {e}")
            raise e

        # Create MQTThandler
        try:
            self.mqtt_handler = MQTTHandler(config=self.config)
        except MemoryError as e:
            logger.error(f"MQTTMS: Memory error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except RuntimeError as e:
            logger.error(f"MQTTMS: Runtime error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except TypeError as e:
            logger.error(f"MQTTMS: TypeError: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except ValueError as e:
            logger.error(f"MQTTMS: ValueError error: {e}")
            self.ms_protocol.graceful_exit()
            raise e
        except Exception as e:
            logger.error(f"MQTTMS: Exception: {e}")
            self.ms_protocol.graceful_exit()
            raise e

        # Connect objects
        self.mqtt_dispatcher.define_ms_protocol(self.ms_protocol)
        self.ms_protocol.define_mqtt_handler(self.mqtt_handler)
        self.mqtt_handler.define_message_handler(self.mqtt_dispatcher)

    def connect_mqtt_broker(self) -> bool:
        try:
            res = self.mqtt_handler.connect()
            if not res:
                self.mqtt_handler.exit_threads()
                return False
            return True
        except Exception as e:
            logger.error(f"MQTTMS: Cannot connect to MQTT broker: {e}")
            return False

    def subscribe(self, topic:str = None) -> bool:
        try:
            if topic is None:
                res = self.ms_protocol.subscribe()
            else:
                res = self._subscribe(topic)
            if not res:
                logger.warning(f"MQTTMS: Not successful subscription: {e}.")
                return False
            return True
        except Exception as e:
                logger.warning(f"MQTTMS: Not successful subscription: {e}.")
                return False

    def _subscribe(self, topic: str, timeout: float = 5.0) -> bool:
        self.mqtt_handler.subscribe(topic)

        if self.mqtt_handler.subscription_estabilished.wait(timeout=self.config['mqttms']['mqtt'].get('timeout', timeout)):
            return True
        else:
            return False

    def publish(self, topic: str, payload:str) -> None:
        self.mqtt_handler.publish_message(topic,payload)

    def graceful_exit(self) -> None:
        if self.ms_protocol:
            self.ms_protocol.graceful_exit()
        if self.mqtt_handler:
            self.mqtt_handler.disconnect_and_exit()
