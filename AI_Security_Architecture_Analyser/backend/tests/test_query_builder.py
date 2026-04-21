import pytest
from retrieval.query_builder import build_retrieval_query

SAMPLE_GRAPH = {
    "nodes": [
        {"id": "ep1", "type": "endpoint"},
        {"id": "i1", "type": "internet"},
        {"id": "a1", "type": "auth"},
        {"id": "d1", "type": "datastore"},
        {"id": "s1", "type": "sensitive"},
        {"id": "e1", "type": "external"},
    ],
    "edges": [
        {"source": "ep1", "target": "i1", "type": "exposed_to"},
        {"source": "ep1", "target": "a1", "type": "authenticates"},
        {"source": "ep1", "target": "d1", "type": "reads_writes"},
        {"source": "ep1", "target": "e1", "type": "integrates_with"},
    ]
}

def test_query_text_is_deterministic_and_stable():
    result1 = build_retrieval_query(SAMPLE_GRAPH)
    result2 = build_retrieval_query(SAMPLE_GRAPH)  # same graph

    # Order of nodes/edges does not matter
    shuffled = {"nodes": SAMPLE_GRAPH["nodes"][::-1], "edges": SAMPLE_GRAPH["edges"][::-1]}
    result3 = build_retrieval_query(shuffled)

    assert result1["query_text"] == result2["query_text"] == result3["query_text"]
    assert "internet-facing public exposure" in result1["query_text"]
    assert "authentication authorization session" in result1["query_text"]
    assert "sensitive data encryption" in result1["query_text"]

def test_deduplication_works():
    duplicate_graph = {
        "nodes": SAMPLE_GRAPH["nodes"],
        "edges": SAMPLE_GRAPH["edges"] * 2  # duplicate edges
    }
    result = build_retrieval_query(duplicate_graph)
    # Still only one instance of each phrase
    assert result["query_text"].count("internet-facing") == 1

def test_filters_shape_and_logic():
    result = build_retrieval_query(SAMPLE_GRAPH)
    assert result["filters"] is not None
    assert result["filters"]["category"] == "Authentication"
    assert result["filters"]["severity"] == "High"

def test_empty_graph_fallback():
    result = build_retrieval_query({})
    assert result["query_text"] == "general software architecture security review"
    assert result["filters"] is None