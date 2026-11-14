# annealed-search

**SearchHack (Telem AI) — Nov 14, 2026.** Article search that uses simulated
quantum annealing (QUBO) to find the best articles. Private repo:
https://github.com/zman007-save/annealed-search

## What it does

1. **Query understanding** — the query is expanded into angles for the wave.
2. **Retrieval (Telem AI, 40% of the judging)** — one Telem call with
   auto-routing (`accuracy`) across providers (tavily, exa, seltz…), plus
   Tavily search + article extract. Grounded results, hard to build without Telem.
   **Scaled:** 10 distinct query angles × up to 10 wave rounds (each round a
   different angle + alternating depth / time range / topic) + 2 meta-search
   passes + Telem — hundreds of raw results, deduped to 100–200 unique
   candidates per query. Extract runs on the top 40 by preliminary
   relevance; the QUBO anneals the FULL candidate set.
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

The dashboard shows the scores of ALL articles (relevance, mantra
grounding, reliability badge, selected or not) plus a Top 10 list per
search.

## Verified live test — 1,010 articles (Nov 14, ~12:53pm PT)

Same query, **"AI search agents 2026"** (advanced depth, 40 wave rounds,
max_results 50, mantra + meta-search on). The scale-up: per-call
max_results raised from 20 to 50 (Tavily's effective per-call cap), 30
distinct query angles, 4 meta passes, and a faster QUBO build (inverted
index — identical mapping, identical 0.05 threshold). Observed end to end:

- Telem: 50 results (auto-routed).
- Tavily: 40 wave rounds × up to 50 results + 4 meta passes → **1,010
  unique candidates** after dedupe, 35 extracted (top 40 by preliminary
  relevance).
- QUBO: **1,010 variables, 244,395 redundancy couplings, 100 annealing
  reads, best energy −10.9985, 55 articles in the best set, 3/100 reads
  converged to the optimum.** Total: ~43.8 s.
- Top article: "Latest News & Trends in Search Agents | IndianWeb2.com",
  relevance 0.909, z +1.48 — super frickin' amazing. Top 10 by relevance:
  0.899–0.909, all High reliability, mantra grounding 1.0.
- None of the top 10 made the best set — the redundancy penalty at this
  scale dominates the head of the ranking (ranks 5, 6 and 8 are the same
  Gadgets360 story in three URL variants). The best set of 55 is drawn
  entirely from outside the top 10. Convergence is low (3/100) at this
  size: the optimum is the best found, but most reads land elsewhere.
- The ~200-article ceiling from the earlier scale check is broken: it was
  a retrieval-rounds limit, not a provider limit. A first 35-round attempt
  landed at 887 unique; 40 rounds with broader angles cleared 1,010.

## Verified live test (Nov 14, ~12:20pm PT)

Query: **"AI search agents 2026"** (advanced depth, 3 wave rounds, mantra + meta-search on). Observed end to end:

- Telem: 50 results, providers tavily / exa / seltz (auto-routed).
- Tavily: 3 wave rounds × 20 results + 2 meta passes → 111 unique
  candidates after dedupe, 36 extracted (top 40 by preliminary relevance).
- QUBO: **111 variables, 3013 redundancy couplings, 100 annealing reads,
  best energy −2.9565, 17 articles in the best set, 31/100 reads converged
  to the optimum.** Total: ~19.5 s.
- Top 10 by relevance: 0.799–0.868, all High reliability, mantra grounding
  1.0. The redundancy penalty visibly works — the top 5 are near-identical
  "best AI search APIs" listicles and only one of them made the best set.
- Scale check on the same query: 5 rounds → 140 candidates, 19 selected,
  −3.2046, 11.6 s. 10 rounds (max) → 194 candidates, 8410 couplings,
  20 selected, −4.0921, 42/100 converged, 16.0 s. Raw calls grow faster
  than unique candidates — Tavily returns heavily overlapping results
  across angles — but the ~200 "ceiling" was only a rounds limit: see the
  1,010-article run above.

## Earlier verified test (Nov 14, ~12:00pm PT, pre-scale-up)

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
