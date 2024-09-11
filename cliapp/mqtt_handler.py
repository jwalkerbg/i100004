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

        self.pending_messages = { }

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

    def define_message_handler(self, handler: callable = None) -> None:
        """
        Assigns a custom message handler function to handle incoming MQTT messages.

        Parameters:
        - handler (callable, optional): A function reference that will be called when a message is received.
        If no handler is provided (None), no custom handler will be set.

        Returns:
        - None: This method does not return a value. It modifies the `self.message_handler` attribute.

        Behavior:
        - Stores the provided handler function in the `self.message_handler` attribute.
        - The handler function should accept a single parameter, which is the message object (`msg`),
        containing details about the received MQTT message.
        """
        self.message_handler = handler

    def exit_threads(self) -> None:
        """
        Gracefully exits the MQTT publish and receive threads by signaling them to stop and waiting for them to terminate.

        Behavior:
        - For the publish thread (`self.mqtt_publish_thread`):
        - A tuple `(None, None)` is inserted into `self.queue_pub` to signal the thread to exit.
        - The thread is then joined (i.e., the main thread waits for the publish thread to finish).

        - For the receive thread (`self.mqtt_receive_thread`):
        - A tuple `(None, None)` is inserted into `self.queue_rec` to signal the thread to exit.
        - The thread is then joined (i.e., the main thread waits for the receive thread to finish).

        Attributes:
        - `self.queue_pub`: A `Queue` that holds messages to be published by the `self.mqtt_publish_thread`.
        - `self.mqtt_publish_thread`: A thread that pulls messages from `self.queue_pub` and publishes them to the MQTT broker.

        - `self.queue_rec`: A `Queue` that holds messages received from the MQTT broker to be processed by `self.mqtt_receive_thread`.
        - `self.mqtt_receive_thread`: A thread that pulls messages from `self.queue_rec` and processes them, typically by calling `self.message_handler`.

        Usage:
        - This method should be called when the application needs to shut down or restart and you need to safely stop background threads.

        Returns:
        - None: This method does not return anything. It only ensures the threads are properly stopped.
        """
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
        """
        Attempts to connect to the MQTT broker, synchronizing the connection process with a threading.Event object.

        Behavior:
        - Clears the `self.connection_established` event to indicate that a new connection attempt is starting.
        - Calls `self.client.connect()` to initiate the connection to the broker.
        - Starts the MQTT client loop in the background with `self.client.loop_start()`.
        - Waits for the `self.connection_established` event to be set by the `on_connect()` callback within a timeout period.
        - If the connection is established within the timeout, returns True. Otherwise, returns False.

        Parameters:
        - None

        Returns:
        - bool: True if the connection is successfully established, False if the connection times out or fails.

        Process Flow:
        1. The `self.connection_established` event is cleared to indicate that the client is not yet connected.
        2. The `client.connect()` method is used to attempt to connect to the MQTT broker.
        3. The `client.loop_start()` method is called to start the background loop that handles MQTT communication.
        4. If an exception occurs during connection, an error message is logged and the method returns False.
        5. The method waits for `self.connection_established` to be set by the `on_connect()` callback.
        6. If the event is set within the timeout (from `self.config['mqtt']['timeout']`), the connection is considered successful, and the method returns True.
        7. If the timeout expires without the event being set, it logs a warning and returns False.

        Usage:
        - This method is used to initiate the connection process to the MQTT broker and synchronize with the broker using the `on_connect()` callback.
        - The method ensures that the connection is established within a specified time limit.
        """
        host = self.config['mqtt']['host']
        port = self.config['mqtt']['port']
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
        waitres = self.connection_established.wait(self.config['mqtt']['timeout'])

        if waitres:
            # Connection was successfully established within the timeout.
            logger.info("MQTT connection established")
            return True
        else:
            # Connection was not established within the timeout.
            logger.warning("No MQTT connection was established in time")
            return False

    def on_connect(self, client: mqtt.Client, userdata: object, flags: dict, rc: int, properties: dict = None) -> None:
        """
        MQTT callback function that is triggered when the client connects to the broker.

        Behavior:
        - If the connection is successful (indicated by `rc == 0`), it logs a success message and sets the `self.connection_established` event to notify the `connect()` method that the connection was successful.
        - If the connection fails (indicated by `rc != 0`), it logs an error message with the return code (rc).

        Parameters:
        - client (mqtt.Client): The MQTT client instance that is attempting to connect.
        - userdata (object): User-defined data passed to callbacks (unused here).
        - flags (dict): Response flags from the broker.
        - rc (int): The connection result code. A value of 0 indicates a successful connection. Other values indicate errors.
        - properties (dict, optional): MQTT 5.0 properties associated with the connection (unused here).

        Returns:
        - None: This is a callback method and does not return anything.

        Usage:
        - This method is automatically triggered by the Paho MQTT client when the connection status is received from the broker.
        - It signals to the rest of the application (through `self.connection_established.set()`) that the connection has been successfully established, allowing the program to proceed.
        """
        if rc == 0:
            # Connection was successful
            logger.info("MQTT connected to MQTT broker.")

            # Set the event to signal the connect() method that the connection is established.
            self.connection_established.set()
        else:
            # Connection failed with a return code (rc != 0)
            logger.info(f"MQTT failed to connect, return code {rc}")

    def disconnect_and_exit(self) -> None:
        """
        Cleanly disconnect from the MQTT broker and exit the publishing and receiving threads.

        Behavior:
        - Signals the publishing and receiving threads to stop by using `self.exit_threads()`.
        - Attempts to disconnect from the MQTT broker, triggering the `on_disconnect()` callback if the disconnection is successful.
        - Handles any exceptions that may occur during the disconnection process to ensure the program logs an error instead of crashing.

        Steps:
        1. Calls `exit_threads()` to stop the background threads responsible for publishing and receiving MQTT messages.
        2. Calls `self.client.disconnect()` to initiate a clean disconnection from the MQTT broker.
        This triggers the `on_disconnect()` callback once the client is successfully disconnected.

        Logging Behavior:
        - Logs the start of the shutdown process and confirms disconnection and thread termination.
        - If an error occurs during disconnection, it logs the error but does not stop the program from continuing the shutdown process.

        Returns:
        - None: This function ensures a clean shutdown of the MQTT client and associated threads without returning a value.
        """
        logger.info("MQTT initiating clean shutdown...")

        # Step 1: Exit the publishing and receiving threads
        self.exit_threads()  # Signal the threads to stop and wait for them to finish

        # Step 2: Disconnect from the MQTT broker
        try:
            self.client.disconnect()  # This will trigger the on_disconnect() callback
            logger.info("MQTT disconnected from MQTT broker.")
        except Exception as e:
            # Log any errors that occur during the disconnection process
            logger.error(f"MQTT error while disconnecting from the broker: {e}")

        logger.info("MQTT clean shutdown complete.")

    def on_disconnect(self, client: mqtt.Client, userdata: object, rc: int) -> None:
        """
        Callback triggered when the client disconnects from the MQTT broker.

        Behavior:
        - If the disconnection is intentional (indicated by `rc == 0`), logs that the client successfully disconnected from the broker.
        - If the disconnection is unintentional (`rc != 0`), logs a warning and attempts to reconnect to the broker.
        - If the reconnection attempt fails, logs the error.

        Parameters:
        - client (mqtt.Client): The MQTT client instance that was disconnected.
        - userdata (object): User-defined data passed to the callback (unused here).
        - rc (int): The reason code for the disconnection.
        - A value of `0` indicates a successful, intentional disconnect (e.g., through `client.disconnect()`).
        - A non-zero value indicates an unexpected disconnect (e.g., due to network issues or broker failure).

        Reconnection Logic:
        - If an unintentional disconnection occurs (`rc != 0`), the function attempts to automatically reconnect to the broker using `client.reconnect()`.
        - If the reconnection attempt fails, the exception is caught, and an error is logged.

        Returns:
        - None: This function does not return a value and simply handles the disconnection event and, if necessary, reconnection.

        Logging Behavior:
        - Logs successful disconnections (when `rc == 0`).
        - Logs warnings and errors when unexpected disconnections occur or when reconnection attempts fail.
        """
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
        """
        Subscribes to the given MQTT topic and waits for acknowledgment from the broker.

        Behavior:
        - Clears the `self.subscription_estabilished` event, indicating that no subscription acknowledgment has been received yet.
        - Initiates a subscription to the specified `topic` using `self.client.subscribe()`.
        - Stores the `mid` (message ID) of the subscription request in `self.pending_subscriptions` to track the acknowledgment.
        - Logs the subscription request.
        - Waits for the subscription acknowledgment by monitoring the `self.subscription_estabilished` event.
        - If acknowledgment is received within the timeout period, it logs success and returns `True`.
        - If no acknowledgment is received within the timeout period, it logs a warning and returns `False`.

        Parameters:
        - topic (str): The MQTT topic to subscribe to.

        Returns:
        - bool: Returns `True` if the subscription is successfully acknowledged, otherwise `False` if the acknowledgment times out.

        Process Flow:
        1. The `self.subscription_estabilished` event is cleared to signal that the subscription has not yet been confirmed.
        2. The MQTT client attempts to subscribe to the specified topic, and the `mid` (message ID) of the subscription is stored.
        3. The method then waits for the `on_subscribe()` callback to signal that the subscription was acknowledged by the broker.
        4. If the acknowledgment is received within the timeout, it returns `True`. If not, it returns `False`.

        Usage:
        - This method is used to subscribe to a topic and ensure that the subscription is confirmed by the broker within a specified time.
        """
        # Clear the subscription event to signal that no acknowledgment has been received yet
        self.subscription_estabilished.clear()

        # Attempt to subscribe to the specified topic
        result, mid = self.client.subscribe(topic=topic)

        # Store the subscription message ID (mid) and associate it with the topic
        self.pending_subscriptions[mid] = topic

        # Log the subscription request
        logger.info(f"MQTT subscribing to topic: {topic}")

        # Wait for the subscription acknowledgment from the broker, with a timeout
        waitres = self.subscription_estabilished.wait(self.config['mqtt']['timeout'])

        if waitres:
            # If the acknowledgment was received in time, log success and return True
            logger.info(f"MQTT subscription established")
            return True
        else:
            # If the acknowledgment was not received in time, log a warning and return False
            logger.warning(f"No MQTT subscription established in time")
            return False

    def on_subscribe(self, client: mqtt.Client, userdata: object, mid: int, rc: int, properties: dict = None) -> None:
        """
        MQTT callback that is triggered when the broker acknowledges a subscription request.

        Behavior:
        - Sets the `self.subscription_estabilished` event to notify the `subscribe()` method that the subscription has been acknowledged.
        - Retrieves the corresponding topic for the subscription `mid` from `self.pending_subscriptions`.
        - Logs whether the subscription acknowledgment was received and associates it with the correct topic.

        Parameters:
        - client (mqtt.Client): The MQTT client instance that is handling the subscription.
        - userdata (object): User-defined data passed to the callback (unused here).
        - mid (int): The message ID of the subscription acknowledgment.
        - rc (int): The result code of the subscription acknowledgment (0 indicates success).
        - properties (dict, optional): MQTT 5.0 properties (unused here).

        Returns:
        - None: This is a callback method and does not return anything.

        Usage:
        - This method is automatically triggered by the Paho MQTT client when the broker acknowledges a subscription.
        - It signals to the rest of the application (through `self.subscription_estabilished.set()`) that the subscription was successfully established.
        """
        # Signal that the subscription acknowledgment has been received
        self.subscription_estabilished.set()

        # Retrieve the topic associated with the message ID (mid)
        topic = self.pending_subscriptions.pop(mid, None)

        # Log the subscription acknowledgment along with the topic, if available
        if topic:
            logger.info(f"MQTT subscription to '{topic}' acknowledged")
        else:
            logger.info(f"MQTT subscription with mid '{mid}' acknowledged but no topic found in pending subscriptions")

    def on_unsubscribe(self, userdata: object, mid: int, rc: int, properties: dict = None) -> None:
        """
        MQTT callback function triggered when the broker acknowledges an unsubscribe request.

        Behavior:
        - Logs a message confirming that the broker has acknowledged the client's request to unsubscribe from a topic.
        - The message ID (`mid`) corresponds to the unsubscribe request and can be used for tracking.
        - The `rc` (return code) indicates the result of the unsubscribe operation.

        Parameters:
        - userdata (object): User-defined data passed to the callback (not used in this implementation).
        - mid (int): The message ID of the unsubscribe request. This ID can be used to track the request.
        - rc (int): The result code returned by the broker, indicating the success or failure of the unsubscribe request. A value of `0` typically indicates success.
        - properties (dict, optional): MQTT 5.0 properties associated with the unsubscribe acknowledgment (unused in this implementation).

        Returns:
        - None: This function does not return a value. It simply logs the acknowledgment.

        Usage:
        - This method is called automatically by the MQTT client when the broker acknowledges an unsubscribe request.
        - The `mid` is used to identify which unsubscribe request was acknowledged, and this can be useful when dealing with multiple subscriptions.

        Logging Behavior:
        - Logs the message ID (`mid`) of the acknowledged unsubscribe request for tracking purposes.
        """
        # Log the message that the unsubscribe request was acknowledged by the broker
        logger.info(f"MQTT unsubscribe acknowledgment for mid '{mid}' received")

    def on_publish(self, client: mqtt.Client, userdata: object, mid: int, reason_code: int, properties: dict = None) -> None:
        """
        Enhanced MQTT on_publish callback to track message publication status.
        """
        # Log successful message publication with its message ID and reason code
        if reason_code == 0:
            logger.info(f"MQTT message with mid '{mid}' successfully published.")
        else:
            logger.warning(f"MQTT failed to publish MQTT message with mid '{mid}', reason code: {reason_code}")

        # Optionally, remove the message ID from a tracking dictionary of pending messages (if applicable)
        if mid in self.pending_messages:
            logger.info(f"MQTT removing message ID '{mid}' from pending messages.")
            del self.pending_messages[mid]

    def publish_message(self, topic: str, payload: str) -> None:
        """
        Publishes a message to the MQTT topic asynchronously by adding it to the publishing queue.

        Behavior:
        - Places the message (topic and payload) into `self.queue_pub`, which is processed by a separate thread (`publish_mqtt_message`).
        - Logs the message being queued for publishing. If the message payload is large and verbosity is disabled, it logs a placeholder instead of the full message.

        Parameters:
        - topic (str): The MQTT topic to which the message will be published.
        - payload (str): The message content (payload) to publish.

        Returns:
        - None: This method enqueues the message for publishing and does not return a value.

        Logging Behavior:
        - If verbosity is disabled (`self.config['verbose']` is `False`) and the payload exceeds a length defined by `self.config['mqtt'].get('long_payload', 0)`, it logs `"<long payload>"` instead of the full message content.
        """
        # Place the topic and payload into the publishing queue
        self.queue_pub.put((topic, payload))

        # Log the message being queued, optionally truncating the payload if verbosity is off and the payload is long
        logger.info(f"MQTT publish: -t '{topic}' -m '{'<long payload>' if not self.config['verbose'] and len(payload) > self.config['mqtt'].get('long_payload', 0) else payload}'")

    def publish_mqtt_message(self, client: mqtt.Client, q: queue.Queue) -> None:
        """
        Thread function responsible for publishing MQTT messages from the queue (`self.queue_pub`).

        Behavior:
        - Continuously retrieves messages from `self.queue_pub`.
        - Publishes each message to the specified MQTT topic.
        - If the message is successfully queued for publishing, it tracks the message ID (`mid`) in `self.pending_messages`.
        - If a `(None, None)` message is received, it breaks the loop and exits the thread (this is used as a signal to stop the thread).

        Parameters:
        - client (mqtt.Client): The MQTT client instance that is handling the publishing.
        - q (queue.Queue): The queue (likely `self.queue_pub`) from which messages are retrieved for publishing.

        Returns:
        - None: This function runs continuously in a thread and does not return a value.

        Thread Lifecycle:
        - The thread will run indefinitely, publishing messages from the queue until a `(None, None)` tuple is received, signaling the thread to stop.

        Publishing Behavior:
        - Each message retrieved from the queue is a tuple containing a `topic` and `payload`.
        - The message is published to the broker using `self.client.publish()`.
        - The thread tracks each published message by storing its message ID (`mid`) in `self.pending_messages`, allowing the program to track the status of each message until the broker confirms it has been published.
        """
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
                logger.info(f"MQTT message queued for topic '{topic}' with mid '{mid}'")
            else:
                logger.warning(f"MQTT failed to publish message to topic '{topic}', return code: {result.rc}")

            # Wait for the message to be fully published (if QoS 1 or 2)
            result.wait_for_publish()

        logger.info(f"MQTT exited publishing thread")

    def on_message(self, client: mqtt.Client, userdata: object, message: mqtt.MQTTMessage) -> None:
        """
        Callback function that is triggered when a message is received from a subscribed MQTT topic.

        Behavior:
        - Decodes the message payload and logs it. If the payload is large and verbosity is disabled, logs a placeholder instead of the full message.
        - Puts the topic and payload into `self.queue_rec`, a queue used by the receiving thread (`receive_mqtt_message`).

        Parameters:
        - client (mqtt.Client): The MQTT client instance that is receiving the message.
        - userdata (object): User-defined data passed to the callback (unused in this case).
        - message (mqtt.MQTTMessage): The message object that contains details about the received MQTT message, including topic, payload, QoS, and retain flag.

        Returns:
        - None: This is a callback function and does not return any value.

        Logging Behavior:
        - If the payload is long and verbosity is disabled, it logs "<long payload>" instead of the full message.
        - The maximum payload length before truncating is defined by `self.config['mqtt'].get('long_payload', 0)`.

        Queueing Behavior:
        - The received message (topic and payload) is placed into `self.queue_rec`, which is processed by the receiving thread (`receive_mqtt_message()`).
        """
        # Decode the payload
        payload = message.payload.decode()

        # Log the message. If verbose mode is off and the payload is long, log a placeholder.
        logger.info(
            f"MQTT receive: -t '{message.topic}' -m '{'<long payload>' if not self.config['verbose'] and len(payload) > self.config['mqtt'].get('long_payload', 0) else payload}'"
        )

        # Place the topic and payload into the receiving queue
        self.queue_rec.put((message.topic, payload))

    def receive_mqtt_message(self, client: mqtt.Client, q: queue.Queue) -> None:
        """
        Thread function responsible for processing MQTT messages from the queue (`self.queue_rec`).

        Behavior:
        - Continuously retrieves messages from the `self.queue_rec` queue.
        - If a message with a topic of `None` is received, it breaks the loop and exits the thread (this is used as a signal to stop the thread).
        - If a `message_handler` function is provided, it calls the handler for each received message.

        Parameters:
        - client (mqtt.Client): The MQTT client instance that is running the thread.
        - q (queue.Queue): The queue (likely `self.queue_rec`) where received messages are stored.

        Returns:
        - None: This function runs continuously in a thread and does not return a value.

        Thread Lifecycle:
        - The thread will run indefinitely, processing incoming messages from the queue until a message with `None` as the topic is received, signaling the thread to exit.

        Processing Behavior:
        - Each message retrieved from the queue is a tuple containing a `topic` and `payload`.
        - If `self.message_handler` is provided, it is called with the `message` (a tuple containing topic and payload).
        """
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
                self.message_handler(message)

        logger.info(f"MQTT exited receiving thread")
