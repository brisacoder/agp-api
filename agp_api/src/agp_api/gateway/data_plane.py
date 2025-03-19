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

