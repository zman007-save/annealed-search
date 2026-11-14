# Connect the real annealed-search pipeline to the annealsearch site

Instruction for the GPT site builder (the agent building the annealsearch site from this repo). Paste the block below to it verbatim — do not add keys, credentials, or any secret values.

```text
Please connect the real annealed-search pipeline to the annealsearch site, replacing the Wikipedia-only fallback.

1. Inspect the annealed-search repository and identify the exact Telem and Tavily environment variable names and any other required configuration. Check what already exists without printing, copying or committing secret values.
2. Set the required API keys as server-side secrets in the actual hosting environment. If a key is missing, ask me to enter it through the provider or hosting platform’s secure secret-entry flow. Never put keys in the frontend, GitHub, logs, screenshots or chat.
3. Connect the site to the real backend and preserve the actual retrieval, scoring and annealing pipeline. Make the provider, search progress and errors clear. Do not silently substitute Wikipedia or claim quantum hardware is being used if it isn’t.
4. Check existing free credits, request limits and expected costs before running any live provider calls. Do not enable paid usage or spend without asking me first.
5. Run a small authorized end-to-end test, verify that both services are actually called and the returned results reach the dashboard, and check that secrets are not exposed. Report the deployed URL, test results, remaining blockers and any costs.
```

Don’t paste the keys into this chat. Muse should use the hosting service’s secure secret-entry controls.

## Where the keys are — and aren't

- The repo has NO GitHub Actions secrets and NO Codespaces secrets, by
  design. Do not look for keys there and do not add them there.
- The keys live only in the project's local `.env` (gitignored, never
  committed) and in the Telem/Tavily provider dashboards.
- For the hosted site: ask Zach to enter `TELEM_API_KEY` and
  `TAVILY_API_KEY` through the hosting platform's secure secret-entry
  flow, as server-side env vars only. Never ask for key values in chat,
  and never put them in the repo, the frontend, logs, or screenshots.
- Telem endpoint for the hosted site: set
  `TELEM_BASE_URL=https://hack.telem.ai/api` (the hackathon dedicated
  server — the key issued on app.telem.ai does NOT work there; it returns
  401). A new key for hack.telem.ai is being issued; use the key Zach
  enters in the hosting environment and verify it returns 200 before
  going live. The Tavily key is unchanged.

## Repo pointers for the builder

- Backend: `app.py` (FastAPI, serves the dashboard from `static/`). Run locally with `./run.sh`, then open http://localhost:8000.
- Required server-side env vars (names only — values are never in this repo): `TELEM_API_KEY`, `TAVILY_API_KEY`. See `README.md` under Setup for where to get them.
- What the pipeline does: Telem AI auto-routed search + Tavily wave rounds and meta-search pull the articles; relevance = 0.6 × Tavily + 0.4 × mantra grounding; net score = relevance − worst-twin redundancy + meta/wave bonuses; a QUBO (one binary variable per article) is solved by local simulated annealing (D-Wave Ocean SDK, 100 reads) to pick the best set. The QPU minute is untouched — simulated today, QPU-ready; never claim hardware was used.
- Dashboard guide: `docs/DASHBOARD_DEMO_README.md`. Verified runs and their real numbers: `VERIFIED_RUNS.md` and `runs/`.
- Free credits on record: Tavily Researcher plan, 9,000 credits; Telem billing not implemented yet; all SearchHack participants get $100 of Telem credits. Check current balances before live calls.
