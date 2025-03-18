"""Module for Agent Gateway API."""

from __future__ import annotations

import asyncio
import json
import logging
import time

from http import HTTPStatus
from fastapi import HTTPException
from fastapi.testclient import TestClient

from ..agent.agent_container import AgentContainer
from .gateway_container import GatewayContainer


logger = logging.getLogger(__file__)


def create_error(error, code) -> str:
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


def process_message(payload: dict) -> str:
    """
    Parse and process the incoming payload message.
    This function decodes the incoming payload, validates essential fields, extracts required information,
    and forwards the request to a FastAPI app. It then returns the server's response or handles errors appropriately.
    Parameters:
        payload (dict): A dictionary containing the message details. Expected keys include:
            - "agent_id": Identifier for the agent; must be non-empty.
            - "route": The API route to which the message should be sent.
            - "input": A dictionary with a key "messages", which is a non-empty list where each element is a dictionary.
                       The last message in this list should contain the human input under the "content" key.
            - "metadata": (Optional) A dictionary that may contain an "id" for tracking purposes.
    Returns:
        str: A JSON string representing the reply. This is either the successful response from the FastAPI server
             when a status code 200 is returned, or a JSON encoded error message if validation fails.
    Raises:
        Exception: If the FastAPI server returns a status code other than 200, an exception with the status code
                   and error details is raised.

    """
    logging.debug("Decoded payload: %s", payload)

    # Extract assistant_id from the payload
    agent_id = payload.get("agent_id")
    logging.debug("Agent id: %s", agent_id)

    # Validate that the assistant_id is not empty.
    if not payload.get("agent_id"):
        return create_error("agent_id is required and cannot be empty.", 422)

    # Extract the route from the message payload.
    # This step is done to emulate the behavior of the REST API.
    route = payload.get("route")
    if not route:
        return create_error("Not Found.", 404)

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
        return create_error("The 'input' field should be a dictionary.", 500)

    # Retrieve the 'messages' list from the 'input' dictionary.
    messages = input_field.get("messages")
    if not isinstance(messages, list) or not messages:
        return create_error(
            "The 'input.messages' field should be a non-empty list.", 500
        )

    # Access the last message in the list.
    last_message = messages[-1]
    if not isinstance(last_message, dict):
        return create_error(
            "The first element in 'input.messages' should be a dictionary.", 500
        )

    # Extract the 'content' from the first message.
    human_input_content = last_message.get("content")
    if human_input_content is None:
        return create_error(
            "Missing 'content' in the first message of 'input.messages'.", 500
        )

    fastapi_app = GatewayContainer.get_fastapi_app()
    if fastapi_app is None:
        logger.error("FastAPI app is not available")
        return create_error("Internal server error", 500)
    # We send all messages to graph

    client = TestClient(fastapi_app)
    try:
        response = client.post(route, json=payload)
        response.raise_for_status()

        if response.status_code == HTTPStatus.OK:
            return json.dumps(response.json())
        else:
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


