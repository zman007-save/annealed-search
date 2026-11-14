# annealed-search

**SearchHack (Telem AI) — Nov 14, 2026.** Article search that uses simulated
quantum annealing (QUBO) to find the best articles. Private repo:
https://github.com/zman007-save/annealed-search

## What it does

1. **Query understanding** — the query is expanded into angles for the wave.
2. **Retrieval (Telem AI, 40% of the judging)** — one Telem call with
   auto-routing (`accuracy`) across providers (tavily, exa, seltz…), plus
   Tavily search + article extract. Grounded results, hard to build without Telem.
3. **Mantra grounding** — the agent repeats the ORIGINAL prompt against each
   article and scores how well the article grounds to it. That is the
   reliability-of-output score (High / Medium / Low).
4. **QUBO + local simulated annealing** — one binary variable per article,
   solved on your own machine with the D-Wave Ocean SDK. Simulated today,
   QPU-ready: the same BQM runs on the QPU later. The free QPU minute is
   never touched.

## The new parameter control (innovation hook)

Exposes the Tavily search controls from the kickoff slides as UI parameters —
`search_depth`, `country`, `include_domains`, `exclude_domains`,
`time_range`, `max_results` — plus three new ones:

- **Frequency / wave search** — retrieval oscillates between angles and
  profiles across rounds, like a wave going back and forth (fresh/shallow
  ↔ deep/broad), instead of one flat query.
- **Mantra search** — the original prompt is repeated per article to score
  grounding/reliability.
- **Meta-search** — merges an extra pass with the opposite parameter profile
  and ranks across both.

## QUBO mapping

For articles `i = 1..n`, binary variable `x_i = 1` if article `i` is in the
best set:

- linear term: `h_i = 0.45 − relevance_i`
  (`relevance = 0.6 · Tavily score + 0.4 · mantra grounding`).
  Relevance rewards selection; 0.45 is the cost of picking an article.
- quadratic term: `J_ij = 1.2 · Jaccard(title+text tokens of i, j)` when the
  similarity is above 0.05 — the redundancy penalty. Similar articles push
  each other out of the set.
- Objective: minimize energy. Solved with
  `dwave.samplers.SimulatedAnnealingSampler`, 100 reads, on CPU.

## Problems it addresses (kickoff slides)

Too much information · fragmented context · expensive at scale · weak
personalization · limited memory · low performance (queries routed to the
wrong source — Telem auto-routing fixes this).

## Setup

```bash
./run.sh
# then open http://localhost:8000
```

`run.sh` creates `.venv`, installs `requirements.txt`, and starts uvicorn.
Needs a `.env` file next to `app.py` (never committed — see `.gitignore`):

```
TELEM_API_KEY=tlm_...
TAVILY_API_KEY=tvly-...
```

Get a Telem key at https://app.telem.ai (sign in → project → API keys);
the Tavily key is in the Tavily dashboard. All participants get $100 of
Telem credits.

## Verified live test (Nov 14, ~12:00pm PT)

Query: **"quantum computing breakthroughs 2026"** (advanced depth, 3 wave
rounds, mantra + meta-search on). Observed end to end:

- Telem: 15 results, providers tavily / exa / seltz (auto-routed).
- Tavily: 3 wave rounds × 8 results + 1 meta pass → 28 candidates, 8 extracted.
- QUBO: 12 variables, 49 redundancy couplings, 100 annealing reads,
  best energy −1.4529, **6 articles in the best set**, 100/100 reads
  converged to the optimum. Total: ~38 s.

## Demo script (60 seconds, for the Devpost video)

1. (0:00) "Search is drowning in results. We anneal them." Type a query.
2. (0:10) Show the parameter controls — pick a depth, a time range, turn the
   wave rounds up. Hit **Anneal it**.
3. (0:20) Pipeline stages light up: Telem auto-routes the query, Tavily pulls
   the articles, the mantra re-scores each one for grounding.
4. (0:35) The QUBO: 12 variables, 49 couplings, 100 reads. Energy trace
   converges; the best set is highlighted in green with reliability badges.
5. (0:50) "Simulated on this laptop today — the same QUBO runs on a D-Wave
   QPU tomorrow."

## Pushing to GitHub (run on a machine with GitHub auth)

```bash
cd ~/workspace/searchhack   # or wherever you cloned it
git remote add origin https://github.com/zman007-save/annealed-search.git
git branch -M main
git push -u origin main
```

The repo is **private**. `.env` is gitignored and is not in the commit.
GitHub will require 2FA on this account before Nov 28, 2026.

## Still needed for the 4:15pm PT submission

- Devpost: hit **Join hackathon** on https://searchhack.devpost.com, then
  create the project and submit by 4:15pm PT. Needs: project name +
  description, video demo link, thumbnail, and the GitHub repo link above.
- Record the demo video (use the script above) and make a thumbnail.
- Luma registration: https://luma.com/e13wf1bd — only teams where every
  builder checked in as an attendee are judged.
