from typing import Any, Dict, List, Optional, Set

def build_retrieval_query(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic query builder for Phase-4 vector retrieval.
    
    Expected graph format (produced by Phase 3):
    {
        "nodes": [
            {"id": str, "type": "component|datastore|auth|external|endpoint|sensitive|internet", ...},
            ...
        ],
        "edges": [
            {"source": str, "target": str, "type": "calls|reads_writes|authenticates|integrates_with|exposed_to", ...},
            ...
        ]
    }
    
    Returns:
    {
        "query_text": str,      # concise, normalized, high-signal text for embed_query()
        "filters": dict | None  # Chroma-compatible where filter (category/severity) or None
    }
    """
    nodes: List[Dict[str, Any]] = graph.get("nodes", [])
    edges: List[Dict[str, Any]] = graph.get("edges", [])

    # Extract presence of high-signal node types (case-insensitive)
    node_types: Set[str] = {n.get("type", "").strip().lower() for n in nodes if isinstance(n, dict)}

    # Extract edge types for relational signals
    edge_types: Set[str] = {e.get("type", "").strip().lower() for e in edges if isinstance(e, dict)}

    # High-signal risk flags (deterministic, no ML)
    has_internet = (
        "internet" in node_types
        or "exposed_to" in edge_types
    )
    has_auth = (
        "auth" in node_types
        or "authenticates" in edge_types
    )
    has_datastore = (
        "datastore" in node_types
        or "reads_writes" in edge_types
    )
    has_external = (
        "external" in node_types
        or "integrates_with" in edge_types
    )
    has_sensitive = "sensitive" in node_types

    # Build query_text – stable ordering + deduplication
    risk_phrases: List[str] = []
    if has_internet:
        risk_phrases.append("internet-facing public exposure")
    if has_auth:
        risk_phrases.append("authentication authorization session")
    if has_datastore:
        risk_phrases.append("datastore database reads-writes")
    if has_external:
        risk_phrases.append("external integration webhook")
    if has_sensitive:
        risk_phrases.append("sensitive data encryption")

    # Deterministic: deduplicate + stable alphabetical sort
    risk_phrases = sorted(set(risk_phrases))

    if risk_phrases:
        query_text = "secure architecture with " + " and ".join(risk_phrases)
    else:
        query_text = "general software architecture security review"

    # Build optional Chroma metadata filters (2026 Chroma syntax: simple dict = AND equality)
    filter_dict: Dict[str, str] = {}
    if has_auth:
        filter_dict["category"] = "Authentication"
    if has_sensitive or has_internet or has_external:
        filter_dict["severity"] = "High"

    filters: Optional[Dict[str, str]] = filter_dict if filter_dict else None

    return {
        "query_text": query_text,
        "filters": filters,
    }