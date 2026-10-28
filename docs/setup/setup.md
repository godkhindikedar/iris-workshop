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
| `GOOGLE_CLOUD_PROJECT`, `LLM_MODEL`, then `make gcp-login` (or a service account key) | Gemini on Google Cloud (Vertex AI), the agent's model. See [Set up Gemini](#set-up-gemini-google-cloud) below |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`, `REDIS_SSL` | Redis Cloud database |
| `CTX_ADMIN_KEY` | Context Surfaces (Context Retriever) |
| `MEMORY_API_BASE_URL`, `MEMORY_STORE_ID`, `MEMORY_API_KEY` | Agent Memory |
| `LANGCACHE_HOST`, `LANGCACHE_CACHE_ID`, `LANGCACHE_API_KEY` | LangCache |

Leave `MCP_AGENT_KEY` and `CTX_SURFACE_ID` empty. The next step fills them in.

No embeddings key is needed: the guardrail, tool routing and Simple RAG use a small embedding model that runs inside the container. The first start downloads it (about 90 MB), so give the backend a minute.

> The demo starts even before any credentials are set. Until `GOOGLE_CLOUD_PROJECT` is set and you have signed in to Google (`make gcp-login`) or added a key, the chat replies with a message saying so. The backend restarts automatically whenever `.env` changes.

## Set up Gemini (Google Cloud)

The agent runs on Gemini through Google Cloud (Vertex AI). You need a Google Cloud **project ID** where Gemini is available, and a Google account that is allowed to use it. There are two ways to give the app access. Most people should use the first.

### Option A: sign in with your Google account (no key file)

Do this inside the workbench:

1. **Get the project ID** of a Google Cloud project where Gemini is enabled in Model Garden (for example `my-project-123456`). In a project your team already uses for Gemini, the **Vertex AI API** (`aiplatform.googleapis.com`) is normally on already; if not, enable it under *APIs & Services*. You do not need a service account or a key file for this option. Your account needs the **Agent Platform User** role (`roles/aiplatform.user`, called *Vertex AI User* in older consoles) on it, plus permission to use the project's APIs for billing (for example the *Service Usage Consumer* role).
2. **Set the project** in `iris/.env` (open it in the **VS Code** panel):

   ```bash
   GOOGLE_CLOUD_PROJECT=my-project-123456
   LLM_MODEL=gemini-3.8-flash
   ```

   Leave `GOOGLE_CLOUD_LOCATION=global` and `GOOGLE_APPLICATION_CREDENTIALS` as they are. `LLM_MODEL` is the model ID shown in Model Garden; the `publishers/google/models/` prefix is optional.
3. **Sign in.** Open the **Terminal** panel and run:

   ```bash
   make gcp-login
   ```

   It prints a long `https://accounts.google.com/...` link. Open it in a new browser tab, choose your Google account, and approve. The last page shows a **verification code**. Copy it and paste it back into the terminal at *Enter authorization code*, then press Enter.
4. **Ask a question** in the **App** panel. The backend restarts by itself after the sign-in, which takes a few seconds. If the chat says Google credentials were not found, run `make gcp-login` again.

Your sign-in is stored in a Docker volume on your own computer, readable only by the workshop containers. It is not part of the code folder and is never committed. To remove it, run `docker compose down -v` (this also removes the other workshop volumes) or run `gcloud auth application-default revoke` in the Terminal. If your organization limits how long sign-ins last and chat starts failing with an authentication error, run `make gcp-login` again.

### Option B: a service account key (for a shared or facilitator-run setup)

Use this when attendees should not sign in themselves, or you want one identity for the whole workshop.

1. **Enable the API.** In the Cloud console, open *APIs & Services*, then *Enable APIs and services*, and enable the **Vertex AI API** (`aiplatform.googleapis.com`, which Google now also labels Agent Platform).
2. **Check model access and quota.** Open *Vertex AI*, then *Model Garden*, find the Gemini model you want, and confirm it is available. Under *IAM & Admin*, then *Quotas & System Limits*, look up the quotas for that model. A new project can have low capacity, which shows up as a "quota exceeded" (429) error in the chat; see Troubleshooting.
3. **Create a service account** under *IAM & Admin*, then *Service Accounts* (for example `iris-workshop-sa`).
4. **Give it the right role.** Grant it the role with ID **`roles/aiplatform.user`**. Google has renamed Vertex AI to *Agent Platform*, so the console may show **Agent Platform User** (older consoles say *Vertex AI User*); search for `aiplatform.user` if the name does not match. It includes `aiplatform.endpoints.predict`, the permission model calls need ([IAM roles reference](https://docs.cloud.google.com/iam/docs/roles-permissions/aiplatform)). Do not use *Vertex AI Service Agent*, which is for Google's own services. From Cloud Shell:

   ```bash
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="serviceAccount:iris-workshop-sa@PROJECT_ID.iam.gserviceaccount.com" \
     --role="roles/aiplatform.user"
   ```
5. **Create a key.** Open the service account, then *Keys*, *Add key*, *Create new key*, **JSON**. Save the file as `secrets/gcp-key.json` in the workshop folder (next to `docker-compose.yml`). Docker mounts that folder into the backend, read-only. The `secrets/` folder is git-ignored. Do not paste the key into chat or email.
6. **Fill in `iris/.env`:**

   ```bash
   GOOGLE_CLOUD_PROJECT=my-project-123456
   GOOGLE_CLOUD_LOCATION=global
   GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-key.json
   LLM_MODEL=gemini-3.8-flash
   ```
7. **Restart the backend** (`docker compose restart backend`) and ask a question. A permission error means step 4 needs rechecking; a quota error means step 2.

Some organizations block service account keys. In that case use Option A, or run `gcloud auth application-default login` on your own computer and copy `~/.config/gcloud/application_default_credentials.json` to `secrets/gcp-key.json` (it holds a long-lived sign-in for your account, so treat it like a password and revoke it when you are done).

`GOOGLE_CLOUD_LOCATION=global` lets Google pick the region. Set a region such as `us-central1` only if the model is available only in specific regions or your quota is regional.

Optional settings: `LLM_THINKING_BUDGET` (default `0`, which turns Gemini's "thinking" off for much faster answers; raise it, for example to `1024`, for harder questions), `LLM_LIGHTWEIGHT_MODEL` (a cheaper model for the optional answer-verification step), `LLM_TIMEOUT_SECONDS` (default 90) and `LLM_MAX_RETRIES` (default 2). Delete the service account key in Google Cloud when the workshop is over.

## 2. Load the Data

Open the **Terminal** panel and run:

```bash
make setup
```

This generates the Reddash data, loads it into Redis, creates a Context Surface, and seeds Agent Memory and LangCache. It takes a minute or two. **It flushes the Redis database you configured.**

## 3. Check That It Works

Open the **App** panel and ask *"Why is my order running late?"*. You should get an answer that names the driver, Marcus Johnson, and the flat tire.

Then click **Redis Iris** (top right). The **Activity** tab should list steps for Semantic Routing, LangCache, Agent Memory and Context Retriever. If one is missing, that service's credentials in `iris/.env` are not set or not valid.

If the App panel shows a 502 error, the backend is still starting (the first start loads the embedding model, which can take a minute or two). Wait a moment and reload.

## Troubleshooting

- **App shows errors / 502:** the backend is still starting or waiting for credentials. Check the container logs (`docker compose logs backend`).
- **Agent has no tools after a restart:** run `make reset` to reload the data.
- **"rate limited" or "out of quota" in the chat:** your Google Cloud project hit its Vertex AI quota for the model (see [Set up Gemini](#set-up-gemini-google-cloud)). Every model call carries the tool definitions (about 20,000 tokens for all 57), and one question makes 2 to 4 calls. Measured on three sample questions, semantic tool routing (on by default) used 19,000 to 24,000 tokens per question, against 63,000 to 78,000 with it off (`TOOL_ROUTING_ENABLED=false`); see [Task 4](/tasks/task-4.md). For a workshop, budget tens of thousands of tokens per question and multiply by the questions your attendees ask in the same minute. Cached and blocked questions use few or no tokens.
- **First start is slow / "could not load the embedding model":** the embedding model downloads from Hugging Face on first use. Check the backend can reach huggingface.co; it is cached afterwards.
- **Frontend logs:** `tail -f /tmp/vite.log` in the Terminal panel.

Tip: to look at the data the demo loaded, import the generated `iris/redis-insight-import.json` into **Redis Insight**. [Task 2](/tasks/task-2.md) has the steps.

Ready? Follow the [first-time learner path](/learn/first-hour.md), or jump to [Task 1](/tasks/task-1.md). Skim [Redis Iris Concepts](/concepts/iris.md) if the product names are new.
