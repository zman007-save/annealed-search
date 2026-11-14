# Guarded backend proposal (not deployed)

Base: 1785a2d7d84894cecf3b2e180345f091ae8ca004. Additive files only; original research app and builder-owned deployment files are unchanged.

## Required deployment changes BEFORE provider keys are present

Use `uvicorn secure_app:app --host 0.0.0.0 --port $PORT --workers 1 --no-access-log`, NOT `app:app`. Set health check `/healthz`. Do not expose a second unguarded app process.

In the host secret-entry UI set BACKEND_ACCESS_TOKEN to a random secret at least 32 characters, TELEM_API_KEY, TAVILY_API_KEY; TELEM_BASE_URL is configuration, currently the builder supplies https://hack.telem.ai/api. Keep ENABLE_PROVIDER_CALLS=false until account credits, endpoint and owner authorization are verified. Wrapper is disabled by default.

Site must use a private authenticated server-side proxy: its runtime secret holds BACKEND_ACCESS_TOKEN; never client JavaScript/localStorage or request query strings. Preserve owner-only Site access and reject unauthenticated proxy calls. Do not use this token as a public-user login mechanism. Proxy implementation remains pending, not part of this proposal.

## Boundary

Only `/healthz` GET is anonymous and returns generic liveness. `/api/health` GET and `/api/search` POST require Bearer auth; no static, documentation, raw provider-state or other routes are exposed by the wrapper. Unset/short token fails closed. No CORS allowance.

Search body max4096bytes, query1–180characters, max_results1–10, frequency_rounds1–2, meta_search=false. Basic depth default. Original relevance, QUBO and sampler unchanged. Limit2 admitted requests per60seconds,10 per process lifetime, one in flight. Invalid input never reaches original app. Telem still requests20 initial results in original app; extract can call up to2 batches for40URLs. These search-count caps are NOT provider-credit or dollar caps.

Limits are process-local and reset at restart. MUST use one worker/instance; no horizontal scaling. They are suitable for a gated owner test, not durable public billing controls. Before public/multiuser use implement persistent shared quota/rate accounting, entitlement validation, timeouts/job isolation and tests. No guarantee that a cancelled upstream call avoids provider billing. No money may be spent solely because a request passes this wrapper.

Run offline checks: `python -m unittest -v test_backend_guard`. Tests substitute a fake ASGI downstream and make zero provider requests. Production source integration and real Render deployment have NOT been tested. Configure TLS through host and preserve secret masking. Review original response/error paths before broad use.
