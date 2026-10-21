"""Tests for LLM error classification (Gemini on Vertex AI)."""

from __future__ import annotations

from backend.app.llm_errors import classify_llm_exception


class _CodedError(Exception):
    def __init__(self, message: str, code: int) -> None:
        super().__init__(message)
        self.code = code


def test_rate_limit_from_status_code() -> None:
    code, msg = classify_llm_exception(_CodedError("slow down", 429))
    assert code == "rate_limited"
    assert "quota" in msg.lower()


def test_rate_limit_from_resource_exhausted_text() -> None:
    code, _ = classify_llm_exception(RuntimeError("429 RESOURCE_EXHAUSTED: Quota exceeded for model"))
    assert code == "rate_limited"


def test_permission_denied() -> None:
    code, msg = classify_llm_exception(_CodedError("The caller does not have permission", 403))
    assert code == "permission_denied"
    assert "roles/aiplatform.user" in msg


def test_generic_exception() -> None:
    code, msg = classify_llm_exception(RuntimeError("Something else broke"))
    assert code == "llm_error"
    assert "Something else broke" in msg
