"""
Connects the DispatchRequest guardrail to the LLM client.

Why this file exists: query_llm() must never be called with unvalidated
data. protected_query_llm() is the only function other code should call —
it validates first, and only calls the LLM if validation succeeds.
"""
from __future__ import annotations

from pydantic import ValidationError

from app.guardrails.schemas import DispatchRequest
from app.llm.client import query_llm

SYSTEM_PROMPT = """
You are MSI Assist AI, an emergency dispatch assistant.

Rules:
- Classify the incident priority.
- Use only the information provided.
- Do not invent missing details.
- Return a structured dispatch recommendation.
"""


class GuardrailRejection(Exception):
    """Raised when a dispatch request fails validation."""

    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        super().__init__(str(validation_error))


def protected_query_llm(data: dict) -> str:
    """
    Validate `data`, then call the LLM only if validation passes.

    If validation fails, this raises GuardrailRejection and query_llm()
    is never reached.
    """
    try:
        request = DispatchRequest(**data)
    except ValidationError as exc:
        raise GuardrailRejection(exc) from exc

    prompt = request.to_prompt_fragment()
    return query_llm(SYSTEM_PROMPT, prompt)
