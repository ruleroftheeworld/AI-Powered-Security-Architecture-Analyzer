#Fast api entry point for AI security assurance analyser backend

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from database import fetch_architecture, init_db, insert_architecture, update_architecture_extraction, update_architecture_graph, insert_graph_log
from schemas import ArchitectureRequest, ArchitectureResponse, ExtractionResult, Graph
from llm import extract_architecture
from graph import build_graph
from retrieval.vector_store import index_guidance

import json
import time

@asynccontextmanager
async def lifespan(app: FastAPI):
    #initialise resources on startup
    init_db()
    index_guidance()
    yield

app = FastAPI(
    title = "AI Security Assurance Analyser",
    description = "Backend API for storing and retrieving AI architecture descriptions.",
    version = "1.0.0",
    lifespan = lifespan,
)

@app.get("/", summary="Health check")
async def root() -> str:
    """Return a simple liveness message."""
    return "AI Security Architecture Analyzer Backend Running"
 
 
@app.post(
    "/architecture",
    response_model=ArchitectureResponse,
    status_code=201,
    summary="Submit an architecture for analysis",
)
async def create_architecture(payload: ArchitectureRequest) -> ArchitectureResponse:
    """
    Accept an architecture description, persist it to the database,
    and return the newly created record.
 
    - **architecture_text**: Plain-text description of the system architecture.
    """
    record = insert_architecture(payload.architecture_text)
    return ArchitectureResponse(**record)
 
 
@app.get(
    "/architecture/{id}",
    response_model=ArchitectureResponse,
    summary="Retrieve a stored architecture",
)
async def get_architecture(id: str) -> ArchitectureResponse:
    """
    Return the architecture record identified by *id*.
 
    Raises **404** if no record with that UUID exists.
    """
    record = fetch_architecture(id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture with id '{id}' not found.",
        )
    return ArchitectureResponse(**record)

@app.post(
    "/extract/{id}",
    response_model=ExtractionResult,
    summary="Run LLM extraction on a stored architecture",
)
async def extract_architecture_by_id(id: str) -> ExtractionResult:
    """
    Retrieve the architecture record for *id*, pass its text through the LLM
    extraction pipeline, validate the result, and return it as a structured
    :class:`ExtractionResult`.
 
    Flow:
        1. Fetch the architecture record from the database (404 if missing).
        2. Call ``extract_architecture()`` from the LLM layer.
        3. Validate and coerce the returned dict with Pydantic.
        4. Return the structured result.
 
    Raises:
        **404** – architecture record not found.
        **422** – LLM returned a response that does not match the schema.
        **500** – unexpected error during LLM extraction.
    """
    # fetch stored architecture
    record = fetch_architecture(id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture with id '{id}' not found.",
        )
 
    #  run LLM extraction
    try:
        raw_extraction: dict = extract_architecture(record["architecture_text"])
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"LLM extraction failed: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during extraction: {exc}",
        ) from exc
    
    extraction_json = json.dumps(raw_extraction)
    update_architecture_extraction(id, extraction_json)

 
    # validate with Pydantic and return
    return ExtractionResult(architecture_id=id, **raw_extraction)

@app.post(
    "/graph/{id}",
    response_model=Graph,
    summary="Build and return a knowledge graph for an architecture",
)
async def construct_graph(id: str) -> Graph:
    """
    Retrieve the stored extraction for the architecture identified by *id*,
    build a knowledge graph from it, and return the graph with normalized
    nodes and typed edges.
    
    Flow:
        1. Fetch the extraction result for *id* (404 if missing).
        2. Call ``build_graph()`` to construct the knowledge graph.
        3. Validate and return the structured Graph schema.
    
    Graph construction rules:
        Nodes:
            - Each extracted item becomes a node with a normalized ID.
            - Node types: component, auth, datastore, external, endpoint, 
                         sensitive, internet (auto-created for public endpoints).
            - IDs are normalized (lowercase, spaces → underscores, deduplicated).
        
        Edges:
            - component → component: "calls" (mesh between components)
            - component → datastore: "reads_writes"
            - component → auth: "authenticates"
            - component → external: "integrates_with"
            - endpoint → internet: "exposed_to"
        
        Determinism:
            - Nodes and edges are always returned in sorted order.
            - No duplicate nodes or edges.
    
    Args:
        id: UUID of the architecture record.
    
    Returns:
        Graph object with normalized nodes and typed edges.
    
    Raises:
        **404** – architecture record or extraction not found.
        **422** – graph construction failed (invalid extraction data).
        **500** – unexpected error during graph construction.
    """
    
    # Fetch the stored architecture
    architecture_record = fetch_architecture(id)
    if architecture_record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Architecture with id '{id}' not found.",
        )
    
    if architecture_record.get("graph"):
        graph_dict = json.loads(architecture_record["graph"])
        node_count = len(graph_dict.get("nodes",[]))
        edge_count = len(graph_dict.get("edges", []))
        insert_graph_log(id,"fetch", node_count, edge_count, duration_ms = 0)
        return Graph(**graph_dict)

    extraction_json = architecture_record.get("extraction")
    if not extraction_json:
        raise HTTPException(status_code=404, detail=f"No extraction stored for architecture '{id}'.")

    extraction_data = json.loads(extraction_json)

    # Build the knowledge graph
    start_time = time.time()
    try:
        graph = build_graph(extraction_data, id)
    except (ValueError, KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Graph construction failed: {exc}",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during graph construction: {exc}",
        ) from exc
    
    duration_ms = int((time.time() - start_time) * 1000)

    graph_json = graph.json()
    update_architecture_graph(id, graph_json)
    insert_graph_log(id, "build", len(graph.nodes), len(graph.edges), duration_ms)

    return graph