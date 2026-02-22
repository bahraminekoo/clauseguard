
RISK_CATEGORIES = {
    "UNLIMITED_LIABILITY": {
        "name": "Unlimited Liability",
        "definition": "Any clause that imposes liability without a clear cap or limitation on damages.",
    },
    "INDEMNIFICATION": {
        "name": "Indemnification",
        "definition": "Obligation to indemnify the other party for broad categories of losses or third-party claims.",
    },
    "TERMINATION": {
        "name": "Termination for Convenience",
        "definition": "Allows unilateral termination without cause, short notice, or without compensation.",
    },
}


def get_category_definition(key: str) -> str:
    category = RISK_CATEGORIES.get(key)
    if not category:
        raise KeyError(f"Unknown risk category: {key}")
    return category["definition"]
