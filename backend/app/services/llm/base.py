from abc import ABC, abstractmethod

from app.models.risk_models import RiskValidationResult


class LLMProvider(ABC):
    """Abstract LLM provider: returns structured RiskValidationResult only."""

    @abstractmethod
    async def validate_clause(
        self,
        clause_text: str,
        category_definition: str,
    ) -> RiskValidationResult:
        """
        Validate a clause against a category definition.

        Implementations MUST return a RiskValidationResult (validated JSON), never raw text.
        """
        raise NotImplementedError