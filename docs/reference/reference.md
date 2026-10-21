# Reference & Resources

## Quick Links

- [Redis Iris](https://redis.io/iris/)
- [Context Retriever](https://redis.io/docs/latest/develop/ai/context-engine/context-retriever/)
- [Agent Memory](https://redis.io/docs/latest/develop/ai/context-engine/agent-memory/)
- [LangCache](https://redis.io/docs/latest/develop/ai/context-engine/langcache/)

## Terminal Commands

Run these in the Terminal panel (they start in `/code/iris`):

| Command | What it does |
|---------|--------------|
| `make domains` | List available demo domains |
| `make setup` | Generate data, load Redis, seed memory and cache |
| `make reset` | Reload data for the current domain |
| `make seed-memories` | Re-seed long-term memories |
| `make seed-langcache` | Re-seed the semantic cache |
| `make create-domain DOMAIN=x` | Scaffold a new domain |
| `make list-surfaces` | Show the Context Surfaces tied to this demo |
| `make delete-surface` | Delete the current Context Surface (asks first) |
| `make delete-old-surfaces` | Delete earlier Context Surfaces, keeping the current one |
| `uv run python scripts/measure_tokens.py "question"` | Measure Gemini tokens per model call (set `TOOL_ROUTING_ENABLED=false` to compare) |
| `uv run python scripts/eval_routing.py` | Score the guardrail and tool-route thresholds against the messages in `domains/reddash/routing_eval.json` (run it after changing the embedding model, routes or thresholds) |
| `pytest` | Run the unit tests |

## Where Things Run

| Piece | Where |
|-------|-------|
| Chat UI (Vite) | `web` container, `/app/` |
| API (FastAPI) | `backend` container, `/api/` |
| Terminal | `web` container, `/terminal/` |

## What the Prompt-Injection Guardrail Covers

The `prompt_injection` route blocks messages that look like attacks: overriding instructions, extracting the system prompt, jailbreak role-play, fake "system" or "admin" messages, and asking for other customers' data. It checks the **latest user message** against example attacks, so it is a first line of defense, not a complete one:

- A new phrasing that is far from every example can slip through, so add examples as you see new attacks. In our tests, 36 of 36 attack phrasings were blocked and none of 63 legitimate questions were flagged as injection.
- It does not inspect text that comes back from tools or memory (indirect injection), and it looks at one message at a time, so an attack split across several messages is not caught.
- The agent itself is also limited to the signed-in customer's identity, which is what actually protects other customers' data.

## Context Surfaces Pile Up

Every `make setup` creates a **new** Context Surface and never removes the old one, and the admin key is shared by everyone on your account. The delete commands only touch surfaces that are tied to your demo: the one in `.env`, ones this checkout created, or ones that own search indexes in your Redis database. A surface from a colleague is refused unless you pass `--id <uuid> --force`. Deleting a surface also removes its search indexes, so run `make setup` again afterwards.

If several people share one Redis database, a `make setup` by one person gives everyone else stale `CTX_SURFACE_ID` and `MCP_AGENT_KEY` values. Copy the new two lines into the other `.env` files.

## Known Issues

- `tests/test_healthcare_domain.py::test_generate_demo_data_jsonl_valid` fails: it expects an `id` field that the generator does not write.

## Keyboard Shortcuts in VS Code

| Action | Windows/Linux | Mac |
|--------|---------------|-----|
| Save | Ctrl+S | Cmd+S |
| Find | Ctrl+F | Cmd+F |
| Command Palette | Ctrl+Shift+P | Cmd+Shift+P |
