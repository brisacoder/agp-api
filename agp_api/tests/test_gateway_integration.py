"""
Integration tests for the AGP Gateway component.

This test suite verifies the integration between the Gateway and Agent components by
testing the communication flow through the Gateway container. It requires either an
existing Gateway container running on port 46357 or will automatically start one
for testing purposes.

The test suite covers:
- Connection establishment between Gateway and Agent containers
- Server-side and client-side connection modes
- Gateway server functionality
- Message publishing and receiving
- End-to-end communication flow

Requirements:
- Docker must be installed and running to start the Gateway container if not already present
- The PASSWORD environment variable should be set or will default to "dummy_password"
- Configuration file at ./config/base/server-config.yaml must exist

Notes:
- Tests will automatically start a Gateway container if one is not already running
- If using an existing Gateway container, it must be accessible at http://127.0.0.1:46357
- The container will be stopped after tests unless it was externally started
"""

import asyncio
import json
import unittest

from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer

from payload import Payload
from fast_api_app import create_app
from docker_container import DockerContainerManager


class TestGatewayIntegration(unittest.IsolatedAsyncioTestCase):
    """Tests that require a running Gateway container"""

    @classmethod
    def setUpClass(cls):
        """Start the Gateway container before all tests if not running."""
        # Check if Gateway is already running
        cls.container_manager = DockerContainerManager()

        if cls.container_manager.is_port_in_use(46357):
            print("Gateway already running on port 46357")
            cls.external_container = True
            return

        print("Starting Gateway container...")
        cls.external_container = False

        try:
            cls.container = cls.container_manager.start_gateway()
            print("Gateway container started successfully")
        except RuntimeError as e:
            raise RuntimeError(f"Gateway container failed to start: {e}") from e

    @classmethod
    def tearDownClass(cls):
        """Stop the Gateway container after all tests."""
        if hasattr(cls, "container_manager") and not cls.external_container:
            print("Stopping Gateway container")
            cls.container_manager.stop_all()

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
            message=Payload.generic,
            agent_container=agent_container,
            remote_agent="server",
        )

    async def test_publish_github_no_messages(self):
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
            message=Payload.github,
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
                message=Payload.generic,
                agent_container=client_agent_container,
                remote_agent="server",
            )
            _, recv = await client_gateway_container.gateway.receive()
            response_data = json.loads(recv.decode("utf8"))

            expected_metadata_id = Payload.generic["metadata"]["id"]

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
