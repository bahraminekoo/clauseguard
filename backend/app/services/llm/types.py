
VALIDATION_SYSTEM_PROMPT = """
You are a deterministic contract risk validator. Respond ONLY with a single JSON object exactly matching this schema:
{
  "risk_detected": boolean,
  "confidence": number between 0 and 1,
  "explanation": non-empty string,
  "category": string,
  "page": integer or null,
  "clause_text": string
}
Rules:
- Output JSON only, no prose before or after.
- If unsure, set risk_detected=false, confidence=0.0, explanation="No risk detected".
- Use page=null when unknown. Keep clause_text exactly as provided.
- Do NOT add fields beyond the schema.
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
