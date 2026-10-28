from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = ROOT_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

DEFAULT_MEMORY_SIMILARITY_THRESHOLD = 0.3

# Default Gemini model when LLM_MODEL is unset. LLM_MODEL may be the bare ID or the Model Garden
# resource name (publishers/google/models/<id>).
DEFAULT_LLM_MODEL = "gemini-3.8-flash"
MODEL_GARDEN_PREFIX = "publishers/google/models/"

# Local sentence-transformers model used for every embedding in the demo (guardrail, tool routing,
# Simple RAG and the seeded policy documents). It runs inside the container, so no API key is needed.
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_EMBEDDING_DIM = 384


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Gemini on Google Cloud (Vertex AI Model Garden), authenticated with a service account key.
    llm_model: str = Field(default="")
    # Cheaper model for answer verification (defaults to LLM_MODEL).
    llm_lightweight_model: str = Field(default="")
    google_cloud_project: str = Field(default="")
    # "global" lets Google pick the region; use a region such as us-central1 if your quota is regional.
    google_cloud_location: str = Field(default="global")
    # Path, as seen inside the container (see docker-compose.yml), to a service account JSON key or to the
    # Application Default Credentials file from `gcloud auth application-default login`.
    google_application_credentials: str = Field(default="")
    # Tokens Gemini may spend "thinking" before each reply. 0 turns thinking off (fastest); empty uses the
    # model's default. Thinking adds seconds to every step of the agent loop.
    llm_thinking_budget: int | None = Field(default=0)
    # Fail fast instead of stalling: seconds to wait for one Gemini request, and how many times to retry
    # a failed one (for example a 429). The library default is 6 retries with no timeout.
    llm_timeout_seconds: float = Field(default=90.0)
    llm_max_retries: int = Field(default=2)

    # Local embeddings. EMBEDDING_DIM must match the model; schemas size their vector fields from it.
    # Set EMBEDDING_MODEL=hash for deterministic fake vectors (tests and offline use only).
    embedding_model: str = Field(default=DEFAULT_EMBEDDING_MODEL)
    embedding_dim: int = Field(default=DEFAULT_EMBEDDING_DIM)

    redis_host: str = Field(default="localhost")
    redis_port: int = Field(default=6379)
    redis_username: str = Field(default="default")
    redis_password: str = Field(default="")
    redis_db: int = Field(default=0)
    redis_ssl: bool = Field(default=False)

    @field_validator("redis_port", mode="before")
    @classmethod
    def _empty_port_to_default(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return 6379
        return v

    @field_validator("redis_db", mode="before")
    @classmethod
    def _empty_db_to_default(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return 0
        return v

    ctx_admin_key: str = Field(default="")
    mcp_agent_key: str = Field(default="")
    ctx_surface_id: str = Field(default="")
    ctx_redis_instance_id: str = Field(default="")

    memory_api_base_url: str = Field(default="")
    memory_store_id: str = Field(default="")
    memory_api_key: str = Field(default="")
    memory_owner_id: str = Field(default="")
    memory_actor_id: str = Field(default="iris-agent")
    memory_namespace: str = Field(default="")
    memory_similarity_threshold: float | None = Field(default=None)
    memory_limit: int = Field(default=6)

    langcache_host: str = Field(default="")
    langcache_cache_id: str = Field(default="")
    langcache_api_key: str = Field(default="")
    langcache_threshold: float = Field(default=0.9)

    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8040)
    cors_origin: str = Field(default="http://localhost:3040")
    guardrail_enabled: bool = Field(default=True)
    # Send the LLM only the tools a question needs (see ToolRoutingConfig in the domain manifest).
    tool_routing_enabled: bool = Field(default=True)
    demo_domain: str = Field(default="reddash")
    show_final_verifier_trace_step: bool = Field(default=False)
    show_llm_trace_steps: bool = Field(default=False)

    radish_hf_embedding_model: str = Field(
        default="sentence-transformers/all-mpnet-base-v2",
    )
    hf_token: str = Field(default="", validation_alias="HF_TOKEN")

    @field_validator("memory_similarity_threshold", mode="before")
    @classmethod
    def _empty_similarity_threshold_to_none(cls, v: object) -> object:
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @property
    def effective_memory_namespace(self) -> str:
        return self.memory_namespace or f"{self.demo_domain}-demo"

    @property
    def effective_memory_actor_id(self) -> str:
        return self.memory_actor_id or f"{self.demo_domain}-agent"

    @property
    def chat_model_name(self) -> str:
        """Gemini model ID for the agent."""
        return self._model_id(self.llm_model)

    @property
    def lightweight_model_name(self) -> str:
        return self._model_id(self.llm_lightweight_model) if self.llm_lightweight_model else self.chat_model_name

    @staticmethod
    def _model_id(configured: str) -> str:
        return (configured or DEFAULT_LLM_MODEL).removeprefix(MODEL_GARDEN_PREFIX)

    @property
    def llm_configured(self) -> bool:
        """True when the Google Cloud project is set and the credentials file exists."""
        return bool(self.google_cloud_project) and bool(
            self.google_application_credentials and Path(self.google_application_credentials).is_file()
        )

    @property
    def llm_key_env_var(self) -> str:
        return "GOOGLE_CLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALS"

    @property
    def llm_setup_message(self) -> str:
        """What the chat tells the user while Gemini is not set up yet."""
        if not self.google_cloud_project:
            return "Set `GOOGLE_CLOUD_PROJECT` in `.env` to your Google Cloud project ID."
        return (
            "Google credentials not found. In the Terminal panel run `make gcp-login` and follow the prompts "
            "(or save a service account key as `secrets/gcp-key.json`)."
        )


def get_settings() -> Settings:
    return Settings()
