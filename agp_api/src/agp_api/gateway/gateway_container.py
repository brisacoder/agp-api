"""Module gateway_holder: Contains the GatewayHolder class for managing the Gateway instance and FastAPI app."""

import asyncio
from http import HTTPStatus
import json
import logging
import time
from typing import Any, Dict, Optional

from agp_bindings import Gateway, GatewayConfig
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from ..agent.agent_container import AgentContainer

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
    """

    def __init__(
        self, gateway: Optional[Gateway] = None, fastapi_app: Optional[FastAPI] = None
    ):
        """
        Initializes the GatewayContainer with a Gateway instance and optionally a FastAPI app.

        Args:
            gateway (Optional[Gateway]): The Gateway instance to manage. If not provided, a new instance will be created.
            fastapi_app (Optional[FastAPI]): The FastAPI application instance.
        """
        self.gateway = gateway if gateway is not None else Gateway()
        self.fastapi_app = fastapi_app

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
        self.gateway = Gateway()
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

    async def _connect(self, agent_container: AgentContainer, remote_agent) -> int:
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
            if remote_agent is not None:
                await self.gateway.set_route(organization, namespace, remote_agent)

        except Exception as e:
            raise RuntimeError(
                "Error subscribing to gateway: unable to subscribe."
            ) from e

        return conn_id

    async def connect_with_retry(
        self,
        agent_container: AgentContainer,
        max_duration=300,
        initial_delay=1,
        remote_agent: Optional[str] = None,
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
                return await self._connect(agent_container, remote_agent)
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

        This function decodes the incoming payload, validates essential fields, extracts required information,
        and forwards the request to a FastAPI app. It then returns the server's response or handles errors appropriately.

        Args:
            payload (dict): A dictionary containing the message details. Expected keys include:
            
            - `"agent_id"` (str): Identifier for the agent; must be non-empty.
            
            - `"route"` (str): The API route to which the message should be sent.
            
            - `"input"` (dict): A dictionary with a key `"messages"`, which is a non-empty list where each element 
            is a dictionary. The last message in this list should contain the human input under the `"content"` key.
            
            - `"metadata"` (Optional[dict]): A dictionary that may contain an `"id"` for tracking purposes.

        Returns:
            str: A JSON string representing the reply. This is either the successful response from the FastAPI server
            when a status code `200` is returned, or a JSON-encoded error message if validation fails.

        Raises:
            Exception: If the FastAPI server returns a status code other than `200`, an exception with the status code
            and error details is raised.
        """
        logging.debug("Decoded payload: %s", payload)

        # Extract assistant_id from the payload
        agent_id = payload.get("agent_id")
        logging.debug("Agent id: %s", agent_id)

        # Validate that the assistant_id is not empty.
        if not payload.get("agent_id"):
            return self.create_error("agent_id is required and cannot be empty.", 422)

        # Extract the route from the message payload.
        # This step is done to emulate the behavior of the REST API.
        route = payload.get("route")
        if not route:
            return self.create_error("Not Found.", 404)

        message_id = None
        # Validate the config section: ensure that config.tags is a non-empty list.
        if (metadata := payload.get("metadata", None)) is not None:
            message_id = metadata.get("id")

        # -----------------------------------------------
        # Extract the human input content from the payload.
        # We expect the content to be located at: payload["input"]["messages"][0]["content"]
        # -----------------------------------------------

        # Retrieve the 'input' field and ensure it is a dictionary.
        input_field = payload.get("input")
        if not isinstance(input_field, dict):
            return self.create_error("The 'input' field should be a dictionary.", 500)

        # Retrieve the 'messages' list from the 'input' dictionary.
        messages = input_field.get("messages")
        if not isinstance(messages, list) or not messages:
            return self.create_error(
                "The 'input.messages' field should be a non-empty list.", 500
            )

        # Access the last message in the list.
        last_message = messages[-1]
        if not isinstance(last_message, dict):
            return self.create_error(
                "The first element in 'input.messages' should be a dictionary.", 500
            )

        # Extract the 'content' from the first message.
        human_input_content = last_message.get("content")
        if human_input_content is None:
            return self.create_error(
                "Missing 'content' in the first message of 'input.messages'.", 500
            )

        fastapi_app = self.get_fastapi_app()
        if fastapi_app is None:
            logger.error("FastAPI app is not available")
            return self.create_error("Internal server error", 500)
        # We send all messages to graph

        client = TestClient(fastapi_app)
        try:
            response = client.post(route, json=payload)
            response.raise_for_status()

            if response.status_code == HTTPStatus.OK:
                return json.dumps(response.json())

            logger.error("Unexpected status code: %s", response.status_code)
            return json.dumps({"error": "Unexpected status code"})
        except HTTPException as http_exc:
            error_detail = http_exc.detail
            messages.append({"role": "ai", "content": error_detail})
            payload = {
                "agent_id": agent_id,
                "output": {"messages": messages},
                "model": "gpt-4o",
                "metadata": {"id": message_id},
            }
            logger.error("HTTP error occurred: %s", error_detail)
            return json.dumps(payload)
        except Exception as exc:
            error_detail = str(exc)
            messages.append({"role": "ai", "content": error_detail})
            payload = {
                "agent_id": agent_id,
                "output": {"messages": messages},
                "model": "gpt-4o",
                "metadata": {"id": message_id},
            }
            logger.error("Unexpected error occurred: %s", error_detail)
            return json.dumps(payload)

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

    async def publish_messsage(self, message: Dict[str, Any], agent_container: AgentContainer, remote_agent: str) -> Any:
        """
        Sends a message (JSON string) to the remote endpoint 

        Args:
            msg (str): A JSON string representing the request payload.
        """

        organization = agent_container.get_organization()
        namespace = agent_container.get_namespace()

        try:
            json_message = json.dumps(message)
            await self.gateway.publish(json_message.encode(), organization, namespace, remote_agent)
        except Exception as e:
            raise ValueError(f"Error sending message: {e}") from e

    @classmethod
    def create_error(cls, error, code) -> str:
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
        }
        msg = json.dumps(payload)
        return msg
