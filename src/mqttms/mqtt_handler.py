import time
import json
import threading
import queue
from typing import Dict
import paho.mqtt.client as mqtt
from mqttms.abstract_dispatcher import AbstractMQTTDispatcher
from mqttms.logger_module import logger

class MQTTHandler:
    def __init__(self, config:Dict, message_handler:AbstractMQTTDispatcher=None):
        self.config = config
        self.configmqttms = config['mqttms']    # shortcut pointer
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,client_id=self.configmqttms['mqtt']['client_id'],protocol=mqtt.MQTTv5)

        self.message_handler = None
        self.define_message_handler(handler=message_handler)

        # Set username and password if provided
        if self.configmqttms['mqtt']['username'] and self.configmqttms['mqtt']['password']:
            self.client.username_pw_set(self.configmqttms['mqtt']['username'], self.configmqttms['mqtt']['password'])

        self.connection_established = threading.Event()

        self.pending_messages = { }

        self.pending_subscriptions = { }
        self.subscription_estabilished = threading.Event()
        self.subscriptions_terminated = threading.Event()

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

    def define_message_handler(self, handler:AbstractMQTTDispatcher=None) -> None:
        if hasattr(handler, 'handle_message') and callable(getattr(handler, 'handle_message')):
            self.message_handler = handler
        else:
            self.message_handler = None

    def exit_threads(self) -> None:
        if self.mqtt_publish_thread:
            # Signal the publish thread to stop by putting (None, None) into the publish queue
            self.queue_pub.put((None, None))
            # Wait for the publish thread to finish its execution
            self.mqtt_publish_thread.join()

        if self.mqtt_receive_thread:
            # Signal the receive thread to stop by putting (None, None) into the receive queue
            self.queue_rec.put((None, None))
            # Wait for the receive thread to finish its execution
            self.mqtt_receive_thread.join()

    def connect(self) -> bool:
        host = self.configmqttms['mqtt']['host']
        port = self.configmqttms['mqtt']['port']
        logger.info(f"MQTT connecting to MQTT broker at {host}:{port}...")

        try:
            # Clear the event to indicate that the connection is not established yet.
            self.connection_established.clear()

            # Attempt to connect to the MQTT broker.
            self.client.connect(host, port, 60)

            # Start the network loop in the background.
            self.client.loop_start()
        except Exception as e:
            # Log any connection failure.
            logger.info(f"MQTT Connect: Failed to connect to MQTT Broker: {e}")
            return False

        # Wait for the connection to be established (set by the on_connect() callback) within the timeout period.
        waitres = self.connection_established.wait(self.configmqttms['mqtt']['timeout'])

        if waitres:
            # Connection was successfully established within the timeout.
            logger.info("MQTT connection established")
            return True
        else:
            # Connection was not established within the timeout.
            logger.warning("No MQTT connection was established in time")
            return False

    def on_connect(self, client: mqtt.Client, userdata: object, flags: dict, rc: int, properties: dict = None) -> None:
        if rc == 0:
            # Connection was successful
            logger.info("MQTT connected to MQTT broker.")

            # Set the event to signal the connect() method that the connection is established.
            self.connection_established.set()
        else:
            # Connection failed with a return code (rc != 0)
            logger.info(f"MQTT failed to connect, return code {rc}")

    def disconnect_and_exit(self) -> None:
        logger.info("MQTT initiating clean shutdown...")

        # Step 1: Unsubscribe all topics
        self.subscriptions_terminated.clear()
        self.client.unsubscribe("#")
        waitres = self.subscriptions_terminated.wait(self.configmqttms['mqtt']['timeout'])
        if waitres:
            logger.info(f"MQTT unsubscribed successfully")
        else:
            logger.error(f"MQTT unsubscribing did finished in time")

        # Step 2: Exit the publishing and receiving threads
        self.exit_threads()  # Signal the threads to stop and wait for them to finish

        # Step 3: Disconnect from the MQTT broker
        try:
            self.client.disconnect()  # This will trigger the on_disconnect() callback
            logger.info("MQTT disconnected from MQTT broker.")
        except Exception as e:
            # Log any errors that occur during the disconnection process
            logger.error(f"MQTT error while disconnecting from the broker: {e}")

        logger.info("MQTT clean shutdown complete.")

    def on_disconnect(self, client: mqtt.Client, userdata: object, rc: int) -> None:
        # If the return code (rc) is 0, the disconnection was intentional
        if rc == 0:
            logger.info("Disconnected from MQTT broker successfully.")
        else:
            # If rc != 0, the disconnection was unintentional
            logger.warning(f"Unexpected disconnection from MQTT broker. Reason code: {rc}")

            # Attempt to reconnect to the broker
            try:
                client.reconnect()
                logger.info("Reconnected to MQTT broker.")
            except Exception as e:
                # Log the failure to reconnect
                logger.error(f"Failed to reconnect: {e}")

    def subscribe(self, topic: str) -> bool:
        # Clear the subscription event to signal that no acknowledgment has been received yet
        self.subscription_estabilished.clear()

        # Attempt to subscribe to the specified topic
        result, mid = self.client.subscribe(topic=topic)

        # Store the subscription message ID (mid) and associate it with the topic
        self.pending_subscriptions[mid] = topic

        # Log the subscription request
        logger.info(f"MQTT subscribing to topic: {topic}")

        # Wait for the subscription acknowledgment from the broker, with a timeout
        waitres = self.subscription_estabilished.wait(self.configmqttms['mqtt']['timeout'])

        if waitres:
            # If the acknowledgment was received in time, log success and return True
            logger.info(f"MQTT subscription established")
            return True
        else:
            # If the acknowledgment was not received in time, log a warning and return False
            logger.warning(f"No MQTT subscription established in time")
            return False

    def on_subscribe(self, client: mqtt.Client, userdata: object, mid: int, rc: int, properties: dict = None) -> None:
        # Signal that the subscription acknowledgment has been received
        self.subscription_estabilished.set()

        # Retrieve the topic associated with the message ID (mid)
        topic = self.pending_subscriptions.pop(mid, None)

        # Log the subscription acknowledgment along with the topic, if available
        if topic:
            logger.info(f"MQTT subscription to '{topic}' acknowledged")
        else:
            logger.info(f"MQTT subscription with mid '{mid}' acknowledged but no topic found in pending subscriptions")

    def on_unsubscribe(self, client: mqtt.Client, userdata: object, mid: int, reason_code_list: list, properties: dict = None) -> None:
        # Signal that the unsubscribe request has been acknowledged by the broker
        self.subscriptions_terminated.set()

        # Log the acknowledgment of the unsubscribe request for the given message ID (mid)
        logger.info(f"MQTT unsubscribe acknowledgment for mid '{mid}' received")

    def on_publish(self, client: mqtt.Client, userdata: object, mid: int, reason_code: int, properties: dict = None) -> None:
        # Log successful message publication with its message ID and reason code
        if reason_code == 0:
            logger.info(f"MQTT message with mid '{mid}' successfully published.")
        else:
            logger.warning(f"MQTT failed to publish MQTT message with mid '{mid}', reason code: {reason_code}")

        # Optionally, remove the message ID from a tracking dictionary of pending messages (if applicable)
        if mid in self.pending_messages:
            self.pending_messages.pop(mid, None)

    def publish_message(self, topic: str, payload: str) -> None:
        # Place the topic and payload into the publishing queue
        self.queue_pub.put((topic, payload))

        # Log the message being queued, optionally truncating the payload if verbosity is off and the payload is long
        logger.info(f"MQTT publish: -t '{topic}' -m '{'<long payload>' if not self.config['logging']['verbose'] and len(payload) > self.configmqttms['mqtt'].get('long_payload', 0) else payload}'")

    def publish_mqtt_message(self, client: mqtt.Client, q: queue.Queue) -> None:
        logger.info(f"MQTT entered publishing thread")

        while True:
            # Wait for the next message in the publishing queue
            message = self.queue_pub.get()

            # Exit the thread if a signal (None, None) is received
            if message == (None, None):
                break

            # Unpack the topic and payload from the message tuple
            topic, payload = message

            # Attempt to publish the message to the MQTT broker
            result = self.client.publish(topic, payload, qos=0)

            # Check if the message was successfully queued for publishing
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                mid = result.mid  # Get the message ID for tracking
                self.pending_messages[mid] = {'topic': topic, 'payload': payload}  # Track the message
            else:
                logger.warning(f"MQTT failed to publish message to topic '{topic}', return code: {result.rc}")

            # Wait for the message to be fully published (if QoS 1 or 2)
            result.wait_for_publish()

        logger.info(f"MQTT exited publishing thread")

    def on_message(self, client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
        # Decode the payload
        payload = message.payload.decode()

        # Log the message. If verbose mode is off and the payload is long, log a placeholder.
        logger.info(
            f"MQTT receive: -t '{message.topic}' -m '{'<long payload>' if not self.config['logging']['verbose'] and len(payload) > self.configmqttms['mqtt'].get('long_payload', 0) else payload}'"
        )

        # Place the topic and payload into the receiving queue
        self.queue_rec.put((message.topic, payload))

    def receive_mqtt_message(self, client: mqtt.Client, q: queue.Queue) -> None:
        logger.info(f"MQTT entered receiving thread")

        while True:
            # Wait for the next message in the queue
            message = self.queue_rec.get()
            topic, payload = message

            # Exit the thread if a message with a None topic is received
            if topic is None:
                break

            # Call the message handler if one is defined
            if self.message_handler:
                if hasattr(self.message_handler, 'handle_message') and callable(getattr(self.message_handler, 'handle_message')):
                    self.message_handler.handle_message(message)

        logger.info(f"MQTT exited receiving thread")
