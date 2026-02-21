from pydantic import BaseModel

class RiskValidationResult(BaseModel):
    risk_detected: bool
    confidence: float
    explanation: str
    category: str
    page: int
    clause_text: str