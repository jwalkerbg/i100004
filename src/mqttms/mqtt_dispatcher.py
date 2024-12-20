# mqtt_dispatcher.py

import re
from typing import Dict, Tuple, Any
from abc import ABC, abstractmethod
from mqttms.abstract_dispatcher import AbstractMQTTDispatcher
from mqttms.ms_protocol import MSProtocol
from mqttms.logger_module import logger

class MQTTDispatcher(AbstractMQTTDispatcher):
    def __init__(self, config: Dict, protocol:MSProtocol = None):
        super().__init__(config)
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
        pattern = fr"^@/{self.config['mqttms']['ms'].get('client_mac', '_')}/RSP/(ASCII|ASCIIHEX|JSON|BINARY)$"

        # Check if the given topic matches the regex pattern
        return bool(re.match(pattern, topic))

    def handle_message(self, message: Tuple[str, str]) -> bool:
        """
        Handles an incoming MQTT message, processes the topic, and dispatches based on matching protocols.

        Args:
            message (Tuple[str, str]): A tuple containing the topic (str) and payload (str).

        Returns:
            Return True if the message is handled
        """

        if not super().handle_message(message):

            if self.match_mqtt_topic_for_ms(message[0]):
                logger.info(f"handle_message: -t '{message[0]}' -m '{message[1]}'")
                self.ms_protocol.put_response(message)
                return True
            # here more dispatcher options may be added if necessary

        return False
