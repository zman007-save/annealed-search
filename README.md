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
  and ranks across both. Articles found by both a wave round and the meta
  pass earn the +0.05 cross-validation bonus in the net score (below).
- **Net score** — one combined number per article: `net = relevance −
  redundancy_max (worst twin) + meta bonus + wave bonus`. Meta bonus +0.05 for
  cross-validation (wave + meta); wave bonus +0.01 per extra distinct wave
  round, max +0.05. The top 10 is ranked by net score. Redundancy here is
  the single most similar other article (max Jaccard), not the mean — the
  mean barely varies among top articles, so it let near-twins top the
  ranking while the annealer threw them out of the set.

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
- Net score (display ranking, same combined signal approximately): `net =
  relevance − redundancy_max + meta bonus + wave bonus`, where
  `redundancy_max` is the article's worst twin — its highest Jaccard
  similarity to any single other article (same similarities, same 0.05
  threshold as the QUBO couplings), meta bonus is +0.05 for articles found
  by both a wave round and the meta pass, and wave bonus is +0.01 per extra
  distinct wave round (max +0.05). The mean was tried first and failed:
  it barely varies among top articles (0.052–0.064), so net stayed a
  relevance ranking and the top 10 overlapped the best set 0/10. The worst
  twin is what actually knocks a top article out of the set, so it is what
  net charges. What remains different: the QUBO penalizes similarity to
  the *selected* set as it forms, net is a per-article standalone number —
  see the worst-twin run below for what that difference does to the top 10
  vs the best set.

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
TELEM_BASE_URL=https://hack.telem.ai/api
```

Get a Telem key at https://hack.telem.ai (sign in with Google →
project → API keys). **The hackathon uses the dedicated server
https://hack.telem.ai/api — a key issued on app.telem.ai returns 401
there** (verified Nov 14, 2:00pm PT: the old key 401'd on the hack
endpoint while returning 200 on router.telem.ai). The Tavily key is in
the Tavily dashboard. All participants get $100 of Telem credits.

The dashboard leads with the annealer's answer: the headline list is the
best set itself, ranked by net score within the set. Below it, a separate
"Highest scoring individuals" section shows the top 10 by net score as
individuals — explicitly not the set. Every card in both lists shows all
component scores (Tavily, mantra grounding, combined relevance, redundancy,
meta/wave bonuses, net) plus its bell-curve grade. The full pool follows
under "All articles".

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
- **Top-10 quality problem, found by Zach:** the #1 "article" above is a
  Blogger label page (`indianweb2.com/search/label/Search Agents`), not an
  article. Fixed by the URL filter — see the filtered re-run below.

## Verified live test — 1,010 articles, filtered re-run (Nov 14, ~1:15pm PT)

Same prompt and settings as the 1,010 run above — **"AI search agents 2026"**
(advanced depth, 40 wave rounds, max_results 50, mantra + meta-search on) —
with one change: a URL filter that runs before scoring. It drops listing
pages (search/label/tag/category/archive index pages), canonicalizes /amp
URLs onto the real article URL, and collapses near-identical titles
(title-token Jaccard ≥ 0.85) so one syndicated story can't take several
top-10 slots. Observed end to end:

- The filter removed 29 listing pages, 647 exact-URL duplicates after
  canonicalization, and 148 same/near-identical titles → **921 unique
  candidates** (vs 1,010 unfiltered), 33 extracted (top 40 by preliminary
  relevance).
- QUBO: **921 variables, 183,289 redundancy couplings, 100 annealing
  reads, best energy −9.8295, 52 articles in the best set, 4/100 reads
  converged to the optimum.** Total: ~34.9 s.
- Top 10 by relevance: 0.886–0.906, all High reliability, mantra grounding
  1.0. All ten are real articles from ten distinct domains — verified: no
  listing pages, no /amp URLs, no duplicate titles. Top article: "Google I/O
  2026: Google Revamps Search Experience With AI Agents, Multi-Modal
  Queries | Technology News" (Gadgets360), 0.906.
- Two honest iterations: the first filtered attempt dropped real articles
  whose paths contain a /search/ directory (e.g. Google's own Search I/O
  2026 blog post) — the rule was narrowed so "search" only counts with a
  label segment, a search query parameter, or a bare /search path. The second
  attempt still showed one syndicated story three times under slightly
  different titles ("Google's New AI Agents…" vs "Google's AI Agents…",
  title Jaccard 0.875), which the title-Jaccard rule then collapsed. Logs:
  `runs/run-1000-filtered-v1-2026-11-14.json` (844 candidates) and
  `runs/run-1000-filtered-v2-2026-11-14.json` (908 candidates).
- As in the unfiltered run, none of the top 10 made the best set — the
  52-article best set is drawn entirely from outside the top 10. Mantra
  grounding is still 1.0 across the whole top 10.

## Verified live test — 1,010 articles, combined net score (Nov 14, ~1:22pm PT)

Same prompt and settings as the filtered run — **"AI search agents 2026"**
(advanced depth, 40 wave rounds, max_results 50, mantra + meta-search on) —
with one change: every article now carries ONE combined net score, and the
top 10 is ranked by it instead of by relevance alone:

**net = relevance − redundancy_avg + meta bonus + wave bonus**, where
relevance = 0.6 × Tavily + 0.4 × mantra grounding; redundancy_avg is the
article's mean Jaccard similarity to the other articles (same similarities
and same 0.05 coupling threshold as the QUBO); meta bonus is +0.05 for
articles found by BOTH a wave round and the meta pass (opposite profile —
cross-validation, tracked from real ingest provenance, not guessed); wave
bonus is +0.01 per extra distinct wave round, max +0.05. Both bonuses are
small nudges by design — relevance and redundancy stay the main terms.
Every component stays visible per article in the API and the dashboard.
The Tavily parameter controls (search_depth, time_range, etc.) are NOT a
score component — they are retrieval knobs that shape the pool, not
properties of an article.

Observed end to end:

- **926 unique candidates** (33 extracted), 136 found by the meta pass,
  61 cross-validated (wave + meta), 231 in 2+ distinct wave rounds.
- QUBO: **926 variables, 184,278 redundancy couplings, 100 annealing
  reads, best energy −9.8576, 53 articles in the best set, 10/100 reads
  converged to the optimum.** Total: ~36.5 s.
- Top 10 by net score: 0.847–0.921, all High reliability, all real articles
  from ten distinct domains. Ranks 1–6 all earned the +0.05 meta bonus;
  ranks 1–3 and 5 also earned the full +0.05 wave bonus (12–14 distinct
  rounds each). Net-score distribution for the run: mean 0.596, σ 0.171.
- **Honest result: the overlap is still 0/10.** None of the new top 10
  made the best set. The best-selected article by net ranks 22nd; only 1
  selected article is in the top 25 by net, 3 in the top 50, 8 in the top
  100. The best set's mean net (0.657) is above the run mean (0.596), but
  the head of the net ranking and the annealer's set still diverge.
- Why: net uses redundancy_avg — the MEAN similarity to all 925 other
  articles — which barely varies among top articles (0.052–0.064), because
  most pairwise similarities are zero. So net is still mostly a relevance
  ranking with a bonus tilt. The annealer, by contrast, penalizes
  similarity to the *selected* articles specifically (1.2 × pairwise
  Jaccard): one near-twin (redundancy_max 0.12–0.23 for the top 10) is
  enough to knock a top article out. Net is a per-article standalone
  approximation; the QUBO is a joint optimization over the set — "good on
  its own" vs "a good addition to this set". The likely next step, if the
  lists should agree: rank by redundancy_max (worst twin) instead of the
  mean. Log: `runs/run-1000-combined-2026-11-14.json`.

## Verified live test — 1,010 articles, net score uses worst-twin redundancy (Nov 14, ~1:32pm PT)

Same prompt and settings as the combined run — **"AI search agents 2026"**
(advanced depth, 40 wave rounds, max_results 50, mantra + meta-search on) —
with two changes: the net score's redundancy term is now redundancy_max
(the worst twin) instead of redundancy_avg, and articles with an empty
title are dropped from the candidate pool before scoring (a result with no
title is not a real article — the combined run had five empty-title
ppc.land Telem hits, one of which sat at position 46 of the best-set
headline).

**net = relevance − redundancy_max + meta bonus + wave bonus**, where
redundancy_max is the article's highest Jaccard similarity to any single
other article (same similarities, same 0.05 coupling threshold as the
QUBO). The dashboard legend and the per-article net breakdown now show
the worst twin instead of the mean.

Observed end to end:

- **902 unique candidates** (34 extracted). Filter dropped 32 listing
  pages, 663 duplicate URLs, 132 duplicate titles, and 20 empty-title
  results. Zero empty-title articles remain in the candidates or the best
  set — the five empty-title ppc.land hits from the combined run are gone
  (the one ppc.land result in this run has a real title and is not
  selected).
- QUBO: **902 variables, 172,063 redundancy couplings, 100 annealing
  reads, best energy −9.1684, 50 articles in the best set, 6/100 reads
  converged to the optimum.** Total: ~39.5 s.
- Top 10 by net score: 0.759–0.823. Net-score distribution for the run:
  mean 0.489, σ 0.188.
- **Honest result: the overlap improved from 0/10 to 2/10.** Two of the
  top 10 are in the best set (ranks 2 and 6), and the best-selected
  article by net now ranks 2nd — up from 22nd. 4 selected articles are in
  the top 25 by net (was 1), 5 in the top 50 (was 3), 8 in the top 100
  (unchanged). The best set's mean net (0.561) is above the run mean
  (0.489). The lists still diverge: the worst-twin charge moved the
  ranking toward the set, but net remains a per-article standalone number
  while the QUBO is a joint optimization over the set — it penalizes
  similarity to the *selected* set as it forms, which no single-article
  score can reproduce. No further terms were stacked on to force the
  overlap; this is the measured result of the one formula change.
- Dashboard render check: the actual dashboard JS was executed in node
  against this run's log — the headline is exactly the 50 selected
  articles in net-descending order, the separate section is exactly the
  log's top 10 by net, and no card falls back to a bare URL as its title.
  Log: `runs/run-1000-maxred-2026-11-14.json`.

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
