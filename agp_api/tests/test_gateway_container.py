"""
Unit tests for the GatewayContainer class.

This module contains tests for the `GatewayContainer` class, specifically
testing its ability to connect to an agent container with retries.

Note: The AGP Gateway must be running and accessible at the configured endpoint
for these tests to pass.
"""

import unittest
from agp_api.gateway.gateway_container import GatewayContainer
from agp_api.agent.agent_container import AgentContainer


class TestGatewayContainer(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for the GatewayContainer class.

    This test suite verifies the functionality of the `GatewayContainer` class,
    including its ability to connect to an AGP Gateway with retry logic.
    """

    async def test_connect_with_retry(self):
        """
        Test the `connect_with_retry` method of GatewayContainer.

        This test verifies that the `connect_with_retry` method successfully
        establishes a connection to an agent container and returns a valid
        connection ID.

        Note: The AGP Gateway must be running and accessible at
        http://127.0.0.1:46357 for this test to pass.
        """
        # Instantiate GatewayContainer and AgentContainer
        gateway_container = GatewayContainer()
        agent_container = AgentContainer()

        # Set configuration for GatewayContainer
        gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)

        # Call connect_with_retry
        conn_id = await gateway_container.connect_with_retry(
            agent_container=agent_container, max_duration=10, initial_delay=1
        )

        # Assert that the connection ID is returned
        self.assertIsInstance(conn_id, int)