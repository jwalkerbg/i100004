import time
import threading
import json
from jsonschema import validate, ValidationError
import queue
import struct
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler

def handle_message(message):
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