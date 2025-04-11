"""Module containing the AgpAgent class for managing agent details."""


class AgentContainer:
    """
    Represents an agent with configuration details.

    Attributes:
        organization (str): The organization associated with the agent.
        namespace (str): The namespace of the agent.
        local_agent (str): The local agent identifier.

    Public Methods:
        get_details() -> dict: Returns a dictionary with the agent's details.
        set_details(organization: str, namespace: str, local_agent: str) -> None: Updates the agent details.
        get_organization() -> str: Retrieves the organization of the agent.
        get_namespace() -> str: Retrieves the namespace of the agent.
        get_local_agent() -> str: Retrieves the local agent identifier.
    """

    def __init__(self, organization: str = "cisco", namespace: str = "default", local_agent: str = "server"):
        """
        Initialize the AgentContainer with optional organization, namespace, and local_agent.

        Parameters:
            organization (str): The name of the organization. Defaults to "cisco".
            namespace (str): The namespace associated with the agent. Defaults to "default".
            local_agent (str): The identifier for the local agent. Defaults to "server".
        """
        self.organization = organization
        self.namespace = namespace
        self.local_agent = local_agent

    def get_details(self) -> dict:
        """
        Retrieve details of the agent, including its organization, namespace, and local agent.

        Returns:
            dict: A dictionary with the following keys:
                - "organization": The organization associated with the agent.
                - "namespace": The namespace of the agent.
                - "local_agent": The local agent identifier.
        """
        return {
            "organization": self.organization,
            "namespace": self.namespace,
            "local_agent": self.local_agent,
        }

    def set_details(self, organization: str, namespace: str, local_agent: str) -> None:
        """
        Set the details for organization, namespace, and local agent.

        Parameters:
            organization (str): The name of the organization.
            namespace (str): The namespace associated with the agent.
            local_agent (str): The identifier for the local agent.

        Returns:
            None
        """
        self.organization = organization
        self.namespace = namespace
        self.local_agent = local_agent

    def get_organization(self) -> str:
        """
        Retrieve the organization associated with the agent.

        Returns:
            str: The organization of the agent.
        """
        return self.organization

    def get_namespace(self) -> str:
        """
        Retrieve the namespace associated with the agent.

        Returns:
            str: The namespace of the agent.
        """
        return self.namespace

    def get_local_agent(self) -> str:
        """
        Retrieve the local agent identifier.

        Returns:
            str: The local agent identifier.
        """
        return self.local_agent