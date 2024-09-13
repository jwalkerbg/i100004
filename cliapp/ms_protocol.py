import time
import threading
import json
from jsonschema import validate, ValidationError
import queue
import struct
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler

class CommandProtocol:
    def __init__(self, master_mac: str, slave_mac: str, command_timeout: int = 10):
        """
        Initialize the command protocol with MQTTHandler and device MAC addresses.

        Parameters:
        - mqtt_handler: An instance of the existing MQTTHandler class that manages the connection.
        - master_mac: MAC address of the master device (this device).
        - slave_mac: MAC address of the slave device (the target device).
        - command_timeout: Timeout in seconds to wait for a response from the slave.
        """
        self.mqtt_handler = None
        self.master_mac = master_mac
        self.slave_mac = slave_mac
        self.command_timeout = command_timeout

        # quque for commands
        self.queue_cmd = queue.Queue()
        # queue for responses
        self.queue_res = queue.Queue()

        # Synchronization for waiting for responses
        self.response_received = threading.Event()

        # To store the response
        self.response = None

        data_formats = { 'binary':'BINARY', 'asciihex':'ASCIIHEX', 'ascii':'ASCII', 'json':'JSON' }

    def command_thread(self):
        logger.info(f"MS command thread started")

        while True:
            # waiting for a command
            message = self.queue_cmd.get()
            # check for exit
            if message == (None, None):
                break

            # sending message for publishing
            topic, payload = message
            self.mqtt_handler.publish_message(topic, payload)

            # wait for response
            try:
                self.response = self.queue_res.get(block=True,timeout=self.command_timeout)
            except queue.Empty:
                # create timeout answer here
                topic = f"@/{self.master_mac}/RSP/ASCIIHEX"
                payload = '{"server":"F412FACEF2E8", "cid":123,"response":"TM","data":""}'
                self.response = (topic, message)

            # wait for previous response to be received and handled
            self.response_received.set()

        logger.info(f"MS command thread exited")

    def define_mqtt_handler(self,handler:MQTTHandler =None):
        self.mqtt_handler = handler
