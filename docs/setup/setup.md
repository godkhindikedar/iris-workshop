# Setup Guide

## Finding Your Code

In VS Code the demo lives in `iris/`:

```
iris/
├── backend/    FastAPI app and LangGraph agent
├── domains/    One folder per demo (reddash, electrohub, ...)
├── frontend/   React chat UI
├── scripts/    Data generation, loading and seeding
└── .env        Your credentials (created on first start)
```

## 1. Add Your Credentials

Open `iris/.env` and fill in the values provided for the workshop:

| Variable(s) | Service |
|-------------|---------|
| `GOOGLE_CLOUD_PROJECT`, `LLM_MODEL`, and a service account key at `secrets/gcp-key.json` | Gemini on Google Cloud (Vertex AI), the agent's model. See [Set up Gemini](#set-up-gemini-google-cloud) below |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_SSL` | Redis Cloud database |
| `CTX_ADMIN_KEY` | Context Surfaces (Context Retriever) |
| `MEMORY_API_BASE_URL`, `MEMORY_STORE_ID`, `MEMORY_API_KEY` | Agent Memory |
| `LANGCACHE_HOST`, `LANGCACHE_CACHE_ID`, `LANGCACHE_API_KEY` | LangCache |

Leave `MCP_AGENT_KEY` and `CTX_SURFACE_ID` empty. The next step fills them in.

No embeddings key is needed: the guardrail, tool routing and Simple RAG use a small embedding model that runs inside the container. The first start downloads it (about 90 MB), so give the backend a minute.

> The demo starts even before any credentials are set. Until `GOOGLE_CLOUD_PROJECT` and the service account key are set, the chat replies with a message saying so. The backend restarts automatically whenever `.env` changes.

## Set up Gemini (Google Cloud)

The agent runs on Gemini through Vertex AI. You need a Google Cloud project with billing enabled, and a service account the app signs in as. Do this once:

1. **Pick the project.** Note its project ID (for example `my-project-123456`).
2. **Enable the API.** In the Cloud console, open *APIs & Services*, then *Enable APIs and services*, and enable the **Vertex AI API** (`aiplatform.googleapis.com`, which Google now also labels Agent Platform).
3. **Check model access and quota.** Open *Vertex AI*, then *Model Garden*, find the Gemini model you want to use, and confirm it is available. Under *IAM & Admin*, then *Quotas*, look up the Vertex AI quotas for that model. A new project can have a low or zero default, which shows up as a "quota exceeded" error in the chat. Request an increase if you need one.
4. **Create a service account.** Under *IAM & Admin*, then *Service Accounts*, create one (for example `iris-workshop-sa`).
5. **Give it the right role.** Under *IAM*, grant that service account the role with ID **`roles/aiplatform.user`**. Google has renamed Vertex AI to *Agent Platform*, so the console may show it as **Agent Platform User** (older consoles and docs call it *Vertex AI User*). Search for the role ID `aiplatform.user` if the name does not match. It grants "access to use all resource in Agent Platform" and includes `aiplatform.endpoints.predict`, which is the permission model calls need ([IAM roles reference for Agent Platform](https://docs.cloud.google.com/iam/docs/roles-permissions/aiplatform)). Do not use *Vertex AI Service Agent*, which is for Google's own services. You can also grant it from Cloud Shell, which works whatever the console calls it:

   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:iris-workshop-sa@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```
6. **Create a key.** Open the service account, then *Keys*, *Add key*, *Create new key*, **JSON**. Save the file as `secrets/gcp-key.json` in the workshop folder (next to `docker-compose.yml`). Docker mounts that folder into the backend, read-only, as `/run/secrets/gcp-key.json`. The `secrets/` folder is git-ignored, so the key is never committed. Do not paste the key into chat or email.
7. **Fill in `iris/.env`:**

   ```bash
   GOOGLE_CLOUD_PROJECT=my-project-123456
   GOOGLE_CLOUD_LOCATION=global
   GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-key.json
   LLM_MODEL=gemini-3.8-flash
   ```

   `LLM_MODEL` takes the model ID shown in Model Garden. The `publishers/google/models/` prefix is optional. `GOOGLE_CLOUD_LOCATION=global` lets Google pick the region; set a region such as `us-central1` if your quota is regional.
8. **Restart the backend** if it was already running (`docker compose restart backend`), then ask a question in the App panel. If you see a permission error, recheck step 5. If you see a quota error, recheck step 3.

Optional settings: `LLM_THINKING_BUDGET` (default `0`, which turns Gemini's "thinking" off for much faster answers; raise it, for example to `1024`, for harder questions) and `LLM_LIGHTWEIGHT_MODEL` (a cheaper model for the optional answer-verification step). Delete the service account key in Google Cloud when the workshop is over.

## 2. Load the Data

Open the **Terminal** panel and run:

```bash
make setup
```

This generates the Reddash data, loads it into Redis, creates a Context Surface, and seeds Agent Memory and LangCache. It takes a minute or two. **It flushes the Redis database you configured.**

## 3. Check That It Works

Open the **App** panel and ask *"Why is my order running late?"*. Then confirm the backend sees every service:

```bash
curl -s backend:8040/api/health
```

`mcp_enabled`, `memory_enabled`, `langcache_enabled` and `guardrail_enabled` should all be `true`.

## Troubleshooting

- **App shows errors / 502:** the backend is still starting or waiting for credentials. Check the container logs (`docker compose logs backend`).
- **Agent has no tools after a restart:** run `make reset` to reload the data.
- **"rate limited" or "out of quota" in the chat:** your Google Cloud project hit its Vertex AI quota for the model (see [Set up Gemini](#set-up-gemini-google-cloud)). Every model call carries the tool definitions (about 20,000 tokens for all 57), and one question makes 2 to 4 calls. Measured on three sample questions, semantic tool routing (on by default) used 19,000 to 24,000 tokens per question, against 63,000 to 78,000 with it off (`TOOL_ROUTING_ENABLED=false`); see [Task 4](/tasks/task-4.md). For a workshop, budget tens of thousands of tokens per question and multiply by the questions your attendees ask in the same minute. Cached and blocked questions use few or no tokens.
- **First start is slow / "could not load the embedding model":** the embedding model downloads from Hugging Face on first use. Check the backend can reach huggingface.co; it is cached afterwards.
- **Frontend logs:** `tail -f /tmp/vite.log` in the Terminal panel.

Tip: to look at the data the demo loaded, import the generated `iris/redis-insight-import.json` into **Redis Insight**. [Task 2](/tasks/task-2.md) has the steps.

Ready? Start [Task 1](/tasks/task-1.md).
