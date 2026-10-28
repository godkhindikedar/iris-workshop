"""Chat model (Gemini on Google Cloud Vertex AI) and message helpers."""

from __future__ import annotations

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel

from backend.app.settings import Settings

MAX_OUTPUT_TOKENS = 4096


def load_google_credentials(settings: Settings) -> Any:
    """Google credentials from GOOGLE_APPLICATION_CREDENTIALS, which can be either file type:

    * a service account key (JSON), or
    * Application Default Credentials created by ``gcloud auth application-default login``
      (an ``authorized_user`` JSON file), for accounts that cannot create service account keys.

    With no file set, falls back to the environment's Application Default Credentials.
    """
    import google.auth

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]
    if settings.google_application_credentials:
        credentials, _ = google.auth.load_credentials_from_file(settings.google_application_credentials, scopes=scopes)
    else:
        credentials, _ = google.auth.default(scopes=scopes)
    # User credentials are billed against a project; use the configured one so no extra gcloud step is needed.
    if settings.google_cloud_project and hasattr(credentials, "with_quota_project"):
        credentials = credentials.with_quota_project(settings.google_cloud_project)
    return credentials


def build_chat_model(settings: Settings, *, lightweight: bool = False) -> BaseChatModel:
    """Build the Gemini chat model on Vertex AI.

    ``lightweight=True`` returns the cheaper model used for answer verification.
    """
    from langchain_google_vertexai import ChatVertexAI

    credentials = load_google_credentials(settings)
    return ChatVertexAI(
        model_name=settings.lightweight_model_name if lightweight else settings.chat_model_name,
        project=settings.google_cloud_project,
        location=settings.google_cloud_location or "global",
        credentials=credentials,
        temperature=0.2,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_budget=settings.llm_thinking_budget,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries,
    )


def message_text(content: Any) -> str:
    """Plain text of a message's content.

    Gemini can return a list of blocks (text, tool_use, thinking...), of which only the text blocks are
    user-visible. A plain string is returned unchanged.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type", "text") == "text":
                text = item.get("text")
                if text:
                    parts.append(str(text))
        return "".join(parts)
    return "" if content is None else str(content)
