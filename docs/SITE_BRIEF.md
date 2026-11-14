# Site brief — Annealed Search (for the GPT site builder)

Build a hosted marketing/demo site for **Annealed Search**, Zach Lafer's
SearchHack (Telem AI, Nov 14, 2026) project. Source of truth is this repo:
`app.py` + `static/` is the working dashboard, `README.md` is the technical
write-up, `runs/*.json` are real verified run logs, `docs/` holds the use-case
documents and the Devpost submission drafts.

## What it is

Annealed Search turns a flood of articles into one best set. A query goes
through Telem AI (auto-routed search) and Tavily (wave search + article
extract), then a QUBO — one binary variable per article, relevance rewarded,
redundancy penalised — is solved by local simulated annealing (D-Wave Ocean
SDK). Simulated today, QPU-ready: the same model runs on a D-Wave QPU later.
The free QPU minute was never used. It is a smarter-search agent: retrieval
beyond keywords, with grounding you can see.

## Sections the site should have

1. **Hero** — the idea in one line ("Search is drowning in results. We
   anneal them."), the query box, and a button linking to the live dashboard
   demo. Keep the hero short; the dashboard is the star.
2. **How it works** — the five stages, in order, each with a one-line
   explanation: (1) Telem retrieval — one auto-routed call across providers
   (tavily, exa, seltz); (2) Frequency wave — retrieval oscillates between
   query angles and depth profiles across rounds, fresh/shallow ↔ deep/broad,
   instead of one flat query; (3) Meta-search — an extra pass with the
   opposite parameter profile, ranked across both; (4) Mantra grounding —
   the original prompt is repeated against each article to score how well
   it grounds to it (High / Medium / Low reliability); (5) Anneal — the
   QUBO is solved with 100 simulated-annealing reads and the lowest-energy
   set wins.
3. **Live dashboard** — embed or prominently link the dashboard
   (`static/index.html` in this repo). Show: the parameter controls
   (search_depth, country, include/exclude domains, time_range,
   max_results, plus wave rounds, mantra, meta-search), the animated stage
   cards, the energy trace, and the clickable top 10 with per-article
   scores.
4. **Use cases** — from `docs/annealed-search-use-cases-master.pdf`. Lead
   with the scoreboard, including the headline run: **1,010 articles**
   ("AI search agents 2026", 40 wave rounds + 4 meta passes, 1,010 QUBO
   variables, 244,395 couplings, best energy −10.9985, 55 articles in the
   best set, 3/100 reads converged, 43.8 s). Top article: "Latest News &
   Trends in Search Agents | IndianWeb2.com", relevance 0.909 — super
   frickin' amazing. Note that energy only compares within one run, never
   across runs.
5. **Score tiers (bell curve)** — show the grading scale with each tier's
   share of the curve: super frickin' amazing 15.9%, amazing 15.0%, good
   19.1%, medium 19.1%, medium rare 15.0%, really frickin' bad 15.9%.
   Grades are relative to each run's own distribution (z-scores), not
   absolute cutoffs. **Ann Nealer** — the animated quantum-annealer robot
   mascot — guides the visitor through the stages; keep her name spelled
   exactly "Ann Nealer" everywhere.
6. **Links** — the Devpost project (see `docs/DEVPOST_DRAFTS.md` for the
   submission name, pitch, and tags) and this GitHub repo.

## Design notes

- Dark theme matching the dashboard (deep navy/purple, glowing accents).
  Playful but credible: this is a real working system with real run logs,
  not a mockup. Use the actual numbers from `runs/` and `README.md`;
  do not invent scores, articles, or results.
- Every article shown must link out to its source URL.

## Do NOT include

- **No API keys anywhere.** The Telem (`tlm_…`) and Tavily (`tvly-…`)
  keys live only in a local `.env` that is gitignored and never committed.
  The site must link to the dashboard / demo video instead of embedding
  any key. Never print, display, or ship a key in any page, file, or
  example code.
- No claim the QPU was used — it was simulated locally; the QPU is a
  future step.
