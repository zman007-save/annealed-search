# Annealed Search — Dashboard & Demo README

**For the GPT site builder.** This document tells you what the product is, how the
dashboard works, and how to write accurate copy for the hosted demo site. Every
number below comes from the verified run logs in `runs/` and the code in
`app.py` — do not invent numbers, titles, or URLs. Source of truth for the
implementation is `app.py`; for the numbers, `runs/run-1000-combined-2026-11-14.json`
(the latest run) and `README.md`.

## 1. What it is

Annealed Search takes a query, pulls hundreds of articles with Telem AI and
Tavily, and uses simulated quantum annealing (a QUBO solved on the local
machine) to pick one best, least-redundant set of articles instead of a
long ranked list. Built for SearchHack (Telem AI), Sunnyvale, Nov 14, 2026;
submissions due 4:15pm PT the same day. One-line pitch: "Search is drowning
in results. We anneal them."

## 2. The dashboard and demo

**Run it locally:**

```bash
./run.sh            # creates .venv, installs requirements, starts uvicorn
# then open http://localhost:8000
```

It needs a `.env` file next to `app.py` with `TELEM_API_KEY` and
`TAVILY_API_KEY`. The keys are **not in this repo and must never be added**
(`.env` is gitignored). The hosted site must not embed keys either — it
links to the dashboard/demo video instead of running live searches itself.

**What the dashboard shows:**

- A big search box, parameter controls (search depth, time range, domains,
  max results, wave rounds, mantra and meta-search toggles), and an
  "⚛ Anneal it" button.
- Five animated stage cards that light up in sequence: 1 · Query
  understanding, 2 · Frequency wave, 3 · Mantra loop, 4 · Meta-search,
  5 · QUBO anneal. The anneal stage has a self-drawing energy trace —
  a canvas that draws the annealing settling from worst to best read.
- **Ann Nealer**, an animated cartoon quantum-annealer robot (spelling:
  A-N-N space N-E-A-L-E-R). She bobs while idle, buzzes through the
  stages, vibrates as the anneal settles, and celebrates when it finishes.
  She narrates in a speech bubble and shows the best energy on her belly
  display. Keep her in the site — she is the mascot.
- A clickable **top 10** (titles link to the source; clicking a card opens
  a preview pane with the extracted text and that article's bell curves).
- **Per-article scores with scale bars**: Tavily, mantra grounding,
  relevance, redundancy, and the combined net score — each with its
  bell-curve grade for that run.
- **Bell-curve grading tiers** (labels are relative to the run's own
  distribution; the raw score next to each is absolute): super frickin'
  amazing (≥ +1σ, top 15.9%), amazing (+0.5σ to +1σ, 15.0%), good
  (0 to +0.5σ, 19.1%), medium (−0.5σ to 0, 19.1%), medium rare
  (−1σ to −0.5σ, 15.0%), really frickin' bad (< −1σ, bottom 15.9%).
  For redundancy the scale is inverted (lower is better). Each tier shows
  its % of the curve and how many of this run's articles fall in it.
- A note the dashboard itself shows: **energy is only comparable within
  one run** — it scales with the number of articles, so a −9.86 on 926
  articles is not "better" than a −1.45 on 12. Compare convergence and
  the picks, not the raw energy.

**Demo script (60 seconds, for the video / live demo):**

1. (0:00) "Search is drowning in results. We anneal them." Type
   **"AI search agents 2026"**.
2. (0:10) Show the parameter controls — pick a depth and time range, turn
   the wave rounds up. Hit **Anneal it**.
3. (0:20) The stages light up: Telem auto-routes the query, Tavily pulls
   the articles across wave rounds, the mantra re-scores each one for
   grounding, the meta pass merges in.
4. (0:35) The QUBO: 926 variables, 184,278 couplings, 100 reads. The
   energy trace converges; the best set is highlighted with reliability
   badges.
5. (0:50) "Simulated on this laptop today — the same QUBO runs on a
   D-Wave QPU tomorrow."

## 3. Pulling articles

- **Telem AI** — one search call with auto-routing (`accuracy`) across
  providers (tavily, exa, seltz). In the latest run Telem returned
  50 results.
- **Tavily frequency / wave search** — retrieval oscillates between query
  angles and parameter profiles across rounds (fresh/shallow ↔ deep/broad),
  up to 40 rounds, 30 distinct angles, max 50 results per call. The
  latest run used 40 wave rounds + 4 meta passes.
- **Meta-search** — an extra pass with the opposite parameter profile,
  merged into the same pool. In the latest run 136 articles were found
  by the meta pass and 231 articles appeared in two or more distinct
  wave rounds.
- **URL filter** (runs before scoring) — drops listing/tag/category/archive
  index pages, canonicalizes `/amp` URLs onto the real article, and
  collapses near-identical titles (title-token Jaccard ≥ 0.85), so one
  syndicated story can't take several top-10 slots.
- **Real scale numbers** (all for the query "AI search agents 2026",
  advanced depth, 40 rounds, max 50): unfiltered run — **1,010 unique
  candidates**, 35 extracted, 43.8 s; filtered re-run — **921
  candidates**, 33 extracted, 34.9 s; latest combined-score run —
  **926 candidates**, 33 extracted, 36.5 s. Extracts run on the top 40
  articles by preliminary relevance, not on all candidates.

## 4. Scoring articles

Exact as implemented in `app.py` (the net-score formula below is live in
the code as of the latest run — it was added the same day, so describe
it as current, not as planned):

- **Relevance** = 0.6 × Tavily score + 0.4 × mantra grounding.
- **Mantra grounding** — the agent repeats the ORIGINAL prompt against
  each article and scores the overlap: how well the article grounds to
  the user's own query. That overlap is the reliability signal.
- **Redundancy** — Jaccard similarity between articles (title + text
  tokens). In the QUBO it is the quadratic penalty: `J_ij = 1.2 ×
  similarity(i, j)` when similarity is above 0.05.
- **Reliability tiers** (High / Medium / Low) are absolute cutoffs on
  relevance: High ≥ 0.6, Medium ≥ 0.35, Low below. They are not a
  separate signal — just a label on the relevance number.
- **Net score** (one combined number per article, and what the top 10
  is ranked by): net = relevance − redundancy (mean Jaccard similarity
  to the other articles) + meta bonus (+0.05 if the article was found by
  both a wave round and the meta pass — cross-validation under two
  different parameter profiles) + wave bonus (+0.01 per extra distinct
  wave round, max +0.05). Every component stays visible per article.
- **The QUBO, in one sentence:** one binary variable per article
  (1 = in the best set); the linear term `0.45 − relevance` rewards
  picking relevant articles, the quadratic term penalizes picking
  similar articles together, and the annealer minimizes total energy.
- **The annealer:** D-Wave Ocean SDK — `dimod` BQM +
  `dwave.samplers.SimulatedAnnealingSampler`, 100 reads, on CPU.
  The reported confidence signal is best energy + how many of the 100
  reads converged to it ("reads converged").

**Known limits — state them honestly, do not smooth them over:**

- Mantra grounding saturates at 1.0 across the whole top 10 on broad
  queries, so it does not discriminate among the best articles there.
- Convergence drops at large scale: 3/100 reads converged at 1,010
  variables, 4/100 at 921, 10/100 at 926. The best set is the best
  found, not a proven optimum.
- The top 10 and the best set are different things and they do not
  overlap in the big runs: in the latest combined run, **0 of the top
  10 by net score are in the 53-article best set**. The top 10 is the
  highest net-scoring articles; the best set is a joint optimization
  that trades relevance against redundancy across the whole set. Do not
  write copy claiming the top 10 *are* the best set.

## 5. Sponsor technology

- **Telem AI** — auto-routed search; 40% of the judging is "Use of
  Telem AI". One call, routes across providers. This is the piece the
  project is hardest to build without.
- **Tavily** — search + article extract, plus the parameter controls
  the dashboard exposes: `search_depth`, `country`, `include_domains`,
  `exclude_domains`, `time_range`, `max_results`.
- **D-Wave Ocean SDK** — `dimod` BQM + `dwave-samplers`, simulated
  annealing today, QPU-ready: the same BQM runs on a D-Wave QPU later.
  The 1 free QPU minute on the trial plan is **untouched and was not
  used** — never claim a QPU run happened.

## 6. Why it solves the problems

From the event's problem slides (six problems) — each mapped to the
feature that answers it, with the real run numbers:

- **Too much information** → 1,010 articles annealed down to one
  55-article best set (latest combined run: 926 → 53). The output is
  a set you can read, not a page of links.
- **Fragmented context** → wave rounds across 30 angles + the meta
  pass + dedupe and canonicalization merge everything into one ranked,
  de-duplicated set instead of scattered result pages.
- **Expensive at scale** → local simulated annealing, no QPU cost
  (the free QPU minute was never spent); the 1,010-article run took
  ~44 s end to end on a laptop, and the QUBO build uses an inverted
  index (verified bit-identical to the naive build) so 244,395
  couplings are handled in seconds.
- **Weak personalization** → mantra grounding ties every article back
  to the user's own original prompt, and the meta/wave bonuses reward
  articles that hold up across different angles and profiles.
- **Limited memory** → be honest here: the app has **no cross-session
  user memory** and this README must not claim it does. What it does
  have is per-run memory: every run is logged (`runs/*.json`) with its
  full scoreboard, and mantra grounding gives per-query memory of the
  original prompt — each article is scored against what *this* user
  actually asked, not a generic relevance model.
- **Low performance** → queries are routed to the right source by
  Telem auto-routing instead of one flat provider, and the inverted-
  index QUBO build plus sparse couplings (only similarities above
  0.05) keep the 1,000-article anneal to tens of seconds.
