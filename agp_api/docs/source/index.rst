.. agp-api documentation master file, created by
   sphinx-quickstart on Wed Mar 19 10:24:08 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

agp-api documentation
======================

Welcome to the official documentation for `agp-api`!

`agp-api` is a Python-based API framework designed to create clients and servers for the Agent Gateway Protocol efficiently. It 
provides a robust and scalable architecture for processing messages, interacting with remote services, and handling agent workflows.

Visit the `agp repository <https://github.com/agntcy/agp>`_ for more details.

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

Client Usage Example
--------------------
Here's a simple example of how to create a client and publish a message using `agp-api`:

.. code-block:: python

   local_agent = "client"

   gateway_container = GatewayContainer()
   agent_container = AgentContainer(local_agent=local_agent)
   gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)

   # Call connect_with_retry
   conn_id = await gateway_container.connect_with_retry(
      agent_container=agent_container, max_duration=10, initial_delay=1
   )

   organization = agent_container.organization
   namespace = agent_container.namespace

   # Register a route with the provided organization, namespace, and remote agent
   await gateway_container.register_route(
      organization=organization, namespace=namespace, remote_agent=remote_agent
   )

   # Publish a message with the provided payload
   _ = await gateway_container.publish_messsage(
      message=payload,
      agent_container=agent_container,
      remote_agent=remote_agent,
   )
   await gateway_container.gateway.disconnect()


Server Usage Example
--------------------
Here's a simple example of how to create a server and processing incopming messages using `agp-api`:

.. code-block:: python

   local_agent = "server"
   gateway_container = GatewayContainer()
   gateway_container.set_fastapi_app(create_app())
   agent_container = AgentContainer(local_agent=local_agent)
   gateway_container.set_config(endpoint="http://127.0.0.1:46357", insecure=True)

   # Call connect_with_retry
   conn_id = await gateway_container.connect_with_retry(
      agent_container=agent_container, max_duration=10, initial_delay=1
   )

   await gateway_container.start_server(agent_container=agent_container)

   await gateway_container.gateway.disconnect()


Further Reading
---------------
- 📜 Check out the `API Reference <modules.html>`_ for detailed module documentation.
- 🎯 Learn about `Pydantic Models <pydantic_models.html>`_ for structured data handling.
- 🔗 Visit the official `GitHub repository <https://github.com/brisacoder/agp-api>`_ for source code and contributions.



.. toctree::
   :maxdepth: 3
   :caption: Contents:

   modules

