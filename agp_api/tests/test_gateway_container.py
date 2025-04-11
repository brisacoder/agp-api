"""
Unit tests for the GatewayContainer class.

This module contains tests for the `GatewayContainer` class, specifically
testing its ability to connect to an agent container with retries.

Note: The AGP Gateway must be running and accessible at the configured endpoint
for these tests to pass.
"""

import json
import time
import unittest
from http import HTTPStatus
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI

from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer

from fast_api_app import create_app
from payload import Payload


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
        gateway_container.set_fastapi_app(create_app())
        agent_container = AgentContainer()
        gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)
        return gateway_container, agent_container

    @patch(
        "agp_api.gateway.gateway_container.Gateway.remove_route", new_callable=AsyncMock
    )
    @patch(
        "agp_api.gateway.gateway_container.Gateway.set_route", new_callable=AsyncMock
    )
    async def test_routes(self, mock_set_route, mock_remove_route):
        """
        Test registering and deregistering routes with the gateway.

        This test verifies that the gateway can properly register and
        deregister routes for remote agents.
        """
        gateway_container, _ = await self.setup_gateway_and_agent()

        organization = "test_org"
        namespace = "test_namespace"
        remote_agent = "test_agent"

        # Test registering a route
        await gateway_container.register_route(organization, namespace, remote_agent)
        mock_set_route.assert_awaited_once_with(
            organization=organization, namespace="test_namespace", agent="test_agent"
        )

        # Verify route exists in the route manager
        self.assertTrue(
            gateway_container.route_manager.route_exists(
                organization=organization,
                namespace=namespace,
                remote_agent=remote_agent,
            )
        )

        # Test deregistering a route
        result = await gateway_container.deregister_route(
            organization, namespace, remote_agent
        )
        self.assertTrue(result)
        mock_remove_route.assert_awaited_once_with(
            organization=organization, namespace="test_namespace", agent="test_agent"
        )

        self.assertFalse(
            gateway_container.route_manager.route_exists(
                organization=organization,
                namespace=namespace,
                remote_agent=remote_agent,
            )
        )

        # Test deregistering a non-existent route
        result = await gateway_container.deregister_route(
            organization, namespace, "non_existent"
        )
        self.assertFalse(result)

    async def test_initialization_without_parameters(self):
        """
        Test initialization of GatewayContainer with no parameters.
        """
        gateway_container = GatewayContainer()
        self.assertIsNotNone(gateway_container.gateway)
        self.assertIsNone(gateway_container.fastapi_app)

    async def test_initialization_with_parameters(self):
        """
        Test initialization of GatewayContainer with provided parameters.
        """
        mock_gateway = MagicMock()
        fastapi_app_init = MagicMock()
        gateway_container = GatewayContainer(
            gateway=mock_gateway, fastapi_app=fastapi_app_init
        )
        self.assertEqual(gateway_container.gateway, mock_gateway)
        self.assertEqual(gateway_container.fastapi_app, fastapi_app_init)

    async def test_set_fastapi_app(self):
        """
        Test setting the FastAPI app.
        """
        gateway_container = GatewayContainer()
        fastapi_app_set = MagicMock()
        gateway_container.set_fastapi_app(fastapi_app_set)
        self.assertEqual(gateway_container.get_fastapi_app(), fastapi_app_set)

    async def test_set_get_gateway(self):
        """
        Test setting and getting the gateway.
        """
        gateway_container = GatewayContainer()
        new_gateway = MagicMock()
        gateway_container.set_gateway(new_gateway)
        self.assertEqual(gateway_container.get_gateway(), new_gateway)

    async def test_create_gateway(self):
        """
        Test the create_gateway method.
        """
        gateway_container = GatewayContainer()
        with patch("agp_api.gateway.gateway_container.Gateway") as MockGateway:
            mock_instance = MagicMock()
            MockGateway.return_value = mock_instance
            created_gateway = gateway_container.create_gateway()
            self.assertEqual(gateway_container.gateway, created_gateway)

    async def test_set_config(self):
        """
        Test setting configuration on the gateway.
        """
        custom_endpoint = "http://custom:8000"
        gateway_container = GatewayContainer()
        mock_config = MagicMock()
        gateway_container.gateway = MagicMock()
        # Initialize config attribute on the gateway mock
        gateway_container.gateway.config = mock_config
        gateway_container.set_config(endpoint=custom_endpoint, insecure=True)
        self.assertEqual(gateway_container.gateway.config.endpoint, custom_endpoint)
        self.assertTrue(gateway_container.gateway.config.insecure)

    async def test_process_message_error_cases(self):
        """
        Test error handling in the process_message method.

        This test verifies proper error handling for various invalid payload cases.
        """
        gateway_container = GatewayContainer()

        response = gateway_container.process_message(Payload.no_agent_id)
        response_data = json.loads(response)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["error"], HTTPStatus.UNPROCESSABLE_ENTITY)

        response = gateway_container.process_message(Payload.no_route)
        response_data = json.loads(response)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["error"], HTTPStatus.NOT_FOUND)

        # There is no FastAPI app set, so this should raise an exception
        response = gateway_container.process_message(Payload.generic)
        response_data = json.loads(response)
        self.assertIn("message", response_data)
        self.assertEqual(response_data["error"], HTTPStatus.INTERNAL_SERVER_ERROR)

    async def test_connect_retry_timeout(self):
        """
        Test timeout behavior in connect_with_retry method.

        This test verifies that the method correctly times out after the specified duration.
        """

        gateway_container, agent_container = await self.setup_gateway_and_agent()

        # Test that connect_with_retry times out after a short duration
        start_time = time.time()

        with self.assertRaises(TimeoutError):
            await gateway_container.connect_with_retry(
                agent_container=agent_container,
                max_duration=2,  # Short timeout for testing
                initial_delay=0.5,
            )

        elapsed_time = time.time() - start_time
        # Verify that timeout happened (with some margin)
        self.assertGreaterEqual(elapsed_time, 1.8)
        self.assertLessEqual(elapsed_time, 4)  # Allow some leeway for test execution

    async def test_create_error_method(self):
        """
        Test the create_error class method.

        This test verifies that error messages are correctly formatted.
        """
        # Test with all parameters
        error_msg = "Test error message"
        error_code = HTTPStatus.BAD_REQUEST
        agent_id = "test_agent"

        error_response = json.loads(
            GatewayContainer.create_error(error_msg, error_code, agent_id)
        )

        self.assertEqual(error_response["message"], error_msg)
        self.assertEqual(error_response["error"], error_code)
        self.assertEqual(error_response["agent_id"], agent_id)

        # Test with None agent_id
        error_response = json.loads(
            GatewayContainer.create_error(error_msg, error_code, None)
        )
        self.assertEqual(error_response["agent_id"], None)

    async def test_server_with_invalid_payload(self):
        """
        Test server processing of invalid payloads.

        This test verifies that the server correctly handles and responds to invalid payloads.
        """
        gateway_container, _ = await self.setup_gateway_and_agent()

        # Test process_message directly
        response = gateway_container.process_message(Payload.no_messages)

        # Since we're returning the payload on exceptions, we should get the original payload
        self.assertEqual(
            json.loads(response)["message"],
            "The input.messages field should be a non-empty list.",
        )


if __name__ == "__main__":
    unittest.main()
