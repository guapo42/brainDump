# ADR 0005 — LLM provider is deferred and abstracted

**Status:** accepted (provider choice deferred) · **Date:** 2026-06-08

## Context
We need a local LLM for the browser Translator (quick capture) and the backend
Extractor (bulk source extraction). Ollama was the prototype's choice, but we are
likely to move to **llama.cpp** (`llama-server`) and have not committed — more
research is needed (performance, model formats, grammar/JSON-schema support,
ops).

## Decision
**Do not couple any code to a specific LLM backend.** Both Ollama and llama.cpp
expose an **OpenAI-compatible** chat-completions API, so we target that surface
and select the provider purely by configuration:

- Backend: `LLM_BASE_URL` + `LLM_MODEL` + a `LLM_PROVIDER` *label* (diagnostics
  only, must not drive code). Default base URL is illustrative, not a commitment.
- Frontend: the Translator's LLM client takes a base URL + model from config.
- Structuring uses JSON mode (`instructor.Mode.JSON` server-side; schema-validated
  client-side) — the lowest common denominator across local servers.

Switching Ollama → llama.cpp must be a `.env` change (e.g.
`LLM_BASE_URL=http://localhost:8080/v1`), never a refactor.

## Consequences
- Any "Ollama" mention in the specs is an **illustrative example**, not a lock-in.
- A thin `LLMProvider`/client port is the only place that knows about transport;
  provider-specific features (e.g. llama.cpp grammars) stay behind it and are
  opt-in.
- Revisit when the research lands; record the final choice as a follow-up ADR
  without changing call sites.
