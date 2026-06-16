import threading
import re
import json
from typing import Dict
import queue
import random
import jsonschema
from jsonschema import Draft7Validator

from mqttms.mqtt_handler import MQTTHandler

from mqttms.logger import get_app_logger

logger = get_app_logger(__name__)

class MSProtocol:
    def __init__(self, config:Dict, process_unsolicited_message=None):
        """
        Initialize the command protocol with MQTTHandler and device MAC addresses.

        Parameters:
        - mqtt_handler: An instance of the existing MQTTHandler class that manages the connection.
        - master_uuid: UUID of the master device (this device).
        - slave_uuid: UUID of the slave device (the server device).
        - command_timeout: Timeout in seconds to wait for a response from the slave.
        - process_unsolicited_message: A callback function to process unsolicited messages.
        """
        self.mqtt_handler = None
        self.config = config
        self.process_unsolicited_message = process_unsolicited_message

        self.valid_formats = ["BINARY", "ASCIIHEX", "ASCII", "JSON"]
        self.mapped_formats = ["base64", "asciihex", "ascii", "object"]
        self.response_schema = {
            "type": "object",
            "properties": {
                "cid": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 999
                },
                "server": {
                    "type": "string",
                    "minLength": 36,
                    "maxLength": 36,
                    "pattern": "^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-4[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
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
        self.unsolicited_schema = {
            "type": "object",
            "properties": {
                "ver": {
                    "type": "string"
                },
                "type": {
                    "type": "string"
                },
                "ts": {
                    "type": "string",
                    "format": "date-time"
                },
                "id": {
                    "type": "integer"
                },
                "severity": {
                    "type": "string"
                },
                "src": {
                    "type": "string"
                },
                "data": {
                    "type": "object"
                }
            },
            "required": ["ver", "type", "ts", "id", "severity", "src", "data"],
            "additionalProperties": False
        }

        # queue for commands
        self.queue_cmd = queue.Queue()
        # queue for responses
        self.queue_res = queue.Queue()
        # queue for unsolicited messages
        self.queue_unsolicited = queue.Queue()

        # Synchronization for waiting for responses
        self.response_received = threading.Event()

        # To store the response
        self.response = None

        self.command_thread = None
        self.command_thread = threading.Thread(target=self.command_thread_runner, args=(self.queue_cmd,self.queue_res))
        self.command_thread.start()

        self.unsolicited_thread = None
        unsolicited_thread = threading.Thread(target=self.unsolicited_thread_runner, args=(self.queue_unsolicited,))
        unsolicited_thread.start()

    def set_unsolicited_message_processor(self, callback):
        self.process_unsolicited_message = callback

    def command_thread_runner(self, qcmd, qres):
        logger.info("MS command thread started")

        while True:
            # waiting for a command
            message = self.queue_cmd.get()
            # check for exit
            if message is None:
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
                logger.info("MS Timeout")
                self.response_received.set()
                continue

            # convert payload to json object
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as e:
                self.construct_not_ok_response(cid,"BD")
                self.response_received.set()
                continue

            payload = self.add_data_type(topic, payload)
            if payload is None:
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

        logger.info("MS command thread exited")

    def unsolicited_thread_runner(self, qunsolicited):
        logger.info("MS unsolicited thread started")

        while True:
            # waiting for an unsolicited message
            message = self.queue_unsolicited.get()
            # check for exit
            if message is None:
                break

            topic, payload = message

            try:
                jpayload = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.warning("Received invalid JSON in unsolicited message: %s", e)
                continue

            validator = Draft7Validator(self.unsolicited_schema)
            try:
                validator.validate(instance=jpayload)
                logger.info("Received valid unsolicited message: %s", jpayload)
                # Here you can add code to process the valid unsolicited message as needed
                # here we can call a callback or put the message in another queue for processing
                if self.process_unsolicited_message:
                    self.process_unsolicited_message(jpayload)
            except jsonschema.exceptions.ValidationError as err:
                logger.warning("Received invalid unsolicited message: %s", err.message)

        logger.info("MS unsolicited thread exited")

    def add_tracking_information(self,payload):
        payload = re.sub('({)', r'\1' + f'"client":"{self.config["mqttms"]["ms"].get("client_uuid","_")}",', payload)
        payload = re.sub('({)', r'\1' + f'"cid":{self.generate_random_cid()},', payload)
        return payload

    def construct_not_ok_response(self, cid: int, response: str):
        payload = {}
        payload["server"] = f'{self.config["mqttms"]["ms"].get("server_uuid", "_")}'
        payload["cid"] = cid
        payload["response"] = response
        payload["data"] = ""
        payload["dataType"] = "asciihex"
        self.response = payload

    def subscribe_all(self, timeout: float = 5.0):
        for topic in self.config['mqttms']['ms'].get('subs_topics', []):
            logger.info("Subscribing to topic: %s with format: %s", topic["topic"], topic["format"])
            self.subscribe(topic["topic"], topic["format"], timeout)

    def subscribe(self, topic: str, format: str, timeout: float = 5.0):
        t = topic.replace('server_uuid',self.config['mqttms']['ms']['server_uuid'])
        t = t.replace('format',format)
        self.mqtt_handler.subscribe(t)

        return bool(self.mqtt_handler.subscription_established.wait(timeout=self.config['mqttms']['mqtt'].get('timeout', timeout)))

    def define_mqtt_handler(self,handler:MQTTHandler =None):
        self.mqtt_handler = handler

    def construct_cmd_topic(self, format='ASCIIHEX'):
        topic = self.config['mqttms']['ms']['cmd_topic'].replace('server_uuid',self.config['mqttms']['ms']['server_uuid'])
        topic = topic.replace('format',format)
        return topic

    def put_command(self, payload):
        self.queue_cmd.put(payload)

    def put_response(self,message):
        self.queue_res.put(message)

    def get_response(self):
        self.response_received.wait()
        return self.response

    def put_unsolicited(self, message):
        self.queue_unsolicited.put(message)

    def get_unsolicited(self):
        return self.queue_unsolicited.get()

    def generate_random_cid(self) -> int:
        return random.randint(0, 999)  # Generate a random, payload: dict

    def add_data_type(self, topic: str, payload: dict) -> None:
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
        return None

    def validate_json(self, data) -> bool:
        validator = Draft7Validator(self.response_schema)
        try:
            validator.validate(instance=data)
            logger.info("JSON validation : OK")
            return True
        except jsonschema.exceptions.ValidationError as err:
            logger.info("JSON data is invalid: %s", err.message)
            return False

    def graceful_exit(self) -> None:
        self.put_command(None)
        self.command_thread.join()
        logger.info("MS: graceful exited")
