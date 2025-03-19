"""
Unit tests for the GatewayContainer class.

This module contains tests for the `GatewayContainer` class, specifically
testing its ability to connect to an agent container with retries.

Note: The AGP Gateway must be running and accessible at the configured endpoint
for these tests to pass.
"""

import asyncio
from http import HTTPStatus
import unittest

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from pydantic import BaseModel

from agp_api.agent.agent_container import AgentContainer
from agp_api.gateway.gateway_container import GatewayContainer

from .models import RunCreateStateless


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
            "output": [{"role": "assistant", "content": "Hello, world!"}],
            "model": "gpt-4o",
            "metadata": {"id": message_id},
        }

        # In a real application, additional processing (like starting a background task) would occur here.
        return JSONResponse(content=response_payload, status_code=HTTPStatus.OK)

    return app


class TestHTTPReinjection(unittest.IsolatedAsyncioTestCase):
    """
    Test suite for the GatewayContainer class.

    This test suite verifies the functionality of the `GatewayContainer` class,
    including its ability to connect to an AGP Gateway with retry logic.
    """

    def setUp(self):
        """Set up the FastAPI server in a background thread."""
        self.app = create_app()
        self.client = TestClient(self.app)




if __name__ == "__main__":
    unittest.main()
