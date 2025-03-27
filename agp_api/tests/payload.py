"""
Payload module providing predefined test payloads for API testing.

Usage:
    These payloads can be used directly in test functions to verify API behavior:
    ```
    response = client.post("/api/v1/runs", json=Payload.generic)
    ```

    during testing. Each payload's metadata contains a unique UUID.
"""

import uuid


class Payload:
    """
    Payload class providing predefined test payloads for API testing.

    This class contains various test payload examples used for testing API endpoints,
    including valid and invalid scenarios. These payloads emulate the structure
    expected by the API's run endpoints.

    Class Attributes:
        generic (dict): Standard valid payload with basic message content.
        github_input (dict): GitHub-specific input parameters.
        github (dict): Complete payload for GitHub-related operations.
        no_messages (dict): Invalid payload missing the required messages field.
        no_agent_id (dict): Invalid payload missing the required agent_id field.

    Note:
        All payloads include a "route" field to emulate REST API routing
        during testing.
    """

    generic = {
        "agent_id": "remote_agent",
        "input": {"messages": [{"role": "assistant", "content": "Hello, world!"}]},
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        # Add the route field to emulate the REST API
        "route": "/api/v1/runs",
    }

    github_input = {
        "github": {
            "repo_url": "https://github.com/brisacoder/agp-api",
            "github_token": "some_token",
            "branch": "main",
        }
    }

    github = {
        "agent_id": "remote_agent",
        "input": github_input,
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        # Add the route field to emulate the REST API
        "route": "/api/v1/runs",
    }

    # Create an invalid payload (missing messages field)
    no_messages = {
        "agent_id": "remote_agent",
        "input": {},  # Missing messages field
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
        "route": "/api/v1/runs",
    }

    # Test with missing agent_id
    no_agent_id = {
        "input": {"messages": [{"role": "assistant", "content": "Hello"}]},
        "route": "/api/v1/runs",
    }

    no_route = {
        "agent_id": "remote_agent",
        "input": {"messages": [{"role": "assistant", "content": "Hello, world!"}]},
        "model": "gpt-4o",
        "metadata": {"id": str(uuid.uuid4())},
    }
