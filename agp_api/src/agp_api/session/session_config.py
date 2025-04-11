"""
Module: session_config
This module defines the SessionConfig class that provides factory methods for creating various session
configurations used by AGP Session Layer. The configurations supported include:
    - Request/Reply sessions: For synchronous communication where a response is expected.
    - Fire-And-Forget sessions: For asynchronous communication where no response is needed.
    - PubSub sessions: Utilizing a streaming configuration for bidirectional communication tailored to
      publish/subscribe patterns. This configuration makes use of an organization, namespace, and
      broadcast topic.
    - Streaming sessions: For unidirectional message flow primarily used in streaming scenarios.
Each factory method encapsulates the creation and configuration of session objects from the "agp_bindings"
module, allowing for standardized session management. Parameters such as maximum retry counts and timeout
durations can be customized to suit different operational requirements.
Usage Example:
    request_reply_config = SessionConfig.create_request_reply_config()
    fire_and_forget_config = SessionConfig.create_fire_and_forget_config()
    pubsub_config = SessionConfig.create_pubsub_config(
        organization="YourOrganization",
        namespace="YourNamespace",
        broadcast_topic="YourBroadcastTopic"
    streaming_config = SessionConfig.create_streaming_config()
Note:
    Ensure that the "agp_bindings" module is correctly installed and configured, as this module
    relies on its classes and enumerations (such as PyFireAndForgetConfiguration, PyRequestResponseConfiguration,
    PyStreamingConfiguration, PyAgentType, and PySessionDirection) for proper operation.

"""

import datetime
from typing import Optional

import agp_bindings
from agp_bindings import (
    PyAgentType,
    PyFireAndForgetConfiguration,
    PyRequestResponseConfiguration,
    PyStreamingConfiguration,
)


class FireAndForgetConfig(PyFireAndForgetConfiguration):
    """
    FireAndForgetConfig is a subclass of PyFireAndForgetConfiguration that provides a custom
    configuration for fire-and-forget sessions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RequestResponseConfig(PyRequestResponseConfiguration):
    """
    RequestResponseConfig is a subclass of PyRequestResponseConfiguration that provides a custom
    configuration for request-reply sessions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PubSubConfig(PyStreamingConfiguration):
    """
    PubSubConfig is a subclass of PyStreamingConfiguration that provides a custom
    configuration for publish-subscribe sessions.
    """

    def __init__(
        self,
        direction: agp_bindings.PySessionDirection,
        topic: Optional[PyAgentType],
        max_retries: int = 5,
        timeout_seconds: int = 5,
        *args,
        **kwargs,
    ):
        """ 
        Initialize the PubSubConfig with the provided parameters.

        Parameters:
            direction (PySessionDirection): The session direction.
            topic (Optional[PyAgentType]): The agent type representing the topic.
            max_retries (int): The maximum number of retry attempts.
        """
        super().__init__(
            direction,
            topic,
            max_retries=max_retries,
            timeout=datetime.timedelta(timeout_seconds),
            *args,
            **kwargs,
        )


class StreamingConfig(PyStreamingConfiguration):
    """
    StreamingConfig is a subclass of PyStreamingConfiguration that provides a custom
    configuration for streaming sessions.
    """

    def __init__(
        self,
        direction=agp_bindings.PySessionDirection.SENDER,
        topic=None,
        max_retries: int = 3,
        timeout_seconds: int = 10,
        *args,
        **kwargs,
    ):
        super().__init__(
            direction,
            topic,
            max_retries=max_retries,
            timeout=datetime.timedelta(timeout_seconds),
            *args,
            **kwargs,
        )


class SessionConfig:
    """
    SessionConfig provides factory methods for creating various session configurations used in the system.

    Class Methods:
        create_request_reply_config() -> PyRequestResponseConfiguration:
            Creates and returns a configuration for Request/Reply sessions.

        create_fire_and_forget_config() -> PyFireAndForgetConfiguration:
            Creates and returns a configuration for Fire-And-Forget sessions.

        create_pubsub_config(
            Creates and returns a configuration tailored for PubSub sessions using a streaming configuration.
            Parameters:
                organization: The organization identifier.
                namespace: The namespace for the session.
                broadcast_topic: The topic used for broadcasting messages.
                max_retries: The maximum number of retry attempts (default is 5).
                timeout_seconds: The timeout duration in seconds for the session (default is 5).

        create_streaming_config(
            Creates and returns a configuration for streaming sessions with unidirectional flow.
            Parameters:
                max_retries: The maximum number of retry attempts (default is 3).
                timeout_seconds: The timeout duration in seconds for the session (default is 10).
    """

    @classmethod
    def create_request_response_config(cls) -> RequestResponseConfig:
        """
        Creates a RequestReply session configuration.
        """
        return RequestResponseConfig()

    @classmethod
    def create_fire_and_forget_config(cls) -> FireAndForgetConfig:
        """
        Creates a Fire-And-Forget session configuration.
        """
        return FireAndForgetConfig()

    @classmethod
    def create_pubsub_config(
        cls,
        organization: str,
        namespace: str,
        broadcast_topic: str,
        max_retries: int = 5,
        timeout_seconds: int = 5,
    ) -> PubSubConfig:
        """
        Creates a PubSub configuration for establishing a bidirectional streaming session.

        This configuration is tailored for the PubSub client and encapsulates details
        such as the target topic, retry mechanism, and timeout settings, allowing for
        robust and efficient message broadcasting.

        Parameters:
            organization (str): Identifier for the organization owning the session.
            namespace (str): Specific namespace within the organization for grouping resources.
            broadcast_topic (str): The topic name used for broadcasting messages.
            max_retries (int, optional): Maximum number of retry attempts for handling transient errors. Defaults to 5.
            timeout_seconds (int, optional): Timeout in seconds for the session operations. Defaults to 5.

        Returns:
            PubSubConfig: A configured PubSub session instance ready for use in a bidirectional streaming context.

        """
        return PubSubConfig(
            agp_bindings.PySessionDirection.BIDIRECTIONAL,
            topic=PyAgentType(organization, namespace, broadcast_topic),
            max_retries=max_retries,
            timeout=datetime.timedelta(seconds=timeout_seconds),
        )

    @classmethod
    def create_streaming_config(
        cls,
        direction=agp_bindings.PySessionDirection.UNIDIRECTIONAL,
        topic=None,
        max_retries: int = 3,
        timeout_seconds: int = 10,
    ) -> PyStreamingConfiguration:
        """
        Creates a streaming session configuration with customizable parameters.

        This method constructs and returns a PyStreamingConfiguration object configured
        for a streaming session. By default, the session is set up as unidirectional, but
        this can be adjusted if bidirectional or specific streaming directions are supported.

        Parameters:
            direction (PySessionDirection, optional): The direction of the streaming session.
                Defaults to agp_bindings.PySessionDirection.UNIDIRECTIONAL.
            topic (str, optional): An optional topic used for session identification or routing.
                Some streaming sessions may not require a topic.
            max_retries (int): The maximum number of retry attempts for establishing the session.
                Defaults to 3.
            timeout_seconds (int): The timeout duration in seconds for session establishment.
                Defaults to 10.

        Returns:
            PyStreamingConfiguration: A streaming session configuration instance with the
            specified parameters.

        Notes:
            - Ensure that the provided direction is supported by your binding.
            - The timeout is internally converted to a datetime.timedelta object.

        Raises:
            ValueError: If any provided parameters are invalid (e.g., negative timeout_seconds).
        """
        return PyStreamingConfiguration(
            direction,
            topic,  # Streaming sessions may not require a topic
            max_retries=max_retries,
            timeout=datetime.timedelta(seconds=timeout_seconds),
        )
