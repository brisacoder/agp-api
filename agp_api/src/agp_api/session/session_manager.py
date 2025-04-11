"""

"""

import logging
from typing import Dict, List, Optional

import agp_bindings

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages sessions for agents in an organization and namespace hierarchy.

    This class provides methods to add, delete, and retrieve routes based on
    organization, namespace, and remote agent information.
    """

    def __init__(self) -> None:
        """
        Initializes the RouteManager with empty route collections.
        """

    async def create_fire_and_forget_session(self, gateway: agp_bindings.PyGateway) -> agp_bindings.PyFireAndForgetConfiguration:
        """
        Creates a fire-and-forget session configuration for the Gateway instance.

        Returns:
            PyFireAndForgetConfiguration: The fire-and-forget session configuration.
        """
        self.session = await gateway.create_ff_session(
            agp_bindings.PyFireAndForgetConfiguration()
        )
        return self.session
