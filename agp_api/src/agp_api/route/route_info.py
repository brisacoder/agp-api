from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

@dataclass
class RouteInfo:
    """Information about a route."""
    organization: str
    namespace: str
    remote_agent: str
    
    def __hash__(self):
        return hash((self.organization, self.namespace, self.remote_agent))