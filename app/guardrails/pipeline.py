"""
Connects the DispatchRequest guardrail to the LLM client.

COMMIT 2.5 UPGRADE — what changed and why:
---------------------------------------------
Commit 2's GuardrailRejection only stored the raw Pydantic ValidationError.
That is fine for a developer reading a traceback, but it is NOT fine for a
caller that wants to show a dispatcher a clean error message, or an API
that wants to return a JSON list of "which fields failed and why". Reading
raw Pydantic error dicts every time is repetitive and easy to get wrong.

This upgrade adds ONE new method, `as_field_errors()`, that converts the
raw Pydantic error into a simple, repeatable list of
{"field": ..., "message": ...} dictionaries. Any caller — a test, a CLI
script, a future API layer — can call this one method instead of reaching
into Pydantic's internals themselves.

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
    """
    Raised when a dispatch request fails validation.

    Stores the original Pydantic ValidationError (for developers who want
    the full detail) AND exposes a simpler, structured version via
    as_field_errors() (for callers who just want "which field, what went
    wrong" without touching Pydantic directly).
    """

    def __init__(self, validation_error: ValidationError):
        self.validation_error = validation_error
        super().__init__(str(validation_error))

    def as_field_errors(self) -> list[dict]:
        """
        Convert the raw Pydantic error into a simple list like:
            [{"field": "incident_id", "message": "String should match pattern..."}]

        Pydantic's own .errors() method returns a "loc" tuple such as
        ("incident_id",) for a normal field, or () (empty) for a
        model-level cross-field error. We handle both cases below so this
        method never crashes, even for the cross-field HIGH-priority rule.
        """
        field_errors = []
        for error in self.validation_error.errors():
            field_name = error["loc"][0] if error["loc"] else "request"
            field_errors.append({"field": field_name, "message": error["msg"]})
        return field_errors


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
