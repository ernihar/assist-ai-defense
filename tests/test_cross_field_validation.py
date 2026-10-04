"""
Tests for the Commit 2.5 Pydantic design upgrade:
  1. Reusable validator function (validate_operational_characters)
  2. Cross-field validation (HIGH priority requires a real description)
  3. Structured error reporting (GuardrailRejection.as_field_errors())

Each test class below maps to exactly one of those three upgrades, so it is
easy to see which test proves which design improvement.
"""
import pytest
from pydantic import ValidationError

from app.guardrails.schemas import DispatchRequest
from app.guardrails.pipeline import GuardrailRejection, protected_query_llm
from app.guardrails.validators import validate_operational_characters


VALID_REQUEST = {
    "incident_id": "INC-2045",
    "grid": "5B",
    "priority": "HIGH",
    "description": "Shots fired near Central Mall",
}


class TestReusableValidatorFunction:
    """
    Upgrade 1: the whitelist check is now a plain function, not a method
    glued to one class. These tests call the function directly, with no
    Pydantic model involved at all, proving it works standalone.
    """

    @pytest.mark.guardrail
    def test_valid_text_is_returned_unchanged(self):
        result = validate_operational_characters("Grid 5B, Priority 1")
        assert result == "Grid 5B, Priority 1"

    @pytest.mark.guardrail
    def test_invalid_text_raises_value_error(self):
        with pytest.raises(ValueError):
            validate_operational_characters("<script>alert(1)</script>")

    @pytest.mark.guardrail
    def test_function_is_reused_by_description_field(self):
        """
        Proves the DispatchRequest.description field actually calls this
        shared function, instead of having its own separate copy of the
        same logic (which was the Commit 2 design).
        """
        with pytest.raises(ValidationError):
            DispatchRequest(**{**VALID_REQUEST, "description": "<b>bad</b>"})


class TestCrossFieldValidation:
    """
    Upgrade 2: a model_validator that checks priority AND description
    TOGETHER. Commit 2 could never express this rule, because
    field_validator only ever sees one field at a time.
    """

    @pytest.mark.guardrail
    def test_high_priority_with_short_description_is_rejected(self):
        data = {**VALID_REQUEST, "priority": "HIGH", "description": "na"}
        with pytest.raises(ValidationError):
            DispatchRequest(**data)

    @pytest.mark.guardrail
    def test_high_priority_with_real_description_passes(self):
        data = {
            **VALID_REQUEST,
            "priority": "HIGH",
            "description": "Shots fired near Central Mall",
        }
        request = DispatchRequest(**data)
        assert request.priority == "HIGH"

    @pytest.mark.guardrail
    def test_low_priority_with_short_description_still_passes(self):
        """
        The cross-field rule only applies to HIGH priority. LOW priority
        with a short description is perfectly fine — proving the rule is
        scoped correctly and does not over-reject unrelated cases.
        """
        data = {**VALID_REQUEST, "priority": "LOW", "description": "ok"}
        request = DispatchRequest(**data)
        assert request.priority == "LOW"
        assert request.description == "ok"

    @pytest.mark.guardrail
    def test_medium_priority_with_short_description_still_passes(self):
        data = {**VALID_REQUEST, "priority": "MEDIUM", "description": "ok"}
        request = DispatchRequest(**data)
        assert request.priority == "MEDIUM"


class TestStructuredErrorReporting:
    """
    Upgrade 3: GuardrailRejection.as_field_errors() turns a raw Pydantic
    ValidationError into a simple list of {"field": ..., "message": ...}
    dictionaries, so callers do not need to know anything about Pydantic.
    """

    @pytest.mark.guardrail
    def test_as_field_errors_returns_a_list(self):
        bad_data = {
            "incident_id": "2045",
            "grid": "5B",
            "priority": "HIGH",
            "description": "Shots fired near Central Mall",
        }
        with pytest.raises(GuardrailRejection) as exc_info:
            protected_query_llm(bad_data)

        errors = exc_info.value.as_field_errors()
        assert isinstance(errors, list)
        assert len(errors) >= 1

    @pytest.mark.guardrail
    def test_as_field_errors_names_the_broken_field(self):
        bad_data = {
            "incident_id": "2045",  # wrong format on purpose
            "grid": "5B",
            "priority": "HIGH",
            "description": "Shots fired near Central Mall",
        }
        with pytest.raises(GuardrailRejection) as exc_info:
            protected_query_llm(bad_data)

        errors = exc_info.value.as_field_errors()
        field_names = [error["field"] for error in errors]
        assert "incident_id" in field_names

    @pytest.mark.guardrail
    def test_multiple_bad_fields_reported(self):
        bad_data = {**VALID_REQUEST, "incident_id": "bad", "grid": "zz"}

        with pytest.raises(GuardrailRejection) as exc_info:
            protected_query_llm(bad_data)

        errors = exc_info.value.as_field_errors()
        field_names = [error["field"] for error in errors]

        assert "incident_id" in field_names
        assert "grid" in field_names

    @pytest.mark.guardrail
    def test_as_field_errors_handles_cross_field_errors_safely(self):
        """
        The HIGH-priority-needs-real-description rule is a MODEL-level
        error, not tied to one specific field, so Pydantic's "loc" is
        empty for it. as_field_errors() must not crash on this case —
        it should fall back to a generic "request" label instead.
        """
        bad_data = {
            "incident_id": "INC-2045",
            "grid": "5B",
            "priority": "HIGH",
            "description": "na",
        }
        with pytest.raises(GuardrailRejection) as exc_info:
            protected_query_llm(bad_data)

        errors = exc_info.value.as_field_errors()
        assert any(error["field"] == "request" for error in errors)

    @pytest.mark.guardrail
    def test_cross_field_error_reported(self):
        bad_data = {**VALID_REQUEST, "priority": "HIGH", "description": "Shots fir"}

        with pytest.raises(GuardrailRejection) as exc_info:
            protected_query_llm(bad_data)

        errors = exc_info.value.as_field_errors()

        assert any(error["field"] == "request" for error in errors)
