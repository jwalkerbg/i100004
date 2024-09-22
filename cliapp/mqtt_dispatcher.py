# mqtt_dispatcher.py

import time
import json
import threading
import queue
import struct
import re
from typing import Dict, Tuple, Any
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler
from cliapp.ms_protocol import MSProtocol

class MQTTDispatcher:
    def __init__(self, config: Dict, protocol:MSProtocol = None):
        self.config = config
        self.ms_protocol = protocol

    def define_ms_protocol(self, protocol:MSProtocol = None) -> None:
        self.ms_protocol = protocol

    def match_mqtt_topic_for_ms(self, topic: str) -> bool:
        """
        Matches an MQTT topic with the following format:
        @/<mac_address>/RSP/<format>

        where mac_address is a 12-digit hexadecimal string and format is one of:
        'ASCII', 'ASCIIHEX', 'JSON', 'BINARY'.

        Args:
            mac_address (str): A 12-character hexadecimal MAC address.
            topic (str): The MQTT topic to validate.

        Returns:
            bool: True if the topic matches the expected format, False otherwise.
        """
        # Define the regex pattern for the MQTT topic, with valid formats embedded
        pattern = fr"^@/{self.config['ms'].get('client_mac', '_')}/RSP/(ASCII|ASCIIHEX|JSON|BINARY)$"

        # Check if the given topic matches the regex pattern
        return bool(re.match(pattern, topic))

    def handle_message(self, message: Tuple[str, str]) -> None:
        """
        Handles an incoming MQTT message, processes the topic, and dispatches based on matching protocols.

        Args:
            message (Tuple[str, str]): A tuple containing the topic (str) and payload (str).

        Returns:
            None: This function does not return anything.
        """
        topic, payload = message
        logger.info(f"handle_device_message: -t '{topic}' -m '{payload}'")

        if self.match_mqtt_topic_for_ms(topic):
            self.ms_protocol.put_response(topic, payload)
            return
        # here more dispatcher options may be added if necessary
