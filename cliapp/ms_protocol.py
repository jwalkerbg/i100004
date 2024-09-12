import time
import threading
import json
from jsonschema import validate, ValidationError
import queue
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler

def handle_message(message):
    topic, payload = message
    logger.info(f"handle_device_message: -t '{topic}' -m '{payload}'")
