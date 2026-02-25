
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend"


class AnalyzeRequest(BaseModel):
    # Backward compatibility: support old text field OR new doc_id/query_text
    text: str | None = None
    doc_id: str | None = None
    query_text: str | None = None
    category_keys: list[str] | None = None


class RiskFinding(BaseModel):
    category: str
    confidence: float
    page: int | None = None
    explanation: str
    clause_text: str


class AnalyzeResponse(BaseModel):
    findings: list[RiskFinding]


class UploadResponse(BaseModel):
    doc_id: str
