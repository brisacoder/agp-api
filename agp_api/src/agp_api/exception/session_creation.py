"""
Module: session_creation
This module provides custom exception classes for handling errors during the session creation process in the AGP system.
Exception: AGPSessionCreationError
Raised when the creation of a session fails in the AGP system.
    message (str): A human-readable description of the error.
"""

from typing import Optional


class AGPSessionCreationError(Exception):
    """
    Exception raised when the creation of a session fails in the AGP system.

    Attributes:
        session_type (str): The type of session that failed to be created.
        message (str): Human-readable description of the error.
        original_exception (Exception, optional): The underlying exception that caused the error, if any.
    """
    def __init__(
        self,
        session_type: str,
        message: str = "Failed to create session",
        original_exception: Optional[Exception] = None,
    ):

        self.session_type = session_type
        self.message = message
        self.original_exception = original_exception
        full_message = f"{message} for session type '{session_type}'"
        if original_exception:
            full_message = f"{full_message}. Caused by: {original_exception!r}"
        super().__init__(full_message)

    def __str__(self):
        return self.args[0]

    def __repr__(self):
        return (
            f"{self.__class__.__name__}(session_type={self.session_type!r}, "
            f"message={self.message!r}, original_exception={self.original_exception!r})"
        )
