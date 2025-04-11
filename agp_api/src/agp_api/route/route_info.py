"""
Module: route_info.py

This module defines the RouteInfo dataclass, which encapsulates essential route details
within an organization's namespace. Its primary purpose is to provide a structured representation
of a route using the attributes organization, namespace, and remote_agent, along with a custom
hash method to facilitate its use in hashed collections.

Classes:
    RouteInfo: Represents a route with the following attributes:
        - organization (str): Identifier for the organization.
        - namespace (str): Logical grouping for routes.
        - remote_agent (str): Identifier for the remote agent.
"""

from dataclasses import dataclass


@dataclass
class RouteInfo:
    """
    Information about a route.

    Attributes:
        organization (str): The identifier for the organization.
        namespace (str): The routing namespace that groups related routes.
        remote_agent (str): Represents the remote agent associated with the route.
    """

    organization: str
    namespace: str
    remote_agent: str

    def __hash__(self):
        """
        Return the hash value of the RouteInfo object by hashing a tuple composed of the organization,
        namespace, and remote_agent. This ensures that each RouteInfo instance can be used reliably in
        hashed collections (e.g., sets and dictionaries).

        Returns:
            int: The computed hash value.
        """
        return hash((self.organization, self.namespace, self.remote_agent))
