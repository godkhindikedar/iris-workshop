import pytest

from backend.app.llm import MAX_OUTPUT_TOKENS, build_chat_model, message_text
from backend.app.settings import DEFAULT_LLM_MODEL, Settings


def _settings(**overrides) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_gemini_is_the_only_model_and_needs_project_and_credentials_file(tmp_path):
    creds = tmp_path / "adc.json"
    creds.write_text("{}")
    s = _settings(google_cloud_project="", google_application_credentials="")
    assert not s.llm_configured
    assert "GOOGLE_CLOUD_PROJECT" in s.llm_key_env_var
    assert s.chat_model_name == DEFAULT_LLM_MODEL
    assert not _settings(google_cloud_project="p", google_application_credentials="").llm_configured
    assert not _settings(google_cloud_project="p", google_application_credentials=str(tmp_path / "missing.json")).llm_configured
    assert _settings(google_cloud_project="p", google_application_credentials=str(creds)).llm_configured


def test_setup_message_points_to_the_next_step():
    assert "GOOGLE_CLOUD_PROJECT" in _settings(google_cloud_project="").llm_setup_message
    assert "make gcp-login" in _settings(google_cloud_project="p", google_application_credentials="/nope.json").llm_setup_message


def test_model_garden_prefix_is_stripped():
    s = _settings(llm_model="publishers/google/models/gemini-3.8-flash")
    assert s.chat_model_name == "gemini-3.8-flash"


def test_lightweight_model_falls_back_to_the_chat_model():
    assert _settings(llm_model="gemini-x").lightweight_model_name == "gemini-x"
    assert _settings(llm_model="gemini-x", llm_lightweight_model="gemini-y").lightweight_model_name == "gemini-y"


def _fake_vertex(monkeypatch, loader_calls):
    import google.auth as ga
    import langchain_google_vertexai as lgv

    class FakeCreds:
        def with_quota_project(self, project):
            loader_calls["quota_project"] = project
            return self

    monkeypatch.setattr(ga, "load_credentials_from_file", lambda path, scopes=None: loader_calls.update(file=path) or (FakeCreds(), "p"))
    monkeypatch.setattr(ga, "default", lambda scopes=None: loader_calls.update(default=True) or (FakeCreds(), "p"))

    class FakeVertex:
        def __init__(self, **kw):
            self.kw = kw

    monkeypatch.setattr(lgv, "ChatVertexAI", FakeVertex)


def test_build_chat_model_uses_vertex_with_a_credentials_file(monkeypatch):
    calls = {}
    _fake_vertex(monkeypatch, calls)
    s = _settings(google_cloud_project="proj", google_application_credentials="/k.json", llm_model="gemini-a", llm_lightweight_model="gemini-b")
    model = build_chat_model(s)
    assert calls["file"] == "/k.json" and calls["quota_project"] == "proj"
    assert model.kw["model_name"] == "gemini-a" and model.kw["project"] == "proj"
    assert model.kw["location"] == "global" and model.kw["thinking_budget"] == 0
    assert model.kw["max_output_tokens"] == MAX_OUTPUT_TOKENS
    assert model.kw["timeout"] == 90.0 and model.kw["max_retries"] == 2
    assert build_chat_model(s, lightweight=True).kw["model_name"] == "gemini-b"


def test_adc_file_and_environment_defaults_both_work(monkeypatch):
    calls = {}
    _fake_vertex(monkeypatch, calls)
    # `gcloud auth application-default login` file (authorized_user) goes through the same loader
    build_chat_model(_settings(google_cloud_project="proj", google_application_credentials="/adc.json"))
    assert calls["file"] == "/adc.json"
    calls.clear()
    # no file: fall back to the environment's Application Default Credentials
    build_chat_model(_settings(google_cloud_project="proj", google_application_credentials=""))
    assert calls.get("default") is True and "file" not in calls


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
