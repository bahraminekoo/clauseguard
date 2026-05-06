
VALIDATION_SYSTEM_PROMPT = """
You are a deterministic contract risk validator.

Respond ONLY with a single JSON object exactly matching this schema:

{
  "risk_detected": boolean,
  "explanation": non-empty string,
  "category": string,
  "page": integer or null,
  "clause_text": string
}

STRICT RULES:

OUTPUT FORMAT
- Output JSON only.
- No prose before or after the JSON.
- Do NOT add fields beyond the schema.
- Keep clause_text EXACTLY as provided.
- Use page=null when unknown.

DECISION STANDARD
- Only set risk_detected=true if the clause CLEARLY and EXPLICITLY matches the category definition.
- If unsure or ambiguous, return:
  risk_detected=false,
  explanation="No risk detected",
  category="NONE".

LEGAL INTERPRETATION RULES

1) UNLIMITED LIABILITY REQUIREMENT
A clause can be classified as Unlimited Liability ONLY if it explicitly creates
financial exposure such as:
- liability for damages or losses
- indemnification obligations
- compensation obligations
- payment responsibility
- reimbursement obligations
WITHOUT a clear monetary cap or limitation.

Termination rights, dismissal provisions, disciplinary actions, or employment
management clauses are NEVER Unlimited Liability unless they explicitly impose
uncapped financial damages or payment obligations.

Severity of consequences (e.g., immediate termination, misconduct, breach)
DOES NOT equal liability.

2) INDEMNIFICATION REQUIREMENT
Indemnification requires an explicit obligation to defend, indemnify,
or hold harmless another party against losses, damages, or third-party claims.

3) TERMINATION FOR CONVENIENCE
Termination for Convenience exists when one party may terminate:
- without cause, OR
- at sole discretion, OR
- for convenience,
especially where the right is unilateral or lacks balanced protections.

Termination for misconduct, breach, or cause is NOT termination for convenience.

4) NO INFERENCE RULE
Do NOT infer risk from tone, harsh wording, or legal strictness.
Risk must arise from explicit legal effect stated in the clause.

"""


def build_validation_prompt(clause_text: str, category_name: str, category_definition: str) -> list[dict]:
    return [
        {
            "role": "system",
            "content": VALIDATION_SYSTEM_PROMPT.strip(),
        },
        {
            "role": "user",
            "content": (
                f"Category: {category_name}\n\n"
                f"Category definition:\n{category_definition}\n\n"

                "VALIDATION INSTRUCTIONS:\n"
                "- Only flag risk_detected=true if the clause CLEARLY matches this category.\n"
                "- If the clause does not explicitly satisfy the definition, return:\n"
                "  risk_detected=false, "
                "explanation='No risk detected', category='NONE'.\n\n"

                "DISAMBIGUATION RULES:\n"
                "- Termination, dismissal, or employment discipline clauses are NOT Unlimited Liability\n"
                "  unless they explicitly impose uncapped financial damages or payment obligations.\n"
                "- A clause MUST mention damages, losses, liability, indemnity, compensation,\n"
                "  or financial responsibility to qualify as Unlimited Liability.\n"
                "- Termination for misconduct or breach is NOT Termination for Convenience.\n"
                "- Termination for Convenience means termination without cause or at sole discretion.\n\n"

                "Analyze ONLY the clause below.\n\n"
                f"Clause:\n{clause_text}"
            ),
        },
    ]