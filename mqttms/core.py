# mqttms/core.py

from typing import Dict
from mqttms.logger_module import logger, string_handler
from mqttms.mqtt_handler import MQTTHandler
from mqttms.ms_protocol import MSProtocol

def graceful_exit(protocol: MSProtocol,mqtthandler: MQTTHandler):
        if protocol:
            protocol.graceful_exit()
        if mqtthandler:
            mqtthandler.disconnect_and_exit()
