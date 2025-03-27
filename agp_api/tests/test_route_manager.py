"""
Unit tests for the RouteManager class.

This module contains tests to verify the functionality of the RouteManager class,
which manages routing information for agents within an organization and namespace
hierarchy.
"""

import unittest
from agp_api.route.route_manager import RouteManager


class TestRouteManager(unittest.TestCase):
    """Test suite for the RouteManager class."""

    def setUp(self):
        """Set up a RouteManager instance for testing."""
        self.route_manager = RouteManager()

    def tearDown(self):
        """Clean up after each test."""
        # Clear any routes that might have been added
        self.route_manager = None

    def test_init(self):
        """Test that the RouteManager initializes with empty collections."""
        # Create a fresh instance to test initialization specifically
        route_manager = RouteManager()

        # Verify the public interface indicates empty state
        self.assertIsNone(route_manager.get_route_by_remote_agent("test_agent"))
        self.assertEqual(route_manager.get_routes_by_organization("test_org"), [])

    def test_add_route(self):
        """Test adding a route to the RouteManager."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Verify the route was added using public methods
        route_info = self.route_manager.get_route_by_remote_agent("agent1")
        self.assertIsNotNone(route_info)
        self.assertEqual(route_info.organization, "org1")
        self.assertEqual(route_info.namespace, "ns1")
        self.assertEqual(route_info.remote_agent, "agent1")

        # Check organization routes
        org_routes = self.route_manager.get_routes_by_organization("org1")
        self.assertEqual(len(org_routes), 1)
        self.assertEqual(org_routes[0].remote_agent, "agent1")

        # Clean up
        try:
            self.route_manager.delete_route("org1", "ns1", "agent1")
        except Exception as e:
            print(f"Cleanup failed: {e}")

    def test_add_route_overwrite(self):
        """
        Test that adding a route with an existing remote_agent overwrites it.
        """
        # This ensures that the `add_route` method updates the route in both
        # the `_routes_by_agent` and `_routes_by_org` collections.
        # Add initial route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Verify initial route using public methods
        initial_route = self.route_manager.get_route_by_remote_agent("agent1")
        self.assertEqual(initial_route.organization, "org1")
        self.assertEqual(initial_route.namespace, "ns1")

        # Add a different route with the same remote_agent to overwrite
        self.route_manager.add_route("org2", "ns2", "agent1")

        # Verify the route was overwritten using public methods
        route_info = self.route_manager.get_route_by_remote_agent("agent1")
        self.assertEqual(route_info.organization, "org2")
        self.assertEqual(route_info.namespace, "ns2")
        routes_in_org1_ns1 = self.route_manager.get_routes_by_organization_namespace(
            "org1", "ns1"
        )
        self.assertEqual(len(routes_in_org1_ns1), 0)
        org1_ns1_routes = self.route_manager.get_routes_by_organization_namespace(
            "org1", "ns1"
        )
        self.assertEqual(len(org1_ns1_routes), 0)

        # Check that it's in the new org/namespace
        routes_in_org2_ns2 = self.route_manager.get_routes_by_organization_namespace(
            "org2", "ns2"
        )
        self.assertEqual(len(routes_in_org2_ns2), 1)
        self.assertEqual(routes_in_org2_ns2[0].remote_agent, "agent1")

        # Clean up
        self.route_manager.delete_route("org2", "ns2", "agent1")

    def test_delete_route_existing(self):
        """Test deleting an existing route."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Delete the route
        result = self.route_manager.delete_route("org1", "ns1", "agent1")

        # Verify the result and that the route was removed
        self.assertTrue(result)
        self.assertIsNone(self.route_manager.get_route_by_remote_agent("agent1"))
        org1_ns1_routes = self.route_manager.get_routes_by_organization_namespace(
            "org1", "ns1"
        )
        self.assertEqual(len(org1_ns1_routes), 0)

    def test_delete_route_nonexistent(self):
        """Test deleting a non-existent route."""
        # Delete a route that doesn't exist
        result = self.route_manager.delete_route("org1", "ns1", "nonexistent")
        self.assertFalse(result)

    def test_delete_route_cleanup(self):
        """Test that deleting a route cleans up empty dictionaries."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Delete the route
        self.route_manager.delete_route("org1", "ns1", "agent1")

        # Verify the route was removed and organization is empty
        self.assertIsNone(self.route_manager.get_route_by_remote_agent("agent1"))

        # Verify that namespace is empty by checking no routes exist for org1/ns1
        org1_ns1_routes = self.route_manager.get_routes_by_organization_namespace(
            "org1", "ns1"
        )
        self.assertEqual(len(org1_ns1_routes), 0)

        # Verify that organization is empty by checking no routes exist for org1
        org1_routes = self.route_manager.get_routes_by_organization("org1")
        self.assertEqual(len(org1_routes), 0)

    def test_get_routes_by_organization(self):
        """Test getting all routes for an organization."""
        # Add multiple routes
        self.route_manager.add_route("org1", "ns1", "agent1")
        self.route_manager.add_route("org1", "ns2", "agent2")
        self.route_manager.add_route("org2", "ns1", "agent3")

        # Get routes for org1
        routes = self.route_manager.get_routes_by_organization("org1")

        # Verify the returned routes
        self.assertEqual(len(routes), 2)
        remote_agents = [route.remote_agent for route in routes]
        self.assertIn("agent1", remote_agents)
        self.assertIn("agent2", remote_agents)
        self.assertNotIn("agent3", remote_agents)

        # Clean up
        self.route_manager.delete_route("org1", "ns1", "agent1")
        try:
            self.route_manager.delete_route("org1", "ns2", "agent2")
        except Exception as e:
            print(f"Cleanup failed: {e}")
        try:
            self.route_manager.delete_route("org2", "ns1", "agent3")
        except Exception as e:
            print(f"Cleanup failed: {e}")

    def test_get_routes_by_organization_nonexistent(self):
        """Test getting routes for a non-existent organization."""
        # Get routes for non-existent org
        routes = self.route_manager.get_routes_by_organization("nonexistent")

        # Verify an empty list is returned
        self.assertEqual(routes, [])

    def test_get_routes_by_organization_namespace(self):
        """Test getting all routes for an organization and namespace."""
        # Add multiple routes
        self.route_manager.add_route("org1", "ns1", "agent1")
        self.route_manager.add_route("org1", "ns1", "agent2")
        self.route_manager.add_route("org1", "ns2", "agent3")

        # Get routes for org1/ns1
        routes = self.route_manager.get_routes_by_organization_namespace("org1", "ns1")

        # Verify the returned routes
        self.assertEqual(len(routes), 2)
        remote_agents = [route.remote_agent for route in routes]
        self.assertIn("agent1", remote_agents)
        self.assertIn("agent2", remote_agents)
        self.assertNotIn("agent3", remote_agents)

        # Clean up
        self.route_manager.delete_route("org1", "ns1", "agent1")
        self.route_manager.delete_route("org1", "ns1", "agent2")
        self.route_manager.delete_route("org1", "ns2", "agent3")

    def test_get_routes_by_organization_namespace_nonexistent(self):
        """Test getting routes for a non-existent org/namespace combination."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Get routes for non-existent combinations
        routes1 = self.route_manager.get_routes_by_organization_namespace(
            "nonexistent", "ns1"
        )
        routes2 = self.route_manager.get_routes_by_organization_namespace(
            "org1", "nonexistent"
        )

        # Verify empty lists are returned
        self.assertEqual(routes1, [])
        self.assertEqual(routes2, [])

        # Clean up
        self.route_manager.delete_route("org1", "ns1", "agent1")

    def test_get_route_by_remote_agent(self):
        """Test looking up a route by remote agent."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Look up the route
        route_info = self.route_manager.get_route_by_remote_agent("agent1")

        # Verify the returned route info
        self.assertIsNotNone(route_info)
        self.assertEqual(route_info.organization, "org1")
        self.assertEqual(route_info.namespace, "ns1")
        self.assertEqual(route_info.remote_agent, "agent1")

        # Clean up
        self.route_manager.delete_route("org1", "ns1", "agent1")

    def test_get_route_by_remote_agent_nonexistent(self):
        """Test looking up a non-existent remote agent."""
        # Look up a non-existent route
        route_info = self.route_manager.get_route_by_remote_agent("nonexistent")

        # Verify None is returned
        self.assertIsNone(route_info)

    def test_delete_route_wrong_org_namespace(self):
        """Test deleting a route with correct agent but wrong org/namespace."""
        # Add a route
        self.route_manager.add_route("org1", "ns1", "agent1")

        # Try to delete with wrong organization/namespace
        result = self.route_manager.delete_route("wrong_org", "ns1", "agent1")
        self.assertFalse(result)

        # Verify route still exists
        route_info = self.route_manager.get_route_by_remote_agent("agent1")
        self.assertIsNotNone(route_info)
        self.assertEqual(route_info.organization, "org1")
        self.assertEqual(route_info.namespace, "ns1")

        # Clean up properly
        self.route_manager.delete_route("org1", "ns1", "agent1")


if __name__ == "__main__":
    unittest.main()
