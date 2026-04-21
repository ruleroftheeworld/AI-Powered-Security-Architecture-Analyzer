# pydantic v2 schemas for request and response

from pydantic import BaseModel, Field

from typing import List

class ArchitectureRequest(BaseModel):
    #Payload accemtped by POST /architecture

    architecture_text: str = Field(
        ...,
        min_length = 1,
        description = "Raw architecture description to be stored and later analysed.",
    )

class ArchitectureResponse(BaseModel):
    # response returend by POST /architecture and GET /architecture/{id}.

    id: str = Field(..., description="UUID of the stored record.")
    architecture_text: str = Field(..., description="The submitted architecture text.")
    created_at: str = Field(..., description="ISO-8601 UTC timestamp of creation.")
    status: str = Field(..., description="Processing status of the record.")

class ExtractionResult(BaseModel):
    """
    Structured security extraction produced by the LLM layer.
 
    Returned by POST /extract/{id}.
    Each field is a list of short descriptive strings identified in the
    architecture text by the LLM.
    """
 
    architecture_id: str = Field(
        ...,
        description="UUID of the source architecture record.",
    )
    components: List[str] = Field(
        default_factory=list,
        description="Internal services, microservices, or modules.",
    )
    auth: List[str] = Field(
        default_factory=list,
        description="Authentication and authorisation mechanisms.",
    )
    data_stores: List[str] = Field(
        default_factory=list,
        description="Databases, caches, object stores, and queues.",
    )
    external_services: List[str] = Field(
        default_factory=list,
        description="Third-party APIs, SaaS integrations, and cloud services.",
    )
    sensitive_data: List[str] = Field(
        default_factory=list,
        description="PII, secrets, credentials, financial data, or health data.",
    )
    public_endpoints: List[str] = Field(
        default_factory=list,
        description="Routes, ports, or interfaces exposed to external clients.",
    )

class GraphNode(BaseModel):
    """
    A single node in the security architecture graph.
    
    Attributes:
        id: Unique normalized identifier (lowercase, underscores, deduplicated).
        label: Human-readable label extracted from architecture description.
        type: Node classification:
               - "component": internal service/microservice/module
               - "auth": authentication/authorisation mechanism
               - "datastore": database/cache/queue
               - "external": third-party API/SaaS/cloud service
               - "endpoint": public route/port/interface
               - "sensitive": sensitive data classification
               - "internet": external internet (auto-generated for public endpoints)
    """
    id: str = Field(
        ...,
        description="Normalized node identifier (lowercase, underscores, no duplicates).",
    )
    label: str = Field(
        ...,
        description="Human-readable label from the architecture description.",
    )
    type: str = Field(
        ...,
        description="Node type: component, auth, datastore, external, endpoint, sensitive, internet.",
    )
 
 
class GraphEdge(BaseModel):
    """
    A directed edge representing a relationship in the architecture graph.
    
    Attributes:
        source: ID of the source node.
        target: ID of the target node.
        type: Relationship type:
               - "calls": component/service calling another
               - "reads_writes": service accessing a datastore
               - "authenticates": service using authentication mechanism
               - "integrates_with": service integrating with external service
               - "exposed_to": endpoint exposed to the internet
    """
    source: str = Field(
        ...,
        description="Source node ID.",
    )
    target: str = Field(
        ...,
        description="Target node ID.",
    )
    type: str = Field(
        ...,
        description="Edge type: calls, reads_writes, authenticates, integrates_with, exposed_to.",
    )
 
 
class Graph(BaseModel):
    """
    Complete security architecture graph extracted from the LLM analysis.
    
    Returned by POST /graph/{id}.
    
    Attributes:
        architecture_id: UUID of the source architecture record.
        nodes: List of all nodes in the graph.
        edges: List of all directed edges in the graph.
    """
    architecture_id: str = Field(
        ...,
        description="UUID of the source architecture record.",
    )
    nodes: List[GraphNode] = Field(
        default_factory=list,
        description="All nodes in the security architecture graph.",
    )
    edges: List[GraphEdge] = Field(
        default_factory=list,
        description="All directed edges representing relationships in the graph.",
    )