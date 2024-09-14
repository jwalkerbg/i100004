import time
import threading
import json
from jsonschema import validate, ValidationError
import queue
import struct
import random
from cliapp.logger_module import logger, string_handler
from cliapp.mqtt_handler import MQTTHandler

class CommandProtocol:
    def __init__(self, config):
        """
        Initialize the command protocol with MQTTHandler and device MAC addresses.

        Parameters:
        - mqtt_handler: An instance of the existing MQTTHandler class that manages the connection.
        - master_mac: MAC address of the master device (this device).
        - slave_mac: MAC address of the slave device (the target device).
        - command_timeout: Timeout in seconds to wait for a response from the slave.
        """
        self.mqtt_handler = None
        self.config = config

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

        data_formats = { 'binary':'BINARY', 'asciihex':'ASCIIHEX', 'ascii':'ASCII', 'json':'JSON' }

    def command_thread_runner(self, qcmd, qres):
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
            logger.info(f"MS ----------------> command sent")

            # wait for response
            try:
                self.response = self.queue_res.get(block=True,timeout=self.config['ms'].get('timeout', 5))
                logger.info(f"MS -----------------> responce received")
            except queue.Empty:
                # create timeout answer here
                topic = self.construct_rsp_topic()
                payload = f'{{"server":"{self.config["ms"].get("server_mac", "_")}","cid":123,"response":"TM","data":""}}'
                self.response = (topic, payload)
                logger.info(f"MS Timeout")
            # flag that response has received or generated timeout response
            self.response_received.set()

        logger.info(f"MS command thread exited")

    def define_mqtt_handler(self,handler:MQTTHandler =None):
        self.mqtt_handler = handler

        #"cmd_topic": "@/server_mac/CMD/format",
       # "rsp_topic": "@/client_mac/RSP/format",

    def construct_cmd_topic(self, format='ASCIIHEX'):
        topic = self.config['ms']['cmd_topic'].replace('server_mac',self.config['ms']['server_mac'])
        topic = topic.replace('format',format)
        return topic

    def construct_rsp_topic(self,format='ASCIIHEX'):
        topic = self.config['ms']['rsp_topic'].replace('client_mac',self.config['ms']['client_mac'])
        topic = topic.replace('format',format)
        return topic

    def put_command(self,topic, payload):
        self.queue_cmd.put((topic,payload))

    def put_response(self,topic,payload):
        self.queue_res.put((topic,payload))

    def get_response(self):
        self.response_received.wait()
        return self.response

    def generate_random_id_string(self) -> str:
        """
        Generate a string in the format 'id_XXX' where XXX is a random number from 0 to 999.
        The number is zero-padded to ensure it has three digits.

        Returns:
        - str: A string in the format 'id_XXX' with a random three-digit number.
        """
        number = random.randint(0, 999)  # Generate a random number between 0 and 999
        return f"id_{number:03d}"
