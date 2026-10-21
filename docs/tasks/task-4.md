# Task 4: Save Tokens with Semantic Tool Routing

## Goal

Cut the cost of every agent question by sending the LLM only the tools it needs, chosen with **Semantic Routing**.

## Why it matters

The Reddash agent has 57 tools. Every time it calls the model, all the tool definitions are sent along: about **20,000 tokens per call on Gemini**, and one question makes 2-4 calls. Most questions only need a few of those tools.

Semantic tool routing fixes that. A second semantic router (stored in Redis, like the guardrail) matches the question against groups of example questions and attaches only the matching group's tools. It reuses the embedding the guardrail already computed, so it adds a Redis vector search and no extra model call. If nothing matches, every tool is attached, so routing can save tokens but never removes the agent's ability to answer.

## Instructions

### Step 1: Measure without routing

In the **Terminal** panel run:

```bash
TOOL_ROUTING_ENABLED=false uv run python scripts/measure_tokens.py "I reported a missing item last week - was that resolved?"
```

Note the **input tokens per call** and the **TOTAL tokens**. (This makes real Gemini calls and uses your project's Vertex AI quota.)

### Step 2: Measure with routing

```bash
TOOL_ROUTING_ENABLED=true uv run python scripts/measure_tokens.py "I reported a missing item last week - was that resolved?"
```

The question now matches the `support_tickets` and `policies` routes, so only 15 of 57 tools are sent. In our test the total dropped from about **78,000** to about **19,000** tokens (75% fewer). Across three sample questions it was about 208,000 against 63,000 tokens, roughly 70% fewer.

### Step 3: Watch it in the app

Ask the same question in the **App** panel and open **Tool selection · ROUTE** under *Semantic Routing* in the activity panel. It shows the matched route, its distance, and how many tools were selected. Then open the **All Context** tab and look at the **Tool Selection** card under *Context Retriever*: it shows how many of the 57 tools were sent, roughly how many tokens that saved per model call, the matched routes, and (under *View selected tools*) the exact tools the LLM was shown.

### Step 4: Read the routes

Open `iris/domains/reddash/domain.py` and find `tool_routing`. Each route has:

- `references`: example questions that describe the route
- `tools`: the tools to attach (names or `*` patterns)
- `distance_threshold`: how close a question must be to match (lower is stricter)

`always_on` lists tools sent with every call (user profile, time, memory).

### Step 5: Experiment

Try one of these, save, and wait a few seconds for the backend to reload and rebuild the router:

1. Ask a question in your own words, such as "Did you ever sort out my complaint?". Does it route correctly? Add a reference phrase to the route if not.
2. Lower a `distance_threshold` until a question stops matching. What does the activity panel show? (No match means every tool is attached.)
3. Remove `filter_supportticket` from the `support_tickets` route and ask the missing-item question again. This is the risk of routing: the agent can't use a tool it was never shown.

### Step 6: Check that you did not break anything

Routes and thresholds are easy to get subtly wrong, so score them against a set of example messages:

```bash
uv run python scripts/eval_routing.py
```

It reports, for the guardrail, any attack that gets through and any normal question that is blocked or flagged, and for the tool routes, any question whose expected tool group was not matched, plus how many groups match on average (fewer groups means fewer tokens). The messages live in `iris/domains/reddash/routing_eval.json`; add your own. Run it again whenever you change a route, a threshold, or the embedding model.

## Challenge

Add a route for a new kind of question, for example one about restaurants only, with 5-6 references. Measure the question before and after with `scripts/measure_tokens.py`.

## What You Learned

✅ Tool definitions are a big, repeated token cost for agents  
✅ Semantic routing can pick tools per question, using the same embeddings and Redis as the guardrail  
✅ The trade-off: tighter routes save more tokens but risk hiding a tool the agent needs  

---

**Happy building!** See the [Reference](/reference/reference.md) for links and commands.
