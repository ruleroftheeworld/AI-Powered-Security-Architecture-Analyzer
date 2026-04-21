from pydantic import BaseModel, Field
from typing import List, Optional

class GuidanceSnippet(BaseModel):
    id: str = Field(..., description="Unique ID (e.g. snip-001)")
    source: str = Field(..., description="Source standard (OWASP ASVS 5.0 or CWE)")
    control: Optional[str] = Field(None, description="Control ID from ASVS")
    category: str = Field(..., description="High-level category")
    title: str = Field(..., description="Concise title")
    description: str = Field(..., description="Atomic guidance text")
    cwe: Optional[str] = Field(None, description="CWE reference if applicable")
    severity: Optional[str] = Field(None, description="Critical | High | Medium | Low")
    mitigation: Optional[str] = Field(None, description="Recommended mitigation")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")