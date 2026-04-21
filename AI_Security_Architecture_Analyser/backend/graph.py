"""
graph.py

Knowledge graph construction module for the AI Security Assurance Analyzer.

Converts extracted architecture data (components, auth, data stores, etc.)
into a structured security-relevant knowledge graph with normalized nodes
and semantic relationships.

Provides:
    - normalize_id(label: str) -> str
    - build_graph(extraction: dict, architecture_id: str) -> Graph
"""

from typing import Dict, List
from schemas import Graph, GraphNode, GraphEdge


NODE_PRIORITY = {
    "component": 6,
    "auth": 7,
    "datastore": 5,
    "external": 4,
    "endpoint": 3,
    "sensitive": 2,
    "internet": 1
}

# Normalization utilities

def normalize_id(label: str) -> str:
    """
    Normalize a label into a unique node identifier.
    
    Rules:
        - Convert to lowercase
        - Replace spaces with underscores
        - Remove special characters (keep alphanumeric and underscores)
    
    Args:
        label: The human-readable label to normalize.
    
    Returns:
        Normalized identifier string.
    
    Example:
        >>> normalize_id("User Authentication Service")
        'user_authentication_service'
        >>> normalize_id("PostgreSQL (v13)")
        'postgresql_v13'
    """
    
    normalized = label.lower()
    
    normalized = normalized.replace(" ", "_")
    
    
    normalized = "".join(c if c.isalnum() or c == "_" else "" for c in normalized)
   
    normalized = normalized.strip("_")
    
    return normalized



def build_graph(extraction: dict, architecture_id: str) -> Graph:
    """
    Construct a security-focused knowledge graph from extracted architecture data.
    
    Node mapping:
        - "components" -> type="component"
        - "auth" -> type="auth"
        - "data_stores" -> type="datastore"
        - "external_services" -> type="external"
        - "public_endpoints" -> type="endpoint"
        - "sensitive_data" -> type="sensitive"
        - Auto-generated "internet" node if public endpoints exist
    
    Edge mapping:
        - component -> component: type="calls"
        - component -> datastore: type="reads_writes"
        - component -> auth: type="authenticates"
        - component -> external: type="integrates_with"
        - endpoint -> internet: type="exposed_to"
    
    Args:
        extraction: Dict with keys: components, auth, data_stores, external_services,
                    sensitive_data, public_endpoints (all values are lists of strings).
        architecture_id: UUID of the source architecture record.
    
    Returns:
        Graph: Validated Graph object with deduplicated nodes and semantic edges.
    """
    
    nodes_dict: Dict[str, GraphNode] = {}
    edges_list: List[GraphEdge] = []
    
    
    def add_node(label: str, node_type: str) -> str:
        """
        Add or retrieve a node. Returns its normalized ID.
        
        Args:
            label: Human-readable label.
            node_type: Type classification.
        
        Returns:
            Normalized node ID.
        """
        node_id = normalize_id(label)
        
        if node_id in nodes_dict:
            existing_type = nodes_dict[node_id].type
            if NODE_PRIORITY.get(node_type, 0) > NODE_PRIORITY.get(existing_type, 0):
                nodes_dict[node_id].type = node_type
        else:
            nodes_dict[node_id] = GraphNode(
                id=node_id,
                label=label,
                type=node_type,
            )
        
        return node_id
    
    
    def add_edge(source_id: str, target_id: str, edge_type: str) -> None:
        """
        Add a directed edge between two nodes.
        
        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            edge_type: Type of relationship.
        """
        edges_list.append(
            GraphEdge(
                source=source_id,
                target=target_id,
                type=edge_type,
            )
        )
    
    # Phase 1: Add all nodes from extraction
    
    # Components (internal services/microservices)
    component_ids: List[str] = []
    for component in extraction.get("components", []):
        node_id = add_node(component, "component")
        component_ids.append(node_id)
    
    # Authentication/Authorization mechanisms
    auth_ids: List[str] = []
    for auth in extraction.get("auth", []):
        node_id = add_node(auth, "auth")
        auth_ids.append(node_id)
    
    # Data stores (databases, caches, queues)
    datastore_ids: List[str] = []
    for datastore in extraction.get("data_stores", []):
        node_id = add_node(datastore, "datastore")
        datastore_ids.append(node_id)
    
    # External services (third-party APIs, SaaS)
    external_ids: List[str] = []
    for external in extraction.get("external_services", []):
        node_id = add_node(external, "external")
        external_ids.append(node_id)
    
    # Public endpoints
    endpoint_ids: List[str] = []
    for endpoint in extraction.get("public_endpoints", []):
        node_id = add_node(endpoint, "endpoint")
        endpoint_ids.append(node_id)
    
    # Sensitive data
    sensitive_ids: List[str] = []
    for sensitive in extraction.get("sensitive_data", []):
        node_id = add_node(sensitive, "sensitive")
        sensitive_ids.append(node_id)
    
    # Phase 2: Create the "internet" node if public endpoints exist
    
    internet_id = None
    if endpoint_ids:
        internet_id = add_node("Internet", "internet")
    
    # Phase 3: Add edges based on semantic rules
    
    # Rule: Component -> Component (calls)
    # Create edges between components (assume a linear call chain or mesh)
    if len(component_ids) > 1:
        for i in range(len(component_ids) - 1):
            add_edge(component_ids[i], component_ids[i + 1], "calls")
    
    # Rule: Component -> Data Store (reads_writes)
    # All components can access all data stores
    for component_id in component_ids:
        for datastore_id in datastore_ids:
            add_edge(component_id, datastore_id, "reads_writes")
    
    # Rule: Component -> Auth (authenticates)
    # All components can use authentication mechanisms
    for component_id in component_ids:
        for auth_id in auth_ids:
            add_edge(component_id, auth_id, "authenticates")
    
    # Rule: Component -> External Service (integrates_with)
    # All components can integrate with external services
    for component_id in component_ids:
        for external_id in external_ids:
            add_edge(component_id, external_id, "integrates_with")
    
    # Rule: Public Endpoint -> Internet (exposed_to)
    # All endpoints are exposed to the internet
    if internet_id:
        for endpoint_id in endpoint_ids:
            add_edge(endpoint_id, internet_id, "exposed_to")
    
    # Note: We do NOT create edges to sensitive_data nodes directly.
    # Sensitive data is tracked as a node type for visualization and analysis,
    # but relationships to it are implicit (accessed via components/datastores).
    
    # Phase 4: Construct and return the Graph
    
    return Graph(
        architecture_id=architecture_id,
        nodes=list(nodes_dict.values()),
        edges=edges_list,
    )