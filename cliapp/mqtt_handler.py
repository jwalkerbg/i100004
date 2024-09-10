import json
import paho.mqtt.client as mqtt

class MQTTHandler:
    def __init__(self, config):
        self.config = config
        self.client = mqtt.Client()

        # Set username and password if provided
        if self.config['mqtt']['username'] and self.config['mqtt']['password']:
            self.client.username_pw_set(self.config['mqtt']['username'], self.config['mqtt']['password'])

        # Assign the default handlers
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

    def connect(self):
        """Connect to the MQTT broker."""
        host = self.config['mqtt']['host']
        port = self.config['mqtt']['port']
        print(f"Connecting to MQTT broker at {host}:{port}...")
        self.client.connect(host, port, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        """Callback when the client connects to the broker."""
        if rc == 0:
            print("Connected to MQTT broker.")
            subscribe_topic = self.config['mqtt']['topics']['subscribe_topic']
            self.client.subscribe(subscribe_topic)
            print(f"Subscribed to topic: {subscribe_topic}")
        else:
            print(f"Failed to connect, return code {rc}")

    def publish_message(self, topic, message):
        """Publish a message to the MQTT topic."""
        self.client.publish(topic, message)
        print(f"Published message to {topic}: {message}")

    def on_message(self, client, userdata, msg):
        """Callback when a message is received."""
        print(f"Received message from {msg.topic}: {msg.payload.decode()}")

    def define_message_handler(self, handler):
        """Define a custom message handler."""
        self.client.on_message = handler
