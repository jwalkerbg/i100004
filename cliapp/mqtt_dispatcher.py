# mqtt_dispatcher.py

import time
import json
import threading
import queue
import struct
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler
from cliapp.ms_protocol import CommandProtocol

class MQTTDispatcher:
    def __init__(self, protocol:CommandProtocol = None):
        self.ms_protocol = protocol


    def define_ms_protocol(self, protocol:CommandProtocol = None):
        self.ms_protocol = protocol

    def handle_message(self,message):
        topic, payload = message
        logger.info(f"handle_device_message: -t '{topic}' -m '{payload}'")

        jp = json.loads(payload)

        jdata = jp.get('data', {})

        logger.info(f"jdata = {jdata}")
        format_string = '<hIIIHBBB'
        bdata = bytes.fromhex(jdata)

        unpacked_data = struct.unpack(format_string, bdata)

        logger.info(f"unpacked_data = {unpacked_data}")

        packed_data = struct.pack(format_string, *unpacked_data)
        hex_string = packed_data.hex()
        logger.info(f"Packed data as hex string: {hex_string}")
