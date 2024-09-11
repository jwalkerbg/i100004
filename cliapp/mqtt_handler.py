import json
import threading
import queue
import paho.mqtt.client as mqtt
from cliapp.logger_module import logger, string_handler

class MQTTHandler:
    def __init__(self, config, message_handler=None):
        self.config = config
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.config['mqtt']['client_id'],protocol=mqtt.MQTTv5)

        self.message_handler = message_handler

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

        self.mqtt_publish_thread = None
        self.mqtt_receive_thread = None

        self.mqtt_publish_thread = threading.Thread(target=self.publish_mqtt_message, args=((self,self.queue_pub)))
        self.mqtt_publish_thread.start()

        self.mqtt_receive_thread = threading.Thread(target=self.receive_mqtt_message, args=((self, self.queue_rec)))
        self.mqtt_receive_thread.start()

    def define_message_handler(self, handler=None):
        """Define a custom message handler."""
        self.message_handler = handler

    def exit_threads(self):
        if self.mqtt_publish_thread:
            self.queue_pub.put((None,None))
            self.mqtt_publish_thread.join()
        if self.mqtt_receive_thread:
            self.queue_rec.put((None,None))
            self.mqtt_receive_thread.join()

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
        if waitres:
            logger.info("MQTT Connection estabilished")
            return True
        else:
            logger.warning("No MQTT connection was estabilished in time")
            return False

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
        logger.info(f"MQTT subscribing to topic: {topic}")

        waitres = self.subscription_estabilished.wait(self.config['mqtt']['timeout'])
        if waitres:
            logger.info(f"MQTT subscription estabilished")
            return True
        else:
            logger.warning(f"No MQTT subscription estabilished in time")
            return False

    def on_subscribe(self, client, userdata, mid, rc, properties):
        self.subscription_estabilished.set()
        topic = self.pending_subscriptions[mid]
        if topic:
            logger.info(f"MQTT subscription to '{topic}' acknowledged")
        else:
            logger.info(f"MQTT subscription with mid '{mid}' acknowledged but no topic found in pending subscriptions")

    def on_unsubscribe(self,userdata,mid,rc,properties):
        topic = self.pending_subscriptions[mid]
        if topic:
            logger.info(f"MQTT unsibscribed from {topic}")
            self.pending_subscriptions[mid] = None
        else:
            logger.info(f"MQTT unsubscribed from {topic} that was not in pending subscriptions")

    def on_publish(self, client, userdata, mid, reason_code, properties):
        logger.info(f"MQTT message published")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        payload = msg.payload.decode()
        logger.info(f"MQTT receive: -t '{msg.topic}' -m '{msg.payload.decode()}'")
        self.queue_rec.put((msg.topic, payload))

    def publish_message(self, topic, message):
        """Publish a message to the MQTT topic."""
        #self.client.publish(topic, message)
        self.queue_pub.put((topic, message))
        logger.info(f"MQTT publish: -t '{topic}' -m '{message}'")

    def publish_mqtt_message(self,client,q):
        logger.info(f"MQTT entered publishing thread")
        while True:
            message = self.queue_pub.get()  # Wait for a message to be available
            if message == (None, None):
                break  # Exit the thread if a None message is received
            topic, payload = message
            #logger.info(f"MQTT publish: -t '{topic}' -m '{'<long payload>' if not self.config['verbose'] and len(payload) > 20 else payload}'")
            result = self.client.publish(topic, payload,qos=0)
            result.wait_for_publish()
        logger.info(f"MQTT exited publishing thread")

    def receive_mqtt_message(self,client,q):
        logger.info(f"MQTT entered receiving thread")
        while True:
            message = self.queue_rec.get()  # Wait for a message to be available
            topic, payload = message
            if topic is None:
                break  # Exit the thread if a None message is received

            # handle handle_device_message
            if self.message_handler:
                self.message_handler(message)

        logger.info(f"MQTT exited receiving thread")
