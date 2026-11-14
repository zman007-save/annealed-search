# Devpost Submission Drafts — annealed-search (SearchHack)

Submission 1303383, account zacharylafer / zacharylafer@gmail.com.
Deadline: Sat Nov 14, 2026, 4:15pm PT.
Status: DRAFTS ONLY — nothing sent, submitted, or filled in. Prepared Nov 14, ~12:38pm PT.

## 1. Project name (51 / 60 characters, verified)

**Annealed Search — Quantum Annealing for AI Search**

Alternative (44 / 60): **Annealed Search: QUBO-Powered Article Search**

## 2. Elevator pitch (194 / 200 characters, verified)

**Annealed Search turns a flood of articles into one best set: Telem AI routes the query, Tavily pulls hundreds of articles, and a QUBO solved by simulated annealing picks the least-redundant set.**

## 3. About the project (Markdown)

```markdown
## Inspiration

AI search today drowns you in results. A query returns hundreds of articles
that all say the same thing, ranked one by one — and the ranking itself is
guessed at by whichever source happened to answer. The SearchHack problem
statement says it plainly: too much information, fragmented context,
expensive retrieval, weak personalization, limited memory, low performance.
We wanted a search layer that doesn't just rank articles — it *optimizes the
whole set*, the way a quantum annealer finds the lowest-energy state of a
system.

## What it does

Annealed Search takes a query and returns one annealed best set of articles
— the most relevant, least redundant collection, chosen as a set, not as a
ranked list.

1. **Query understanding** — the query is expanded into 10 distinct angles
   for the frequency wave.
2. **Retrieval** — Telem AI auto-routes the query across providers, and
   Tavily runs wave rounds plus meta-search, pulling up to 1,010 unique
   candidate articles per query (40 wave rounds).
3. **Mantra grounding** — the agent repeats the ORIGINAL prompt against
   every article and scores how well each one grounds to it. That's the
   reliability-of-output score: High / Medium / Low.
4. **QUBO + simulated annealing** — one binary variable per article, solved
   locally with the D-Wave Ocean SDK. The annealer minimizes energy: relevance
   pulls articles in, redundancy pushes near-duplicates out.
5. **Dashboard** — the headline is the annealer's best set itself, ranked
   by net score within the set, with a separate "Highest scoring
   individuals" section for the top 10 by net score. Per-article feature
   scores, bell-curve grading (from "super frickin' amazing" to "really
   frickin' bad"), clickable source links and article previews, and Ann
   Nealer, our animated quantum-annealer robot, who narrates each stage.
   One combined net score per article: relevance − worst-twin redundancy
   + meta/wave bonuses (see below).

## How we built it — Telem AI (the core of the build)

Telem AI is the query-understanding and retrieval backbone. Every search
starts with **one Telem call with auto-routing set to `accuracy`**, which
routes the query across providers — tavily, exa, seltz — and returns the best
grounded results instead of one provider's guess. On our flagship run
("AI search agents 2026"), Telem returned 50 results across those three
providers. Telem's routing is what makes the pipeline hard to build without
it: the annealer can only optimize what retrieval actually found, and
auto-routing is what finds the right sources. This is also what the
dashboard's first pipeline stage shows lighting up.

## How we built it — Tavily

Tavily is the retrieval engine, and we use it in three ways:

- **Wave (frequency) search** — up to 40 rounds, each a different query
  angle with an alternating profile (fresh/shallow ↔ deep/broad, cycling
  time range and topic), so rounds return *different* articles instead of
  the same ones. The kickoff slides' Tavily controls — `search_depth`,
  `country`, `include_domains`, `exclude_domains`, `time_range`,
  `max_results` — are all exposed as UI parameters.
- **Meta-search** — four extra passes with the opposite parameter profile,
  merged and ranked with the rest. Articles found by both a wave round
  and the meta pass earn a +0.05 cross-validation bonus in the net score;
  articles appearing in multiple distinct wave rounds earn up to +0.05.
- **Extract** — full article text for the most promising candidates
  (33–35 per run at the 1,000-article scale), which feeds the mantra
  grounding and the redundancy measure. A URL filter drops listing/tag/
  category pages, canonicalizes /amp URLs, and collapses identical titles
  before scoring, and articles with an empty title are dropped entirely —
  so the top 10 are real articles, not index pages or one story in three
  URL variants.

Tavily's per-result score is also half the relevance formula:
`relevance = 0.6 · Tavily score + 0.4 · mantra grounding`.

## How we built it — the QUBO

One binary variable `x_i` per article (`x_i = 1` if it's in the best set):

- Linear term: `h_i = 0.45 − relevance_i` — relevance rewards selection,
  0.45 is the cost of picking an article.
- Quadratic term: `J_ij = 1.2 · Jaccard(title+text tokens of i, j)` when
  similarity is above 0.05 — the redundancy penalty. Similar articles push
  each other out of the set.
- Solved with `dwave.samplers.SimulatedAnnealingSampler`, 100 reads, on
  CPU. **Simulated today, QPU-ready: the same BQM runs on a D-Wave QPU
  later.** The free QPU minute was never touched.
- **Net score** — one combined number per article for display ranking:
  `net = relevance − redundancy_max + meta bonus + wave bonus`, where
  `redundancy_max` is the worst twin (the single most similar other
  article), meta bonus is +0.05 for cross-validation (wave + meta), and
  wave bonus is +0.01 per extra distinct wave round (max +0.05). The
  QUBO penalizes similarity to the *selected* set as it forms, while net
  is a per-article number — so the top 10 by net and the best set are
  different things, and the dashboard shows both separately.

## Verified results (all live runs, Nov 14)

- **Scale** — the same query at 40 rounds reaches 1,010 unique
  candidates, 244,395 couplings, best energy −10.9985, 55 selected, in
  43.8 s. After the URL filter: 921 candidates, best energy −9.8295, 52
  selected. With the combined net score: 926 candidates, best energy
  −9.8576, 10/100 converged, 53 selected. With worst-twin net: 902
  candidates, best energy −9.1684, 6/100 converged, 50 selected, and the
  top 10 by net now overlaps the best set 2/10 (up from 0/10) — the
  best-selected article by net ranks 2nd.
- **Earlier runs** — "quantum computing breakthroughs 2026": 12 variables,
  49 couplings, best energy −1.4529, **100/100 reads converged**, 6
  selected. "AI search personalization memory": best energy −1.4125,
  99/100 converged, 5 selected. "AI search agents 2026" (first big run):
  111 candidates, 3,013 couplings, best energy −2.9565, 31/100 converged,
  17 selected, in 19.5 s. The top 5 articles by relevance were
  near-identical "best AI search APIs" listicles — and only one of them
  made the best set. That's the redundancy penalty doing its job: the
  annealer picks a *set*, not just the top-ranked singles.

## Challenges we ran into

- **Convergence drops at scale.** On 12 variables the annealer converges
  100/100 reads; on ~1,000 variables it was 3–10/100. It still finds the
  optimum, just less often per read — expected on a much larger landscape,
  and the energy trace on the dashboard shows it.
- **The top 10 and the best set are different things.** A per-article
  score can't reproduce a joint set optimization: even with worst-twin
  redundancy in the net score, the top 10 overlaps the best set only 2/10
  (up from 0/10). The dashboard shows both separately instead of
  pretending they agree.
- **Ranking can be fooled by non-articles.** Our first 1,010-article run
  ranked a Blogger label page #1 — a listing page full of the query's
  keywords. A URL filter (listing/tag/category pages, /amp variants,
  identical titles, empty titles) now runs before scoring.
- **Mantra grounding saturates on broad queries.** On "AI search agents
  2026" the top 10 all scored grounding 1.0 — every query token appears in
  every top article. The metric discriminates better on narrower queries.
- **Energy is only comparable within a run.** It scales with article
  count, so −2.96 on 111 articles doesn't "beat" −1.45 on 12. The
  dashboard says this plainly instead of pretending otherwise.

## What we learned

Ranking articles one by one is not the same problem as choosing a good
*set*. The moment you add a redundancy term, the annealer starts doing
something no ranked list does: it sacrifices a slightly-more-relevant
article to keep the set diverse. And a grounding score that repeats the
original prompt per article is a cheap, honest reliability signal — it
catches articles that are on-topic in keywords but off-prompt in substance.
Finally: the score that matters most for a solver isn't the best energy,
it's how often the reads converge on it.
```

## 4. Built-with tags (17 / 25)

Python, FastAPI, Uvicorn, D-Wave Ocean SDK, dimod, dwave-samplers, Telem AI, Tavily, QUBO, Simulated Annealing, JavaScript, HTML, CSS, httpx, python-dotenv, JSON, GitHub

## 5. "Try it out" links

- GitHub repo: https://github.com/zman007-save/annealed-search

> ⚠️ **FLAG — BLOCKER: that repo is currently PRIVATE.** Judges clicking the link from Devpost would hit a 404 / "not found" page and could not see the code. **Zach must make the repo public (GitHub → Settings → Danger Zone → Change visibility → Public) before submitting.** Do not submit with a private repo link. The `.env` file is gitignored and is not in the commit, so making the repo public does not expose any API keys.

## Still missing / blocked on Zach — do NOT attempt without him

1. **Video demo link (required by Devpost).** Needs recording + upload to YouTube or Vimeo as Unlisted, then the link pasted into the form. A 60-second script already exists in `~/workspace/searchhack/README.md` ("Demo script" section). SearchHack states no video length limit; Devpost's general guidance is under 5 minutes.
2. **Thumbnail image (required).** JPG/PNG/GIF, 5 MB max, 3:2 ratio. Suggestion: a screenshot of the finished redesigned dashboard (bell-curve tiers + Ann Nealer) once the redesign lands and is verified — do not use the old dashboard.
3. **Delete the stray wrong-account draft 1303533.** The Devpost browser task is waiting on Zach to enter the zachary294 (zachary@brainmatch.app) login himself via the secure sign-in card. No saved login exists. Only Zach can do this step.
4. **Luma check-in — NOT approved.** Devpost's Nov 14 11:10am email says register at https://luma.com/e13wf1bd and only teams where every builder checked in as an attendee are judged. Zach's earlier "No" was ambiguous, so this is **not** treated as approved. Needs his explicit yes before anyone registers him.
5. **Make the GitHub repo public** (see the flag above) — Zach's decision, his account.
