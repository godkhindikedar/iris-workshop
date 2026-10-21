"""Classify LLM errors (Gemini on Vertex AI) for user-facing SSE messages."""

from __future__ import annotations

_QUOTA_MESSAGE = (
    "The model is rate limited or out of quota right now. Wait a moment and try again, or ask for a higher "
    "Vertex AI quota for this model."
)
_PERMISSION_MESSAGE = (
    "Google Cloud refused the request. Check that the service account has the Agent Platform User role (roles/aiplatform.user) and that "
    "the model is enabled for the project."
)


def _truncate_detail(text: str, *, max_len: int = 280) -> str:
    normalized = text.strip()
    if len(normalized) <= max_len:
        return normalized or "An LLM request failed."
    return normalized[: max_len - 1] + "…"


def classify_llm_exception(exc: BaseException) -> tuple[str, str]:
    """Return ``(error_code, user_message)`` for SSE ``error`` events.

    Codes: ``rate_limited`` (HTTP 429 / RESOURCE_EXHAUSTED), ``permission_denied`` (HTTP 403 / 401)
    and ``llm_error`` (anything else).
    """
    text = str(exc)
    lower = text.lower()
    status = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if status == 429 or "resource_exhausted" in lower or "quota exceeded" in lower or "429" in lower[:40]:
        return ("rate_limited", _QUOTA_MESSAGE)
    if status in (401, 403) or "permission_denied" in lower or "permission denied" in lower:
        return ("permission_denied", _PERMISSION_MESSAGE)
    return ("llm_error", _truncate_detail(text))
