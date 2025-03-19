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
from agp_api.gateway.gateway_container import GatewayContainer
from agp_api.agent.agent_container import AgentContainer


class TestGatewayContainer(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for the GatewayContainer class.

    This test suite verifies the functionality of the `GatewayContainer` class,
    including its ability to connect to an AGP Gateway with retry logic.
    """

    async def setup_gateway_and_agent(self) -> tuple[GatewayContainer, AgentContainer]:
        """
        Helper method to set up GatewayContainer and AgentContainer with configuration.
        """
        gateway_container = GatewayContainer()
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

        payload = {
            "agent_id": "remote_agent",
            "input": {"messages": [{"role": "assistant", "content": "Hello, world!"}]},
            "model": "gpt-4o",
            "metadata": {"id": str(uuid.uuid4())},
            # Add the route field to emulate the REST API
            "route": "/api/v1/runs",
        }

        # Publish a message
        response = await gateway_container.publish_messsage(
            message=json.dumps(payload),
            agent_container=agent_container,
            remote_agent="server"
        )
        self.assertTrue(response)


if __name__ == "__main__":
    unittest.main()
