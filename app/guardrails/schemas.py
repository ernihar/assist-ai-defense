"""
Defines the DispatchRequest schema used to validate a dispatcher's incident
request before it is sent to the LLM.

Why this file exists: the LLM should never see raw, unchecked text. This
schema checks that every field has the right shape (character whitelist,
correct length, correct format) BEFORE the request is allowed through.
"""
from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator
from typing import Literal

ALLOWED_CHARACTERS_PATTERN = re.compile(r"^[A-Za-z0-9,\- ]+$")


class DispatchRequest(BaseModel):
    """
    A validated dispatch request.

    Each field below only accepts a specific format. If a field does not
    match, Pydantic raises a ValidationError automatically — we do not
    need to write manual if-checks for each field.
    """

    incident_id: str = Field(pattern=r"^INC-\d{4}$")
    grid: str = Field(pattern=r"^[A-Z0-9]{2,4}$")
    priority: Literal["LOW", "MEDIUM", "HIGH"]
    description: str = Field(min_length=1, max_length=500)

    @field_validator("description")
    @classmethod
    def check_description_characters(cls, value: str) -> str:
        """
        The description is free text typed by a dispatcher, so it is the
        highest-risk field. This check makes sure it only contains letters,
        numbers, spaces, commas, and hyphens.
        """
        if not ALLOWED_CHARACTERS_PATTERN.match(value):
            raise ValueError(
                "description contains characters outside the allowed set "
                "(letters, numbers, space, comma, hyphen only)"
            )
        return value

    def to_prompt_fragment(self) -> str:
        """Format the validated fields into the text sent to the LLM."""
        return (
            f"Incident ID : {self.incident_id}\n"
            f"Grid        : {self.grid}\n"
            f"Priority    : {self.priority}\n"
            f"Description : {self.description}"
        )
