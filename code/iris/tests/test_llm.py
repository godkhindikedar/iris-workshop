import pytest

from backend.app.llm import MAX_OUTPUT_TOKENS, build_chat_model, message_text
from backend.app.settings import DEFAULT_LLM_MODEL, Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_gemini_is_the_only_model_and_needs_project_and_key_file():
    s = _settings(google_cloud_project="", google_application_credentials="")
    assert not s.llm_configured
    assert "GOOGLE_CLOUD_PROJECT" in s.llm_key_env_var
    assert s.chat_model_name == DEFAULT_LLM_MODEL
    assert not _settings(google_cloud_project="p", google_application_credentials="").llm_configured
    assert _settings(google_cloud_project="p", google_application_credentials="/k.json").llm_configured


def test_model_garden_prefix_is_stripped():
    s = _settings(llm_model="publishers/google/models/gemini-3.8-flash")
    assert s.chat_model_name == "gemini-3.8-flash"


def test_lightweight_model_falls_back_to_the_chat_model():
    assert _settings(llm_model="gemini-x").lightweight_model_name == "gemini-x"
    assert _settings(llm_model="gemini-x", llm_lightweight_model="gemini-y").lightweight_model_name == "gemini-y"


def test_build_chat_model_uses_vertex_with_service_account(monkeypatch):
    import google.oauth2.service_account as sa

    class FakeCreds:
        pass

    seen = {}
    monkeypatch.setattr(sa.Credentials, "from_service_account_file", classmethod(lambda cls, path, scopes=None: seen.update(path=path) or FakeCreds()))
    import langchain_google_vertexai as lgv

    class FakeVertex:
        def __init__(self, **kw):
            self.kw = kw

    monkeypatch.setattr(lgv, "ChatVertexAI", FakeVertex)
    s = _settings(google_cloud_project="proj", google_application_credentials="/k.json", llm_model="gemini-a", llm_lightweight_model="gemini-b")
    model = build_chat_model(s)
    assert seen["path"] == "/k.json"
    assert model.kw["model_name"] == "gemini-a" and model.kw["project"] == "proj"
    assert model.kw["location"] == "global" and model.kw["thinking_budget"] == 0
    assert model.kw["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert build_chat_model(s, lightweight=True).kw["model_name"] == "gemini-b"


def test_only_gemini_dependencies_remain():
    import importlib.util

    assert importlib.util.find_spec("openai") is None
    assert importlib.util.find_spec("langchain_openai") is None
    assert importlib.util.find_spec("anthropic") is None
    assert importlib.util.find_spec("langchain_anthropic") is None


@pytest.mark.parametrize(
    "content, expected",
    [
        ("plain text", "plain text"),
        ([{"type": "text", "text": "Hello "}, {"type": "text", "text": "world"}], "Hello world"),
        ([{"type": "thinking", "thinking": "hmm"}, {"type": "text", "text": "Answer"}, {"type": "tool_use", "name": "x"}], "Answer"),
        ([], ""),
        (None, ""),
    ],
)
def test_message_text_keeps_only_visible_text(content, expected):
    assert message_text(content) == expected
