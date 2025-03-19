"""
Unit tests for the GatewayContainer class.

This module contains tests for the `GatewayContainer` class, specifically
testing its ability to connect to an agent container with retries.

Note: The AGP Gateway must be running and accessible at the configured endpoint
for these tests to pass.
"""

import asyncio
import json
import unittest
import uuid
from http import HTTPStatus

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from models import RunCreateStateless

from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer


def create_app():
    """Creates and configures a FastAPI application with a single POST endpoint.
    The application includes a '/api/v1/runs' endpoint that processes run creation requests.
    It validates the incoming payload structure and returns a formatted response.
    Returns:
        FastAPI: A configured FastAPI application instance with the following endpoint:
            - POST /api/v1/runs: Creates a new run with the provided payload
    Raises:
        ValueError: If the input payload structure is invalid:
            - When 'input' field is not a dictionary
            - When 'input.messages' is not a non-empty list
    Example payload:
        {
            "agent_id": "some_agent_id",
            "metadata": {"id": "message_id"},
            "input": {
                "messages": [...]
    """
    app = FastAPI()

    @app.post("/api/v1/runs")
    def create_run(body: RunCreateStateless):
        payload = body.model_dump()

        # Extract agent_id from the payload
        agent_id = payload.get("agent_id")

        message_id = ""
        # Validate the metadata section: ensure that metadata.id exists if provided.
        if (metadata := payload.get("metadata", None)) is not None:
            message_id = metadata.get("id")

        input_field = payload.get("input")
        if not isinstance(input_field, dict):
            raise ValueError("The 'input' field should be a dictionary.")

        # Retrieve the 'messages' list from the 'input' dictionary.
        messages = input_field.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("The 'input.messages' field should be a non-empty list.")

        # Payload to send to autogen server at /runs endpoint
        response_payload = {
            "agent_id": agent_id,
            "output": [{"role": "assistant", "content": "Hi!"}],
            "model": "gpt-4o",
            "metadata": {"id": message_id},
        }

        return JSONResponse(content=response_payload, status_code=HTTPStatus.OK)

    return app


class TestGatewayContainer(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for the GatewayContainer class.

    This test suite verifies the functionality of the `GatewayContainer` class,
    including its ability to connect to an AGP Gateway with retry logic.
    """

    payload = {
        "agent_id": "remote_agent",
        "input": {"messages": [{"role": "assistant", "content": "Hello, world!"}]},
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        # Add the route field to emulate the REST API
        "route": "/api/v1/runs",
    }

    async def setup_gateway_and_agent(self) -> tuple[GatewayContainer, AgentContainer]:
        """
        Helper method to set up GatewayContainer and AgentContainer with configuration.
        """
        gateway_container = GatewayContainer()
        gateway_container.set_fastapi_app(create_app())
        agent_container = AgentContainer()
        gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)
        return gateway_container, agent_container

    async def test_server_connect(self):
        """
        Test the `connect_with_retry` method of GatewayContainer.

        This test verifies that the `connect_with_retry` method successfully
        establishes a connection to an agent container and returns a valid
        connection ID.

        Note: The AGP Gateway must be running and accessible at
        http://127.0.0.1:46357 for this test to pass.
        """
        gateway_container, agent_container = await self.setup_gateway_and_agent()

        # Call connect_with_retry
        conn_id = await gateway_container.connect_with_retry(
            agent_container=agent_container, max_duration=10, initial_delay=1
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(conn_id, int)

    async def test_client_connect(self):
        """
        Test the `connect_with_retry` method of GatewayContainer.

        This test verifies that the `connect_with_retry` method successfully
        establishes a connection to an agent container and returns a valid
        connection ID.

        Note: The AGP Gateway must be running and accessible at
        http://127.0.0.1:46357 for this test to pass.
        """

        gateway_container, agent_container = await self.setup_gateway_and_agent()

        # Call connect_with_retry
        conn_id = await gateway_container.connect_with_retry(
            agent_container=agent_container,
            max_duration=10,
            initial_delay=1,
            remote_agent="server",
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(conn_id, int)

    async def test_start_server(self):
        """
        Test the `connect_with_retry` method of GatewayContainer.

        This test verifies that the `connect_with_retry` method successfully
        establishes a connection to an agent container and returns a valid
        connection ID.

        Note: The AGP Gateway must be running and accessible at
        http://127.0.0.1:46357 for this test to pass.
        """
        gateway_container, agent_container = await self.setup_gateway_and_agent()

        # Call connect_with_retry
        conn_id = await gateway_container.connect_with_retry(
            agent_container=agent_container, max_duration=10, initial_delay=1
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(conn_id, int)

        server_task = asyncio.create_task(
            gateway_container.start_server(agent_container=agent_container)
        )
        # Wait briefly to ensure the server has started
        await asyncio.sleep(1)

        try:
            server_task.cancel()
        except asyncio.CancelledError:
            pass  # Expected when the task is canceled

        try:
            await server_task
        except RuntimeError:
            pass  # Expected when the task is canceled

    async def test_publish_message(self):
        """Test the publish_message functionality of the GatewayContainer.

        This test case verifies that:
        1. A connection can be established between gateway and agent containers
        2. Messages can be published successfully through the gateway

        The test follows these steps:
        1. Sets up gateway and agent containers
        2. Establishes connection with retry mechanism
        3. Verifies connection ID is returned
        4. Publishes a test message
        5. Verifies response is received

        Returns:
            None

        Raises:
            AssertionError: If any of the test conditions fail
        """

        gateway_container, agent_container = await self.setup_gateway_and_agent()

        # Call connect_with_retry
        conn_id = await gateway_container.connect_with_retry(
            agent_container=agent_container,
            max_duration=10,
            initial_delay=1,
            remote_agent="server",
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(conn_id, int)

        # Publish a message
        _ = await gateway_container.publish_messsage(
            message=json.dumps(self.payload),
            agent_container=agent_container,
            remote_agent="server",
        )

    async def test_publish_and_receive_message(self):
        """
        Tests the publish and receive message functionality of the gateway container.
        This test verifies:
        1. Successful connection establishment between gateway and agent containers
        2. Proper server startup
        3. Message publishing functionality
        4. Correct server shutdown
        The test:
        - Sets up gateway and agent containers
        - Establishes connection with retry mechanism
        - Starts server in async task
        - Publishes test message
        - Verifies successful message delivery
        - Performs clean server shutdown
        Returns:
            None
        Raises:
            AssertionError: If connection ID is not an integer or if message publish fails
        """

        # Client
        client_gateway_container, client_agent_container = (
            await self.setup_gateway_and_agent()
        )

        # Client connection
        client_conn_id = await client_gateway_container.connect_with_retry(
            agent_container=client_agent_container,
            max_duration=10,
            initial_delay=1,
            remote_agent="server",
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(client_conn_id, int)

        # Server
        server_gateway_container, server_agent_container = (
            await self.setup_gateway_and_agent()
        )

        # Server connection
        server_conn_id = await server_gateway_container.connect_with_retry(
            agent_container=server_agent_container, max_duration=10, initial_delay=1
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(server_conn_id, int)

        # Start the server
        server_task = asyncio.create_task(
            server_gateway_container.start_server(
                agent_container=server_agent_container
            )
        )

        try:
            # Wait briefly to ensure the server has started
            await asyncio.sleep(1)

            # Publish a message
            await client_gateway_container.publish_messsage(
                message=json.dumps(self.payload),
                agent_container=client_agent_container,
                remote_agent="server",
            )
            _, recv = await client_gateway_container.gateway.receive()
            response_data = json.loads(recv.decode("utf8"))

            expected_metadata_id = self.payload["metadata"]["id"]

            # Expected response data structure
            expected_response = {
                "agent_id": "remote_agent",
                "output": [{"role": "assistant", "content": "Hi!"}],
                "model": "gpt-4o",
                "metadata": {"id": expected_metadata_id},
            }

            # Assert that the response data matches the expected structure
            self.assertDictEqual(response_data, expected_response)

        finally:
            # Ensure the server task is canceled and awaited
            server_task.cancel()
            try:
                await server_task
            except RuntimeError:
                pass


if __name__ == "__main__":
    unittest.main()
