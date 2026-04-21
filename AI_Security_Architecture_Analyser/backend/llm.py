"""
llm.py
Structured LLM extraction layer for the AI Security Assurance Analyzer.

Provides:
    extract_architecture(text: str) -> dict

The function sends a structured prompt (with few-shot examples) to an LLM
and returns a validated JSON object matching the extraction schema.

"""

import json
import re
from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv()
# ---------------------------------------------------------------------------
# Prompt definition
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a security-focused architecture analyst.

Your job is to extract structured security-relevant information from a plain-text
description of a software architecture.

You MUST respond with ONLY a single valid JSON object — no markdown, no prose,
no code fences. The object must follow this exact schema:

{
  "components":        [],   // internal services / microservices / modules
  "auth":              [],   // authentication or authorisation mechanisms
  "data_stores":       [],   // databases, caches, object stores, queues
  "external_services": [],   // third-party APIs, SaaS integrations, cloud services
  "sensitive_data":    [],   // PII, secrets, credentials, financial data, health data
  "public_endpoints":  []    // routes, ports, or interfaces exposed to external clients
}

All values are arrays of short descriptive strings. Return empty arrays for
categories that are not mentioned or implied.

--- EXAMPLE 1 ---
Input:
"A React frontend talks to a Node.js REST API secured with JWT. User passwords and
emails are stored in PostgreSQL. The API calls Stripe for payment processing and
sends emails via SendGrid. The /api/v1/* routes are public."

Output:
{
  "components": ["React frontend", "Node.js REST API"],
  "auth": ["JWT authentication"],
  "data_stores": ["PostgreSQL"],
  "external_services": ["Stripe (payment processing)", "SendGrid (email delivery)"],
  "sensitive_data": ["user passwords", "user emails", "payment data"],
  "public_endpoints": ["/api/v1/*"]
}

--- EXAMPLE 2 ---
Input:
"A Django monolith handles web requests. Sessions are managed with Django's built-in
session framework backed by Redis. Static files are served from S3. Admin panel is
at /admin and requires staff login. Celery workers consume jobs from RabbitMQ.
No external payment provider is used."

Output:
{
  "components": ["Django monolith", "Celery workers"],
  "auth": ["Django session authentication", "staff login for admin panel"],
  "data_stores": ["Redis (session store)", "S3 (static files)", "RabbitMQ (job queue)"],
  "external_services": [],
  "sensitive_data": ["session tokens"],
  "public_endpoints": ["/admin (staff-restricted)"]
}

--- EXAMPLE 3 ---
Input:
"Microservices: Auth Service issues OAuth2 tokens, Product Service manages inventory,
Order Service processes purchases. All inter-service calls go through an internal API
Gateway. PostgreSQL per service (database-per-service pattern). Secrets stored in
HashiCorp Vault. External: Twilio for SMS OTP, AWS SES for email. Public: POST /login,
POST /register, GET /products."

Output:
{
  "components": ["Auth Service", "Product Service", "Order Service", "API Gateway"],
  "auth": ["OAuth2 token issuance", "SMS OTP via Twilio"],
  "data_stores": ["PostgreSQL (Auth Service)", "PostgreSQL (Product Service)", "PostgreSQL (Order Service)", "HashiCorp Vault (secrets)"],
  "external_services": ["Twilio (SMS OTP)", "AWS SES (email delivery)"],
  "sensitive_data": ["OAuth2 tokens", "SMS OTP codes", "secrets in Vault", "order/purchase data"],
  "public_endpoints": ["POST /login", "POST /register", "GET /products"]
}
"""

def _call_llm(prompt: str) -> str:
    """
    Send *prompt* to Gemini 2.5 Flash and return the raw text response.

    Requires:
        GEMINI_API_KEY environment variable to be set.

    Args:
        prompt: The user-facing portion of the prompt (the architecture text).

    Returns:
        A JSON string matching the extraction schema.
    """
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            temperature=0,                  # deterministic output
            response_mime_type="application/json",  # forces JSON-only response
        ),
    )

    return response.text


# ---------------------------------------------------------------------------
# Public extraction function
# ---------------------------------------------------------------------------

def extract_architecture(text: str) -> dict:
    """
    Extract structured security-relevant information from an architecture description.

    Sends *text* to the LLM using a structured few-shot prompt, parses the
    JSON response, and returns it as a Python dict.

    The returned dict always contains the following keys (values are lists of str):
        - components
        - auth
        - data_stores
        - external_services
        - sensitive_data
        - public_endpoints

    Args:
        text: Plain-text architecture description submitted by the user.

    Returns:
        A dict matching the extraction schema.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON or is
                    missing required schema keys.
    """
    # Build the user-turn prompt
    user_prompt = f"Extract security-relevant information from the following architecture description:\n\n{text}"

    # Call the LLM (mocked for now)
    raw_response: str = _call_llm(user_prompt)

    # Strip accidental markdown fences the model might emit
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_response.strip(), flags=re.MULTILINE)

    # Parse JSON
    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned invalid JSON: {exc}\nRaw response: {raw_response!r}") from exc

    # Validate required keys are present
    required_keys = {"components", "auth", "data_stores", "external_services", "sensitive_data", "public_endpoints"}
    missing = required_keys - result.keys()
    if missing:
        raise ValueError(f"LLM response is missing required keys: {missing}")

    # Ensure every value is a list (guard against malformed model output)
    for key in required_keys:
        if not isinstance(result[key], list):
            raise ValueError(f"Expected a list for key '{key}', got {type(result[key]).__name__}.")

    return result