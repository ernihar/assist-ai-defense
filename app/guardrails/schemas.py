"""
Defines the DispatchRequest schema used to validate a dispatcher's incident
request before it is sent to the LLM.

COMMIT 2.5 UPGRADE — what changed and why:
---------------------------------------------
1. The character whitelist check used to live INSIDE this file as a
   @field_validator. It has now moved to app/guardrails/validators.py as a
   plain, reusable function. We attach it here using Annotated + AfterValidator
   so the same check can be reused by future schemas without copy-pasting it.

2. Commit 2 only validated each field by itself (incident_id looks right?
   grid looks right? priority is one of three words?). It never checked
   whether the FIELDS MAKE SENSE TOGETHER. For example, a HIGH priority
   incident with an empty-ish description ("na") would have passed Commit 2
   even though a real dispatcher would never submit that. This file adds a
   model_validator — a check that runs AFTER all individual fields pass —
   to catch exactly that kind of cross-field problem.

Guardrail location: app/guardrails/schemas.py
Tested by: tests/test_character_validation.py (unchanged tests) and
           tests/test_cross_field_validation.py (new tests for this upgrade)
"""
from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, Field, model_validator

from app.guardrails.validators import validate_operational_characters

# This type alias means: "a string that must also pass
# validate_operational_characters before Pydantic accepts it."
# Any field below (or in a future schema) can reuse this one alias instead
# of writing its own @field_validator.
WhitelistedText = Annotated[str, AfterValidator(validate_operational_characters)]


class DispatchRequest(BaseModel):
    """
    A validated dispatch request.

    Field-level checks (regex patterns, the whitelist) run first, one field
    at a time. Only if every field passes does Pydantic run the cross-field
    check defined below in `check_high_priority_has_real_description`.
    """

    incident_id: str = Field(pattern=r"^INC-\d{4}$")
    grid: str = Field(pattern=r"^[A-Z0-9]{2,4}$")
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    description: WhitelistedText = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def check_high_priority_has_real_description(self) -> "DispatchRequest":
        """
        Cross-field rule: if priority is HIGH, the description must be a
        real sentence (at least 10 characters), not a placeholder like "na"
        or "x". A single field can never catch this on its own, because the
        rule depends on TWO fields (priority AND description) at the same
        time. This is why it lives in a model_validator instead of a
        field_validator.

        mode="after" means this method runs only after every individual
        field has already passed its own check — so by the time we get
        here, self.priority and self.description are both guaranteed to
        already be valid on their own.
        """
        if self.priority == "HIGH" and len(self.description.strip()) < 10:
            raise ValueError(
                "HIGH priority incidents require a description of at "
                "least 10 characters explaining the situation"
            )
        return self

    def to_prompt_fragment(self) -> str:
        """Format the validated fields into the text sent to the LLM."""
        return (
            f"Incident ID : {self.incident_id}\n"
            f"Grid        : {self.grid}\n"
            f"Priority    : {self.priority}\n"
            f"Description : {self.description}"
        )
