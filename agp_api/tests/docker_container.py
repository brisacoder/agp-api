"""
Helper class to manage Docker containers for testing.

This class provides functionality to start and stop Docker containers
for testing purposes, particularly focused on the Gateway container.

Attributes:
    client (docker.client.DockerClient): Docker client instance.
    containers (dict): Dictionary of managed containers keyed by name.

Example:
    >>> container_mgr = DockerContainerManager()
    >>> container = container_mgr.start_gateway(password="test_password")
    >>> # Run your tests...
    >>> container_mgr.stop_all()  # Clean up after testing

Note:
    Requires the Docker Python SDK and a running Docker daemon.
"""

import os
import socket
import time
import docker


class DockerContainerManager:
    """Helper class to manage Docker containers for testing"""

    def __init__(self):
        self.client = docker.from_env()
        self.containers = {}

    def start_gateway(self, password="dummy_password", config_path=None, port=46357):
        """Start the Gateway container if not running."""
        if self.is_port_in_use(port):
            return None

        if config_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(current_dir, "data", "server-config.yaml")

        container = self.client.containers.run(
            "ghcr.io/agntcy/agp/gw:0.3.10",
            command="/gateway --config /config.yaml",
            environment={"PASSWORD": password},
            volumes={config_path: {"bind": "/config.yaml", "mode": "ro"}},
            ports={f"{port}/tcp": port},
            detach=True,
            auto_remove=True,
        )

        # Wait for container to start
        for _ in range(10):
            if self.is_port_in_use(port):
                break
            time.sleep(1)
        else:
            container.stop()
            raise RuntimeError("Gateway container failed to start")

        self.containers["gateway"] = container
        return container

    def stop_all(self):
        """Stop all containers started by this manager."""
        for name, container in self.containers.items():
            try:
                container.stop()
                print(f"Stopped {name} container")
            except Exception as e:
                print(f"Error stopping {name} container: {e}")
        self.containers = {}

    @staticmethod
    def is_port_in_use(port, host="127.0.0.1"):
        """Check if a port is in use."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex((host, port)) == 0
