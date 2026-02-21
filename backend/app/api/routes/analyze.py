
from fastapi import APIRouter

from app.api.schemas import AnalyzeRequest, AnalyzeResponse, RiskFinding


router = APIRouter(tags=["analyze"])


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(payload: AnalyzeRequest) -> AnalyzeResponse:
    text = payload.text.strip()

    findings: list[RiskFinding] = []
    if "liable" in text.lower() or "liability" in text.lower():
        findings.append(
            RiskFinding(
                category="Unlimited Liability",
                confidence=0.75,
                page=None,
                explanation="The provided text appears to reference liability without a clear limitation.",
                clause_text=text[:500],
            )
        )

    return AnalyzeResponse(findings=findings)
