"""
Reusable validator functions shared across guardrail schemas.

WHY THIS FILE EXISTS (the upgrade from Commit 2):
---------------------------------------------------
In Commit 2, the character whitelist check lived INSIDE the DispatchRequest
class as a @field_validator. That worked fine for one schema, but as soon as
we add a second schema (for example, a future OutputGuardrailResponse or a
ToolCallRequest), we would have to copy-paste the same whitelist check into
every new class. Copy-pasted validation logic is a maintenance risk: if we
ever change the whitelist rule, we would have to remember to update it in
every file that copied it.

This file solves that by defining the whitelist check ONCE, as a plain
function, so any schema can reuse it with Pydantic's Annotated + AfterValidator
pattern. This is the "reusable validators" half of the Commit 2.5 upgrade.
"""
from __future__ import annotations

import re

# Single source of truth for the character whitelist.
# Letters, numbers, space, comma, hyphen only — matches the study guide.
ALLOWED_CHARACTERS_PATTERN = re.compile(r"^[A-Za-z0-9,\- ]+$")


def validate_operational_characters(value: str) -> str:
    """
    Check that `value` only contains whitelisted characters.

    This is a plain function (not a method on any class), so it can be
    attached to ANY string field on ANY future schema using Pydantic's
    Annotated[str, AfterValidator(validate_operational_characters)] pattern.
    Pydantic calls this function automatically after it has already
    confirmed the value is a string.
    """
    if not ALLOWED_CHARACTERS_PATTERN.match(value):
        raise ValueError(
            "text contains characters outside the allowed set "
            "(letters, numbers, space, comma, hyphen only)"
        )
    return value
