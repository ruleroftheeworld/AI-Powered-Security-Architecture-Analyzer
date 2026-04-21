import pytest
from retrieval.vector_store import index_guidance, retrieve_guidance, get_collection

def test_indexing_loads_correct_count():
    index_guidance()
    collection = get_collection()
    assert collection.count() == 25

def test_retrieval_returns_relevant_snippet_for_architecture_query():
    results = retrieve_guidance("secure authentication architecture for microservices", top_k=3)
    assert len(results) >= 1
    # At least one result should be authentication-related
    assert any("Authentication" in r["metadata"].get("category", "") for r in results)

def test_metadata_filtering_works():
    results = retrieve_guidance("password storage", top_k=2, filters={"category": "Authentication"})
    assert len(results) > 0
    assert all(r["metadata"]["category"] == "Authentication" for r in results)

def test_cwe_filter_example():
    results = retrieve_guidance("xss prevention", top_k=1, filters={"cwe": "CWE-79"})
    assert len(results) > 0