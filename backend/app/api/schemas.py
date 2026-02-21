
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend"


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1)


class RiskFinding(BaseModel):
    category: str
    confidence: float
    page: int | None = None
    explanation: str
    clause_text: str


class AnalyzeResponse(BaseModel):
    findings: list[RiskFinding]
