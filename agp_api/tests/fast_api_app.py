"""
FastAPI Test Application Module

This module provides a test FastAPI application for the AGP API service.
It defines a single endpoint for run creation that validates incoming 
requests and returns structured responses.

The module is intended for testing API interactions with the run creation
endpoint without requiring a full server deployment.

Functions:
    create_app(): Creates and returns a configured FastAPI application instance

Dependencies:
    - fastapi: Web framework for building the API
    - models: Contains the RunCreateStateless Pydantic model for request validation
f
"""

from http import HTTPStatus
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from models import RunCreateStateless


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
            raise ValueError("The input field should be a dictionary.")

        # Retrieve the 'messages' list from the 'input' dictionary.
        messages = input_field.get("messages")
        if not isinstance(messages, list) or not messages:
            raise ValueError("The input.messages field should be a non-empty list.")

        # Payload to send to autogen server at /runs endpoint
        response_payload = {
            "agent_id": agent_id,
            "output": [{"role": "assistant", "content": "Hi!"}],
            "model": "gpt-4o",
            "metadata": {"id": message_id},
        }

        return JSONResponse(content=response_payload, status_code=HTTPStatus.OK)

    return app
