import json
import threading
import queue
import paho.mqtt.client as mqtt
from cliapp.logger_module import logger, string_handler

class MQTTHandler:
    def __init__(self, config):
        self.config = config
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.config['mqtt']['client_id'],protocol=mqtt.MQTTv5)

        # Set username and password if provided
        if self.config['mqtt']['username'] and self.config['mqtt']['password']:
            self.client.username_pw_set(self.config['mqtt']['username'], self.config['mqtt']['password'])

        self.connection_established = threading.Event()

        self.pending_subscriptions = { }
        self.subscription_estabilished = threading.Event()

        # queue for messages to be published
        self.queue_pub = queue.Queue()
        # queue for received messages
        self.queue_rec = queue.Queue()

        # Assign the default handlers
        self.client.on_connect = self.on_connect
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message

        self.mqtt_publish_thread = threading.Thread(target=self.publish_mqtt_message, args=((self,self.queue_pub)))
        self.mqtt_publish_thread.start()

        self.mqtt_receive_thread = threading.Thread(target=self.receive_mqtt_message, args=((self, self.queue_rec)))
        self.mqtt_receive_thread.start()

    def connect(self):
        """Connect to the MQTT broker."""
        host = self.config['mqtt']['host']
        port = self.config['mqtt']['port']
        logger.info(f"Connecting to MQTT broker at {host}:{port}...")

        try:
            self.connection_established.clear()
            self.client.connect(host, port, 60)
            self.client.loop_start()
        except Exception as e:
            logger.info(f"MQTT Connect: Failed to connect to MQTT Broker: {e}")
            return False

        waitres = self.connection_established.wait(self.config['mqtt']['timeout'])
        if not waitres:
            logger.info("No MQTT connection was estabilished in time")
            return False
        else:
            logger.info("MQTT Connection estabilished")
            return True

    def on_connect(self, client, userdata, flags, rc, properties):
        """Callback when the client connects to the broker."""
        if rc == 0:
            logger.info("Connected to MQTT broker.")
            self.connection_established.set()
        else:
            logger.info(f"Failed to connect, return code {rc}")

    def subscribe(self,topic):
        self.subscription_estabilished.clear()
        result, mid = self.client.subscribe(topic=topic)
        self.pending_subscriptions[mid] = topic
        logger.info(f"Subscribing to topic: {topic}")

    def on_subscribe(self, client, userdata, mid, rc, properties):
        self.subscription_estabilished.set()
        topic = self.pending_subscriptions[mid]
        if topic:
            logger.info(f"MQTT Subscription to '{topic}' acknowledged")
        else:
            logger.info(f"MQTT Subscription with mid '{mid}' acknowledged but no topic found in pending subscriptions")

        logger.info(f"userdata: {userdata}")
        logger.info(f"mid: {mid}")
        logger.info(f"rc: {rc}")
        logger.info(f"properties: {properties}")

    def on_unsubscribe(self,userdata,mid,rc,properties):
        topic = self.pending_subscriptions[mid]
        if topic:
            logger.info(f"Unsibscribed from {topic}")
            self.pending_subscriptions[mid] = None
        else:
            logger.info(f"Unsubscribed from {topic} that was not in pending subscriptions")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        logger.info(f"MQTT message published")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        payload = msg.payload.decode()
        logger.info(f"MQTT Receive: topic: {msg.topic}, payload: {msg.payload.decode()}")
        self.queue_rec.put((msg.topic, payload))

    def publish_message(self, topic, message):
        """Publish a message to the MQTT topic."""
        self.client.publish(topic, message)
        logger.info(f"Published message to {topic}: {message}")

    def publish_mqtt_message(self,client,q):
        #global mqtt_verbose_log
        while True:
            message = self.queue_pub.get()  # Wait for a message to be available
            if message == (None, None):
                break  # Exit the thread if a None message is received
            topic, payload = message
            #logger.info(f"MQTT Publish: topic: {topic}, payload: {'<long payload>' if not self.config['verbose'] and len(payload) > DEFAULT_MQTT_LONG_PAYLOAD else payload}")
            logger.info(f"MQTT Publish: topic: {topic}, payload: {'<long payload>' if not self.config['verbose'] and len(payload) > 20 else payload}")
            result = self.client.publish(topic, payload,qos=0)
            result.wait_for_publish()

    def receive_mqtt_message(self,client,q):
        while True:
            topic, payload = self.queue_rec.get()  # Wait for a message to be available
            if topic is None:
                break  # Exit the thread if a None message is received

            # handle received message here (command or data rceived). Still not defined format.
            # The message shall have following format
            # odoo/<work_order>/<serial> : {"uid": "<unique id>", <Configuration, Firmware>}
            # here unique id is the same that sent by get_device message, Configuration is a JSON object
            # handle_device_message() is provided by the specific test bench
            handle_device_message(topic, payload)

    def define_message_handler(self, handler):
        """Define a custom message handler."""
        self.client.on_message = handler

def handle_device_message(topic, payload):
    logger.info(f"handle_device_message: {topic}, {payload}")