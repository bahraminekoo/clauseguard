from pydantic import BaseModel, field_validator


class RiskValidationResult(BaseModel):
    risk_detected: bool
    explanation: str
    category: str
    page: int | None = None
    clause_text: str

    model_config = {
        "extra": "ignore",
    }

    @field_validator("explanation", "category", "clause_text")
    @classmethod
    def no_empty_strings(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v