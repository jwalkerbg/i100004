import threading
import re
import json
import jsonschema
from jsonschema import validate, ValidationError, Draft7Validator, FormatChecker
from typing import Dict
import queue
import random

from mqttms.mqtt_handler import MQTTHandler
from mqttms.logger_module import logger

class MSProtocol:
    def __init__(self, config:Dict):
        """
        Initialize the command protocol with MQTTHandler and device MAC addresses.

        Parameters:
        - mqtt_handler: An instance of the existing MQTTHandler class that manages the connection.
        - master_mac: MAC address of the master device (this device).
        - slave_mac: MAC address of the slave device (the server device).
        - command_timeout: Timeout in seconds to wait for a response from the slave.
        """
        self.mqtt_handler = None
        self.config = config

        self.valid_formats = ["BINARY", "ASCIIHEX", "ASCII", "JSON"]
        self.mapped_formats = ["base64", "asciihex", "ascii", "object"]
        self.RESPONSE_SCHEMA = {
            "type": "object",
            "properties": {
                "cid": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 999
                },
                "server": {
                    "type": "string",
                    "minLength": 12,
                    "maxLength": 12,
                    "pattern": "^[0-9a-fA-F]+$"
                },
                "response": {
                    "type": "string",
                    "minLength": 2,
                    "maxLength": 2,
                    "pattern": "^[A-Z]+$"
                },
                "dataType": {
                    "type": "string",
                    "enum": ["base64", "asciihex", "ascii", "object"]
                },
                "data": {}
            },
            "required": ["cid", "server", "response", "dataType", "data"],
            "additionalProperties": False,
            "if": {
                    "properties": {
                    "dataType": { "const": "asciihex" }
                }
            },
            "then": {
                "properties": {
                    "data": {
                        "type": "string",
                        "pattern": "^[0-9a-fA-F]*$",
                        "minLength": 0
                    }
                }
            },
            "else": {
                "if": {
                    "properties": {
                        "dataType": { "const": "ascii" }
                    }
                },
                "then": {
                    "properties": {
                        "data": {
                            "type": "string",
                            "pattern": "^[\\x20-\\x7E]*$",
                            "minLength": 0
                        }
                    }
                },
                "else": {
                    "if": {
                        "properties": {
                            "dataType": { "const": "base64" }
                        }
                    },
                    "then": {
                        "properties": {
                            "data": {
                                "type": "string",
                                "pattern": "^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$",
                                "minLength": 0
                            }
                        }
                    },
                    "else": {
                        "if": {
                            "properties": {
                                "dataType": { "const": "object" }
                            }
                        },
                        "then": {
                            "properties": {
                                "data": {
                                    "type": "object",
                                    "additionalProperties": True
                                }
                            }
                        }
                    }
                }
            }
        }

        # quque for commands
        self.queue_cmd = queue.Queue()
        # queue for responses
        self.queue_res = queue.Queue()

        # Synchronization for waiting for responses
        self.response_received = threading.Event()

        # To store the response
        self.response = None

        self.command_thread = None
        self.command_thread = threading.Thread(target=self.command_thread_runner, args=(self.queue_cmd,self.queue_res))
        self.command_thread.start()

    def command_thread_runner(self, qcmd, qres):
        logger.info(f"MS command thread started")

        while True:
            # waiting for a command
            message = self.queue_cmd.get()
            # check for exit
            if message == None:
                break

            # sending message for publishing
            topic = self.construct_cmd_topic()
            payload = self.add_tracking_information(payload=message)
            self.mqtt_handler.publish_message(topic, payload)
            try:
                jpayload = json.loads(payload)
                cid = jpayload.get('cid', 0)
            except json.JSONDecodeError as e:
                cid = 0

            # wait for response
            try:
                topic, payload = self.queue_res.get(block=True,timeout=self.config['mqttms']['ms'].get('timeout', 5))
            except queue.Empty:
                # create timeout answer here
                self.construct_not_ok_response(cid,"TM")
                logger.info(f"MS Timeout")
                self.response_received.set()
                continue

            # convert payload to json object
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as e:
                self.construct_not_ok_response(cid,"BD")
                self.response_received.set()
                continue

            payload = self.add_dataType(topic, payload)
            if payload == None:
                # construct BD response
                self.construct_not_ok_response(cid,"BD")
                self.response_received.set()
                continue

            if not self.validate_json(data=payload):
                # construct BD response
                self.construct_not_ok_response(cid,"BD")
                self.response_received.set()
                continue

            # flag that response has received or generated timeout response
            self.response = payload
            self.response_received.set()

        logger.info(f"MS command thread exited")

    def add_tracking_information(self,payload):
        payload = re.sub('({)', r'\1' + f'"client":"{self.config["mqttms"]["ms"].get("client_mac","_")}",', payload)
        payload = re.sub('({)', r'\1' + f'"cid":{self.generate_random_cid()},', payload)
        return payload

    def construct_not_ok_response(self, cid: int, response: str):
        payload = {}
        payload["server"] = f'{self.config["mqttms"]["ms"].get("server_mac", "_")}'
        payload["cid"] = cid
        payload["response"] = response
        payload["data"] = ""
        payload["dataType"] = "asciihex"
        self.response = payload

    def subscribe(self, timeout: float = 5.0):
        topic = self.construct_rsp_topic()
        self.mqtt_handler.subscribe(topic)

        if self.mqtt_handler.subscription_estabilished.wait(timeout=self.config['mqttms']['mqtt'].get('timeout', timeout)):
            return True
        else:
            return False

    def define_mqtt_handler(self,handler:MQTTHandler =None):
        self.mqtt_handler = handler

    def construct_cmd_topic(self, format='ASCIIHEX'):
        topic = self.config['mqttms']['ms']['cmd_topic'].replace('server_mac',self.config['mqttms']['ms']['server_mac'])
        topic = topic.replace('format',format)
        return topic

    def construct_rsp_topic(self,format='ASCIIHEX'):
        topic = self.config['mqttms']['ms']['rsp_topic'].replace('client_mac',self.config['mqttms']['ms']['client_mac'])
        topic = topic.replace('format',format)
        return topic

    def put_command(self, payload):
        self.queue_cmd.put(payload)

    def put_response(self,message):
        self.queue_res.put(message)

    def get_response(self):
        self.response_received.wait()
        return self.response

    def generate_random_cid(self) -> int:
        return random.randint(0, 999)  # Generate a random, payload: dict

    def add_dataType(self, topic: str, payload: dict) -> None:
        # Split the topic by '/'
        topic_parts = topic.split('/')

        # Ensure the topic has at least 4 elements and the last element is the format
        if len(topic_parts) < 4:
            return None

        # Extract the format (last element of the topic)
        format_part = topic_parts[-1]

        # Check if the format part is in the array of valid formats
        if format_part in self.valid_formats:
            # Find the index in valid_formats and map to mapped_formats
            # Note that valid_formats and mapped_formats are parallel arrays and are under control.
            index = self.valid_formats.index(format_part)
            payload["dataType"] = self.mapped_formats[index]
            return payload
        else:
            return None

    def validate_json(self, data) -> bool:
        validator = Draft7Validator(self.RESPONSE_SCHEMA)
        try:
            validator.validate(instance=data)
            logger.info("JSON validation : OK")
            return True
        except jsonschema.exceptions.ValidationError as err:
            logger.info(f"JSON data is invalid: {err.message}")
            return False

    def graceful_exit(self) -> None:
        self.put_command(None)
        self.command_thread.join()
        logger.info(f"MS: graceful exited")
