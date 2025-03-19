.. agp-api documentation master file, created by
   sphinx-quickstart on Wed Mar 19 10:24:08 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

agp-api documentation
======================

Welcome to the official documentation for `agp-api`!

`agp-api` is a Python-based API framework designed to create clients and servers for the Agent Gateway Protocol efficiently. It provides a robust and 
scalable architecture for processing messages, interacting with remote services, and handling agent workflows.

Features
--------
- 📌 Supports structured logging with JSON output.
- 🚀 Built-in FastAPI integration for handling API requests.
- 🔄 Stateless message processing with LangGraph.
- 📊 Configurable and extensible agent framework.

Installation
------------
To install `agp-api`, run:

.. code-block:: bash

   pip install agp-api

Usage Example
-------------
Here's a simple example of how to create a client and publish a message using `agp-api`:

.. code-block:: python

   from agp_api.gateway.gateway_container import GatewayContainer, AgentContainer

   gateway_container = GatewayContainer()
   gateway_container.set_fastapi_app(create_app())
   agent_container = AgentContainer()
   gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)

   # Call connect_with_retry
   conn_id = await gateway_container.connect_with_retry(
      agent_container=agent_container,
      max_duration=10,
      initial_delay=1,
      remote_agent="server",
   )

   # Assert that the connection ID is returned
   self.assertIsInstance(conn_id, int)

   # Publish a message
   _ = await gateway_container.publish_messsage(
      message=json.dumps(self.payload),
      agent_container=agent_container,
      remote_agent="server",
   )

Further Reading
---------------
- 📜 Check out the `API Reference <modules.html>`_ for detailed module documentation.
- 🎯 Learn about `Pydantic Models <pydantic_models.html>`_ for structured data handling.
- 🔗 Visit the official `GitHub repository <https://github.com/brisacoder/agp-api>`_ for source code and contributions.



.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules

