"""
Route Management Module for Agent Routing System

This module provides functionality for managing routing information for agents
within a hierarchical organization and namespace structure. It enables tracking,
looking up, and managing agent routes across different organizational boundaries.

The module organizes routes in a three-level hierarchy:
- Organization: Top-level grouping (e.g., company or department)
- Namespace: Sub-grouping within an organization (e.g., project or team)
- Remote Agent: Individual agent identifier

Key components:
- RouteManager: Central class that maintains routing tables and provides CRUD operations
- RouteInfo: Data structure storing route information (imported from .route_info)

Routes can be looked up by organization, namespace, or directly by agent identifier,
allowing for flexible routing in distributed agent systems.

Typical usage:
    route_mgr = RouteManager()
    route_mgr.add_route("my_org", "dev_team", "agent123")
    route_info = route_mgr.get_route_by_remote_agent("agent123")
"""

import logging
from typing import Dict, List, Optional

from .route_info import RouteInfo

logger = logging.getLogger(__name__)


class RouteManager:
    """
    Manages routes for agents in an organization and namespace hierarchy.

    This class provides methods to add, delete, and retrieve routes based on
    organization, namespace, and remote agent information.
    """

    def __init__(self) -> None:
        """
        Initializes the RouteManager with empty route collections.
        """
        self._routes_by_remote_agent: Dict[str, RouteInfo] = {}
        self._routes_by_organization_and_namespace: Dict[
            str, Dict[str, Dict[str, RouteInfo]]
        ] = {}

    def add_route(self, organization: str, namespace: str, remote_agent: str) -> None:
        """
        Adds a route to the manager for the specified organization, namespace, and remote agent.

        This method first checks if there is an existing route for the given remote_agent.
        If one is found, it is removed to avoid duplicates. Then, a new route is created
        and stored in both the _routes_by_agent dictionary and the _routes_by_org nested dictionary.

        Args:
            organization (str): The identifier for the organization containing the route.
            namespace (str): The identifier for the namespace within the organization.
            remote_agent (str): The identifier for the remote agent to route.

        Returns:
            None
        """
        existing_route = self._routes_by_remote_agent.get(remote_agent)
        if existing_route and not isinstance(existing_route, RouteInfo):
            raise ValueError(
                f"Invalid RouteInfo object for remote agent '{remote_agent}'"
            )
        if existing_route:
            logger.info(
                "Replacing existing route for : '%s/%s' -> '%s'",
                existing_route.organization,
                existing_route.namespace,
                remote_agent,
            )
            self.delete_route(
                existing_route.organization, existing_route.namespace, remote_agent
            )
        route_info = RouteInfo(organization, namespace, remote_agent)
        self._routes_by_remote_agent[remote_agent] = route_info
        if organization not in self._routes_by_organization_and_namespace:
            self._routes_by_organization_and_namespace[organization] = {}
        if namespace not in self._routes_by_organization_and_namespace[organization]:
            self._routes_by_organization_and_namespace[organization][namespace] = {}
        self._routes_by_organization_and_namespace[organization][namespace][
            remote_agent
        ] = route_info

    def delete_route(
        self, organization: str, namespace: str, remote_agent: str
    ) -> bool:
        """
        Delete a route for the given organization and namespace associated with a specific remote agent.

        This method checks if the provided remote agent exists within the stored routes.
        If the remote agent exists, it validates that the provided organization and namespace match
        those saved for the remote agent. If there is a mismatch or if the remote agent doesn't exist,
        the method returns False. Otherwise, it removes the route information and returns True.

        Args:
            organization (str): The identifier for the organization.
            namespace (str): The identifier for the namespace.
            remote_agent (str): The identifier for the remote agent whose route should be removed.
        """
        if remote_agent not in self._routes_by_remote_agent:
            logger.warning(
                "Delete route failed: Remote agent '%s' not found", remote_agent
            )
            return False
        actual_route = self._routes_by_remote_agent[remote_agent]
        actual_org = actual_route.organization
        actual_namespace = actual_route.namespace
        if organization != actual_org or namespace != actual_namespace:
            logger.warning(
                f"Delete route failed: Organization/namespace mismatch for '{remote_agent}'. "
                f"Expected: '{actual_org}/{actual_namespace}', got: '{organization}/{namespace}'"
            )
            return False
        self._routes_by_remote_agent.pop(remote_agent)
        if (
            actual_org in self._routes_by_organization_and_namespace
            and actual_namespace
            in self._routes_by_organization_and_namespace[actual_org]
        ):
            self._routes_by_organization_and_namespace[actual_org][
                actual_namespace
            ].pop(remote_agent, None)
            if not self._routes_by_organization_and_namespace[actual_org][
                actual_namespace
            ]:
                self._routes_by_organization_and_namespace[actual_org].pop(
                    actual_namespace
                )
            if not self._routes_by_organization_and_namespace[actual_org]:
                self._routes_by_organization_and_namespace.pop(actual_org)
        logger.info(
            "Route deleted: '%s' from '%s/%s'", remote_agent, organization, namespace
        )
        return True

    def get_routes_by_organization(self, organization: str) -> List[RouteInfo]:
        """
        Retrieves all routes associated with the specified organization.

        Args:
            organization (str): The identifier or name of the organization.

        Returns:
            List[RouteInfo]: A list of RouteInfo objects corresponding to the organization's routes.
        """
        if organization not in self._routes_by_organization_and_namespace:
            return []
        routes: List[RouteInfo] = []
        for namespace_dict in self._routes_by_organization_and_namespace[
            organization
        ].values():
            routes.extend(namespace_dict.values())
        return routes

    def _organization_namespace_exists(self, organization: str, namespace: str) -> bool:
        """
        Checks if the given organization and namespace exist in the routing structure.

        Args:
            organization (str): The identifier for the organization.
            namespace (str): The namespace within the organization.

        Returns:
            bool: True if both organization and namespace exist, False otherwise.
        """
        return (
            organization in self._routes_by_organization_and_namespace
            and namespace in self._routes_by_organization_and_namespace[organization]
        )

    def get_routes_by_organization_namespace(
        self, organization: str, namespace: str
    ) -> List[RouteInfo]:
        """
        Retrieve a list of RouteInfo objects for a specified organization and namespace.

        This method checks whether the provided organization exists in the internal routes
        mapping and whether the specified namespace is present under that organization.
        If either the organization or the namespace is not found, it returns an empty list.

        Args:
            organization (str): The identifier for the organization.
            namespace (str): The namespace within the organization.

        Returns:
            List[RouteInfo]: A list of RouteInfo objects for the specified organization and namespace.
        """
        if not self._organization_namespace_exists(organization, namespace):
            return []
        return list(
            self._routes_by_organization_and_namespace[organization][namespace].values()
        )

    def get_route_by_remote_agent(self, remote_agent: str) -> Optional[RouteInfo]:
        """
        Retrieves the RouteInfo associated with the specified remote agent.

        Parameters:
            remote_agent (str): The identifier for the remote agent.

        Returns:
            Optional[RouteInfo]: The RouteInfo corresponding to the given remote agent if found,
            otherwise None.
        """
        route_info = self._routes_by_remote_agent.get(remote_agent)
        if route_info and not isinstance(route_info, RouteInfo):
            logger.error(
                "Inconsistent data: Invalid RouteInfo object for remote agent '%s'",
                remote_agent,
            )
            return None
        return route_info

    def route_exists(
        self, organization: str, namespace: str, remote_agent: str
    ) -> bool:
        """
        Determines whether a route exists for the specified organization, namespace, and remote agent.

        This method first retrieves the route information associated with the given remote agent from the internal dictionary.
        If no route is found, the method returns False. Otherwise, it checks that the route's organization and namespace match
        the provided parameters.

        Parameters:
            organization (str): The organization's identifier to match against the route.
            namespace (str): The namespace to match against the route.
            remote_agent (str): The identifier for the remote agent whose route is being checked.
        """
        route_info = self._routes_by_remote_agent.get(remote_agent)
        if not route_info or not isinstance(route_info, RouteInfo):
            logger.warning(
                "Invalid or missing RouteInfo for remote agent '%s'", remote_agent
            )
            return False
        is_matching_route = (
            route_info.organization == organization
            and route_info.namespace == namespace
        )
        return is_matching_route
