"""
Session Type Module

This module defines the SessionType enum which represents different communication patterns
that can be used within the API. Each session type corresponds to a distinct communication
paradigm with different characteristics:

- FIRE_AND_FORGET: One-way message delivery with no response expected. Useful for
  logging, notifications, or when acknowledgment isn't required.

- PUBSUB: Publisher-Subscriber pattern where messages are broadcast to multiple
  subscribers. Enables one-to-many message distribution.

- REQUEST_REPLY: Synchronous request-response pattern where a reply is expected for
  each request. Useful for typical API calls requiring immediate feedback.

- STREAMING: Continuous stream of data in one or both directions. Appropriate for
  real-time data feeds, file transfers, or ongoing event streams.

The module provides utility methods for working with session types, including
validation, searching, and listing capabilities.
"""

from enum import Enum, auto
from typing import List, Optional


class SessionType(Enum):
    """
    Enum representing different types of sessions.

    FIRE_AND_FORGET: One-way message delivery with no response expected
    PUBSUB: Publisher-Subscriber pattern where messages are broadcast to subscribers
    REQUEST_REPLY: Request-response pattern where a reply is expected for each request
    STREAMING: Continuous stream of data in one or both directions
    """

    FIRE_AND_FORGET = auto()
    PUBSUB = auto()
    REQUEST_REPLY = auto()
    STREAMING = auto()

    @classmethod
    def find_by_name(cls, name: str) -> Optional["SessionType"]:
        """
        Find a session type by its name (case-insensitive).

        Args:
            name: The name of the session type to find

        Returns:
            The SessionType if found, None otherwise
        """
        name = name.upper()
        for session_type in cls:
            if session_type.name == name:
                return session_type
        return None

    @classmethod
    def list_all(cls) -> List["SessionType"]:
        """
        List all available session types.

        Returns:
            A list of all SessionType values
        """
        return list(cls)

    @classmethod
    def get_names(cls) -> List[str]:
        """
        Get a list of all session type names.

        Returns:
            A list of session type names as strings
        """
        return [session_type.name for session_type in cls]

    @classmethod
    def is_valid_name(cls, name: str) -> bool:
        """
        Check if a given name is a valid session type.

        Args:
            name: The name to check

        Returns:
            True if the name corresponds to a valid session type, False otherwise
        """
        return cls.find_by_name(name) is not None

    def is_synchronous(self) -> bool:
        """
        Check if the session type is synchronous (expects a response).

        Returns:
            True for REQUEST_REPLY, False for other types
        """
        return self == SessionType.REQUEST_REPLY

    def is_streaming(self) -> bool:
        """
        Check if the session type supports streaming data.

        Returns:
            True for STREAMING, False for other types
        """
        return self == SessionType.STREAMING

    def __str__(self) -> str:
        """String representation of the session type."""
        return self.name

    def __repr__(self) -> str:
        """Official string representation of the session type."""
        return f"SessionType.{self.name}"
