# AI Security Architecture Analyzer

A specialized prototype designed to bridge the gap between software design and security auditing. This tool automates the extraction of security-relevant metadata from high-level architecture descriptions to build a structured **Security Knowledge Graph**, enabling early-stage risk assessment before a single line of application code is written.

---

## Overview
The **AI Security Architecture Analyzer** transforms unstructured architectural descriptions into a formal, queryable representation. By utilizing Large Language Models (LLMs) for entity extraction and a deterministic graph construction pipeline, the system identifies critical components, trust boundaries, and data flows essential for threat modeling.

### Key Capabilities
* **Automated Extraction:** Identifies components, data stores, auth mechanisms, and exposure points from raw text.
* **Graph-Based Modeling:** Maps architectural relationships into a typed directed graph.
* **Structured Validation:** Ensures data integrity using Pydantic schemas for all extraction stages.
* **Security Focus:** Prioritizes the identification of sensitive data paths and public-facing endpoints.

---

## System Architecture

The project is built with a modular, pipeline-oriented backend to ensure explainability and reproducibility.



### 1. Backend Core
* **FastAPI:** High-performance asynchronous API framework.
* **Pydantic:** Strict schema enforcement for data validation and normalization.
* **SQLite:** Persistent storage for architecture versions and analysis results.

### 2. LLM Extraction Layer
The system leverages a hosted **Gemini** model with a zero-temperature configuration to ensure deterministic and structured outputs.
* **Schema Enforcement:** Prompt engineering techniques are used to force the model to adhere strictly to defined security taxonomies.
* **Entity Recognition:** Specifically tuned to extract:
    * **Components:** Logic units (e.g., Node API, React Frontend).
    * **Auth Mechanisms:** Security protocols (e.g., JWT, OAuth2).
    * **Data Stores:** Persistence layers (e.g., PostgreSQL, S3 Buckets).
    * **Public Endpoints:** Entry points (e.g., Admin Dashboards, Webhooks).

### 3. Knowledge Graph Construction
The extraction results are converted into a formal graph structure to support future path-finding and risk-propagation analysis.

**Node Types:** `component`, `auth`, `datastore`, `external`, `endpoint`, `sensitive`, `internet`.
**Edge Types:** * `calls`: Service-to-service communication.
* `reads_writes`: Data persistence interactions.
* `authenticates`: Security boundary verification.
* `exposed_to`: Network exposure (e.g., Endpoint → Internet).

---

## Implementation Details

### Current Workflow
1.  **Ingestion:** User submits a high-level architecture string via the REST API.
2.  **Processing:** The LLM parses the text into a structured JSON payload.
3.  **Normalization:** Node IDs are lowercased, deduplicated, and typed.
4.  **Graph Generation:** Adjacency lists (nodes and edges) are generated and stored.
5.  **Persistence:** The raw description, extracted entities, and final graph are saved in SQLite for historical analysis.

### API Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/architecture` | Submit a new architecture description for analysis. |
| `POST` | `/extract/{id}` | Trigger LLM extraction for a specific ID. |
| `POST` | `/graph/{id}` | Construct and retrieve the Knowledge Graph. |
| `GET` | `/architecture/{id}` | Fetch the stored state of an analysis. |

---

## Project Structure
```text
backend/
├── main.py          # FastAPI application & Route definitions
├── database.py      # SQLite session and Model management
├── schemas.py       # Pydantic models for strict data typing
├── llm.py           # Gemini integration & Extraction logic
├── graph.py         # Deterministic graph construction logic
└── ai_security.db   # Local persistence layer
```

---

## Getting Started

### Prerequisites
* Python 3.10+
* Gemini API Key

### Installation & Setup
1.  **Clone the repository and install dependencies:**
    ```bash
    pip install fastapi uvicorn pydantic python-dotenv google-genai
    ```
2.  **Configure Environment:**
    Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_actual_api_key_here
    ```
3.  **Launch the Server:**
    ```bash
    uvicorn main:app --reload
    ```
4.  **Access Documentation:**
    Navigate to `http://localhost:8000/docs` to interact with the API via Swagger UI.

---

## Roadmap
The project is designed for extensibility, with the following modules currently in development:
* **Security Gap Detection:** Rule-based heuristics to flag missing authentication or direct database exposure.
* **Readiness Scoring:** Weighted risk assessment based on component sensitivity.
* **Standards Mapping:** Aligning identified risks with **OWASP ASVS** and **CWE** taxonomies.
* **Graph Visualization:** A React-based frontend using **React Flow** for interactive threat modeling.
