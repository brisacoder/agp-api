"""Module gateway_holder: Contains the GatewayHolder class for managing the Gateway instance and FastAPI app."""

import asyncio
import json
import logging
import time
from http import HTTPStatus
from typing import Any, Dict, Optional

from agp_bindings import Gateway, GatewayConfig
import agp_bindings
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from ..agent.agent_container import AgentContainer
from ..route.route_manager import RouteManager

logger = logging.getLogger(__name__)


class GatewayContainer:
    """
    A container class for managing the Gateway instance and FastAPI app.

    This class serves as a central point for handling the Gateway instance and the FastAPI application.
    It facilitates the reception of packets from the Agent Gateway Protocol (AGP) and reinjects them
    into the FastAPI application for further processing.

    Attributes:
        gateway (Gateway): An instance of the Gateway that this container encapsulates.
        fastapi_app (Optional[FastAPI]): An instance of the FastAPI application used to process
            incoming packets from the AGP.
        route_manager (RouteManager): Manages routes for agent communication.
    """

    def __init__(
        self,
        organization: str,
        namespace: str,
        agent_name: str,
        gateway: Optional[Gateway] = None,
        fastapi_app: Optional[FastAPI] = None,
    ):
        """
        Initialize a GatewayContainer instance with optional gateway management and FastAPI integration.
        Parameters:
            organization (str): Identifier for the organization.
            namespace (str): Namespace in which the agent operates.
            agent_name (str): Name of the agent.
            gateway (Optional[Gateway]): An existing Gateway instance. If not provided, a new instance will be created based on the organization, namespace, and agent_name.
            fastapi_app (Optional[FastAPI]): A FastAPI application instance for HTTP integrations.
        Attributes:
            gateway (Gateway): The Gateway instance used for managing gateway operations.
            fastapi_app (Optional[FastAPI]): The FastAPI app instance (if provided).
            organization (str): Organization identifier provided during initialization.
            namespace (str): Namespace provided during initialization.
            agent_name (str): Agent name provided during initialization.
            route_manager (RouteManager): An instance of RouteManager used for managing Agent routes.
            session: Placeholder for the session layer; initialized to None.
        """
        self.gateway = (
            gateway
            if gateway is not None
            else Gateway.new(organization, namespace, agent_name)
        )
        self.fastapi_app = fastapi_app
        self.organization = organization
        self.namespace = namespace
        self.agent_name = agent_name
        self.route_manager = RouteManager()
        # Session Layer
        self.session = None

    async def register_route(self, organization, namespace, remote_agent):
        """
        Registers a route for a remote agent within a specific organization and namespace.
        This method sets the route on the gateway and adds it to the local route registry.
        If the operation fails, the error is logged and the exception is re-raised.

        Parameters:
            organization (str): The organization identifier
            namespace (str): The namespace within the organization
            remote_agent (str): The identifier of the remote agent

        Returns:
            None

        Raises:
            Exception: If setting the route on the gateway fails
        """

        try:
            await self.gateway.set_route(
                organization=organization,
                namespace=namespace,
                agent=remote_agent,
            )
            # Only add route to route manager if set_route succeeds
            self.route_manager.add_route(
                organization=organization,
                namespace=namespace,
                remote_agent=remote_agent,
            )
        except Exception as e:
            logger.error("Failed to set route: %s", e)
            raise

    async def deregister_route(self, organization, namespace, remote_agent):
        """
        Deregisters a route for a remote agent within a specific organization and namespace.
        This method clears the route on the gateway and removes it from the local route registry.
        If the operation fails, the error is logged and the exception is re-raised.

        Parameters:
            organization (str): The organization identifier
            namespace (str): The namespace within the organization
            remote_agent (str): The identifier of the remote agent

        Returns:
            bool: True if the route was successfully removed, False if it didn't exist

        Raises:
            Exception: If clearing the route on the gateway fails
        """
        try:
            # Remote route from Gateway instance
            await self.gateway.remove_route(
                organization=organization,
                namespace=namespace,
                agent=remote_agent,
            )
            # Only delete route if remove_route succeeds
            return self.route_manager.delete_route(
                organization=organization,
                namespace=namespace,
                remote_agent=remote_agent,
            )
        except Exception as e:
            logger.error("Failed to remove route: %s", e)
            raise

    def get_fastapi_app(self) -> Optional[FastAPI]:
        """
        Returns the stored FastAPI application instance.
        """
        return self.fastapi_app

    def set_fastapi_app(self, app: FastAPI) -> None:
        """
        Sets the FastAPI application instance.
        """
        self.fastapi_app = app

    def create_gateway(self) -> Gateway:
        """
        Creates a new Gateway instance with the provided configuration.

        Returns:
            Gateway: The newly created Gateway instance.
        """
        if self.gateway is None:
            self.gateway = Gateway.new(
                self.organization, self.namespace, self.agent_name
            )
        return self.gateway

    def set_config(
        self, endpoint: str = "http://127.0.0.1:46357", insecure: bool = False
    ) -> None:
        """
        Sets the configuration for the Gateway instance.

        Args:
            endpoint (str, optional): The endpoint for the Gateway in the format "http://<hostname_or_ip>:<port>".
                                    Defaults to "http://127.0.0.1:46357".
            insecure (bool, optional): Whether to use an insecure connection. Defaults to False.

        Returns:
            None
        """
        self.gateway.config = GatewayConfig(endpoint=endpoint, insecure=insecure)
        self.gateway.configure(self.gateway.config)

    def get_gateway(self) -> Gateway:
        """
        Returns the stored Gateway instance.
        """
        return self.gateway

    def set_gateway(self, gateway: Gateway) -> None:
        """
        Sets the Gateway instance.
        """
        self.gateway = gateway

    async def _connect(self, agent_container: AgentContainer) -> int:
        """
        Connects to the remote gateway, subscribes to messages, and processes them.

        Args:
            agent_container (AgentContainer): An instance of AgentContainer containing agent details.

        Returns:
            int: The connection ID.
        """

        # An agent app is identified by a name in the format
        # /organization/namespace/agent_class/agent_id. The agent_class indicates the
        # type of agent, and there can be multiple instances of the same type running
        # (e.g., horizontal scaling of the same app in Kubernetes). The agent_id
        # identifies a specific instance of the agent and it is returned by the
        # create_agent function if not provided.

        organization = agent_container.get_organization()
        namespace = agent_container.get_namespace()
        local_agent = agent_container.get_local_agent()

        # Connect to the gateway server
        local_agent_id = await self.gateway.create_agent(
            organization,
            namespace,
            local_agent,
        )

        # Connect to the service and subscribe for messages
        try:
            conn_id = await self.gateway.connect()
        except Exception as e:
            raise ValueError(f"Error connecting to gateway: {e}") from e

        try:
            await self.gateway.subscribe(
                organization,
                namespace,
                local_agent,
                local_agent_id,
            )

        except Exception as e:
            raise RuntimeError(
                "Error subscribing to gateway: unable to subscribe."
            ) from e

        return conn_id

    async def connect_with_retry(
        self, agent_container: AgentContainer, max_duration=300, initial_delay=1
    ):
        """
        Attempts to connect to a gateway at the specified address and port using exponential backoff.
        This asynchronous function repeatedly tries to establish a connection by calling the
        connect_to_gateway function. If a connection attempt fails, it logs a warning and waits for a period
        that doubles after each failure (capped at 30 seconds) until a successful connection is made or until
        the accumulated time exceeds max_duration.
        Parameters:
            address (str): The hostname or IP address of the gateway.
            port (int): The port number to connect to.
            max_duration (int, optional): Maximum duration (in seconds) to attempt the connection. Default is 300.
            initial_delay (int, optional): Initial delay (in seconds) before the first retry. Default is 1.
        Returns:
            tuple: Returns a tuple containing the source and a message received upon successful connection.
        Raises:
            TimeoutError: If the connection is not successfully established within max_duration seconds.
        """
        start_time = time.time()
        delay = initial_delay

        while time.time() - start_time < max_duration:
            try:
                remaining_time = max_duration - (time.time() - start_time)
                if remaining_time <= 0:
                    break
                return await asyncio.wait_for(
                    self._connect(agent_container), timeout=remaining_time
                )
            except Exception as e:
                logger.warning(
                    "Connection attempt failed: %s. Retrying in %s seconds...", e, delay
                )
                await asyncio.sleep(delay)
                delay = min(
                    delay * 2, 30
                )  # Exponential backoff, max delay capped at 30 sec

        raise TimeoutError("Failed to connect within the allowed time frame")

    def process_message(self, payload: dict) -> str:
        """
        Parse and process the incoming payload message.

        This method decodes the incoming payload, validates required fields, extracts identifying information,
        and forwards the request to the FastAPI application. It returns the server's JSON response when the HTTP
        status is 200, or a JSON-formatted error message if validation fails or an error occurs during processing.

        Args:
            payload (dict): A dictionary containing the message details. Expected keys include:
            - "agent_id" (str): A non-empty identifier for the agent.
            - "route" (str): The API route where the message should be sent.
            - "input" (dict): A dictionary containing a key "messages", which must be a non-empty list of dictionaries.
               The last dictionary should have the user input under the "content" key.
            - "metadata" (Optional[dict]): An optional dictionary that may contain an "id" for tracking purposes.

        Returns:
            str: A JSON string representing the reply. This is either the successful response from the FastAPI server
             when the HTTP status is 200, or a JSON-encoded error message if validation fails or an error occurs.

        Raises:
            Exception: If an error occurs during processing, such as a non-200 response from the FastAPI server.
        """
        logging.debug("Decoded payload: %s", payload)

        # Extract assistant_id from the payload
        agent_id = payload.get("agent_id")
        logging.debug("Agent id: %s", agent_id)

        # Validate that the agent_id is not empty.
        if not payload.get("agent_id"):
            return self.create_error(
                agent_id=agent_id,
                error="agent_id is required and cannot be empty.",
                code=HTTPStatus.UNPROCESSABLE_ENTITY,
            )

        # Extract the route from the message payload.
        # This step is done to emulate the behavior of the REST API.
        route = payload.get("route")
        if not route:
            return self.create_error(
                agent_id=agent_id,
                error=HTTPStatus.NOT_FOUND.name,
                code=HTTPStatus.NOT_FOUND,
            )

        fastapi_app = self.get_fastapi_app()
        if fastapi_app is None:
            logger.error("FastAPI app is not available")
            return self.create_error(
                agent_id=agent_id,
                error="FastAPI app is not available",
                code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
        # We send all messages to graph

        client = TestClient(fastapi_app)
        try:
            headers = payload.get("headers", {})
            response = client.post(route, json=payload, headers=headers)
            response.raise_for_status()

            if response.status_code == HTTPStatus.OK:
                return json.dumps(response.json())

            logger.error("Unexpected status code: %s", response.status_code)
            return json.dumps({"error": "Unexpected status code"})
        except HTTPException as http_exc:
            error_detail = http_exc.detail
            error_msg = self.create_error(
                agent_id=agent_id, error=error_detail, code=http_exc.status_code
            )
            logger.error("HTTP error occurred: %s", error_detail)
            return error_msg
        except Exception as exc:
            error_detail = str(exc)
            error_msg = self.create_error(
                agent_id=agent_id,
                error=error_detail,
                code=HTTPStatus.INTERNAL_SERVER_ERROR,
            )
            logger.error("Unexpected error occurred: %s", error_detail)
            return error_msg

    async def start_server(self, agent_container: AgentContainer):
        """
        Asynchronously starts the data plane, which listens for incoming messages from the gateway,
        processes each message, and sends a reply back to the source agent.
        The function retrieves necessary agent configuration parameters such as organization,
        namespace, and local agent information. It then enters an infinite loop, waiting for messages,
        processing each message with process_message, logging the interaction, and replying to the source.
        If the asynchronous task is cancelled, it logs a shutdown message and raises a RuntimeError.
        Returns:
            tuple: A tuple (last_src, last_msg) containing the last received source and the last processed message.
        Raises:
            RuntimeError: If the task is cancelled, triggering a shutdown of the data plane.
        """

        last_src = ""
        last_msg = ""

        organization = agent_container.get_organization()
        namespace = agent_container.get_namespace()
        local_agent = agent_container.get_local_agent

        try:
            logger.info(
                "AGP Server started for agent: %s/%s/%s",
                organization,
                namespace,
                local_agent,
            )
            while True:
                src, recv = await self.gateway.receive()
                payload = json.loads(recv.decode("utf8"))

                # Store the last received source and message
                last_src = src
                last_msg = payload

                logger.info("Received message %s, from src agent %s", payload, src)

                msg = self.process_message(payload)

                # Publish reply message to src agent
                await self.gateway.publish_to(msg.encode(), src)
        except asyncio.exceptions.CancelledError as e:
            logger.error("Shutdown server")
            raise RuntimeError(
                f"Shutdown server. Last source: {last_src}, Last message: {last_msg}"
            ) from e
        finally:
            logger.info(
                "Shutting down agent %s/%s/%s", organization, namespace, local_agent
            )

    async def publish_messsage(
        self,
        session: agp_bindings.PySessionInfo,
        message: Dict[str, Any],
        agent_container: AgentContainer,
        remote_agent: str,
    ):
        """
        Sends a message (JSON string) to the remote endpoint

        Args:
            msg (str): A JSON string representing the request payload.
        """

        organization = agent_container.get_organization()
        namespace = agent_container.get_namespace()

        try:
            json_message = json.dumps(message)
            await self.gateway.publish(
                session,
                json_message.encode(),
                organization,
                namespace,
                remote_agent
            )
        except Exception as e:
            raise ValueError(f"Error sending message: {e}") from e

    @classmethod
    def create_error(cls, error, code, agent_id: str | None) -> str:
        """
        Creates a reply message with an error code.

        Parameters:
            error (str): The error message that will be included in the reply.
            code (int): The numerical code representing the error.

        Returns:
            str: A JSON-formatted string encapsulating the error message and error code.
        """
        payload = {
            "message": error,
            "error": code,
            "agent_id": agent_id,
        }
        msg = json.dumps(payload)
        return msg


