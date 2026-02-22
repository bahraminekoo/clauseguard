
VALIDATION_SYSTEM_PROMPT = """
You are a deterministic contract risk validator.
You MUST respond ONLY with valid JSON matching this schema:
{
  "risk_detected": boolean,
  "confidence": number between 0 and 1,
  "explanation": string
}
Do not include any text outside JSON. If unsure, set risk_detected to false and confidence to 0.0.
"""


def build_validation_prompt(clause_text: str, category_definition: str) -> list[dict]:
    """Return chat messages for the LLM provider (provider decides how to send)."""
    return [
        {"role": "system", "content": VALIDATION_SYSTEM_PROMPT.strip()},
        {
            "role": "user",
            "content": f"Category definition:\n{category_definition}\n\nClause:\n{clause_text}",
        },
    ]
