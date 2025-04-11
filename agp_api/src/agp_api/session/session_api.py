""" """

import datetime
import logging
from typing import Optional

import agp_bindings
from agp_bindings import (
    PyFireAndForgetConfiguration,
    PyRequestResponseConfiguration,
    PyStreamingConfiguration,
    PyAgentType,
)

from agp_api.exception.session_creation import AGPSessionCreationError
from agp_api.gateway.gateway_container import GatewayContainer
from agp_api.session.session_type import SessionType

logger = logging.getLogger(__name__)


class SessionAPI:
    """
    Manages sessions for agents in an organization and namespace hierarchy.

    This class provides methods to add, delete, and retrieve routes based on
    organization, namespace, and remote agent information.
    """

    def __init__(self) -> None:
        """
        Initializes the RouteManager with empty route collections.
        """

    async def create_session(
        self,
        session_type: SessionType,
        gateway_container: GatewayContainer,

    ):
        """
        Creates a session based on the specified session type.

        Args:
            session_type: The type of session to create (from SessionType enum)
            gateway_container: The gateway container to use for creating the session
            organization: (Optional) The organization identifier
            namespace: (Optional) The namespace identifier
            broadcast_topic: (Optional) The broadcast topic

        Returns:
            The created session configuration object or None if creation fails
        """
        logger.info(f"Creating session of type: {session_type}")

        try:
            if session_type == SessionType.FIRE_AND_FORGET:
                return await self._create_fire_and_forget_session(gateway_container)
            elif session_type == SessionType.PUBSUB:
                return await self._create_pubsub_session(gateway_container, organization, namespace, broadcast_topic)
            elif session_type == SessionType.REQUEST_REPLY:
                return await self._create_request_reply_session(gateway_container)
            elif session_type == SessionType.STREAMING:
                return await self._create_streaming_session(gateway_container)
            else:
                logger.error(f"Unknown session type: {session_type}")
                raise AGPSessionCreationError(f"Unknown session type: {session_type}")
        except AGPSessionCreationError as e:
            logger.error(f"Failed to create {session_type.name} session: {e}")
            raise

    async def _create_request_reply_session(
        self, gateway_container: GatewayContainer
    ) -> Optional[PyRequestResponseConfiguration]:
        try:
            config = agp_bindings.PyRequestResponseConfiguration()
            session = await gateway_container.gateway.create_rr_session(config)
            return session
        except Exception as e:
            logger.error(
                "Failed to create request-reply session for gateway_container %s: %s",
                gateway_container,
                e,
            )
            raise AGPSessionCreationError(
                "Request reply session creation failed"
            ) from e

    async def _create_fire_and_forget_session(
        self, gateway_container: GatewayContainer
    ) -> Optional[PyFireAndForgetConfiguration]:
        """
        Creates a fire-and-forget session configuration for the Gateway instance.

        Returns:
            PyFireAndForgetConfiguration or None: The fire-and-forget session configuration,
            or None if an error occurs.
        """
        try:
            config = agp_bindings.PyFireAndForgetConfiguration()
            session = await gateway_container.gateway.create_ff_session(config)
            return session
        except Exception as e:
            logger.error(
                "Failed to create fire-and-forget session for gateway_container %s: %s",
                gateway_container,
                e,
            )
            raise AGPSessionCreationError(
                "Request reply session creation failed"
            ) from e

    async def _create_pubsub_session(
        self, gateway_container: GatewayContainer, organization, namespace, broadcast_topic
    ) -> Optional[PyFireAndForgetConfiguration]:
        """
        Creates a fire-and-forget session configuration for the Gateway instance.

        Returns:
            PyFireAndForgetConfiguration or None: The fire-and-forget session configuration,
            or None if an error occurs.
        """
        try:
            config = PyStreamingConfiguration(
                agp_bindings.PySessionDirection.BIDIRECTIONAL,
                topic=PyAgentType(
                    organization, namespace, broadcast_topic
                ),
                max_retries=5,
                timeout=datetime.timedelta(seconds=5),
            )
            session = await gateway_container.gateway.create_ff_session(config)
            return session
        except Exception as e:
            logger.error(
                "Failed to create pubsub session for gateway_container %s: %s",
                gateway_container,
                e,
            )
            raise AGPSessionCreationError(
                "PubSub session creation failed"
            ) from e
