# Annealed Search — verified live runs (source data for the use-case document)

Project: annealed-search (SearchHack, Telem AI, Nov 14, 2026). Private repo:
https://github.com/zman007-save/annealed-search

## Method (all runs)

- Query → Telem AI search (auto-routing across providers) + Tavily search
  (wave rounds) + Tavily extract.
- Mantra grounding: the ORIGINAL prompt is repeated against each article and
  scored by token overlap with the article. Reliability badge: High / Medium /
  Low.
- Relevance per article = 0.6 * Tavily score + 0.4 * mantra grounding.
- QUBO: one binary variable per article. Linear term h_i = 0.45 − relevance_i
  (0.45 is the cost of picking an article). Quadratic term
  J_ij = 1.2 * Jaccard(title+text tokens of i, j) when similarity > 0.05
  (redundancy penalty). Objective: minimize energy.
- Solver: dwave.samplers.SimulatedAnnealingSampler, 100 reads, on CPU.
  Simulated today, QPU-ready: the same BQM runs on a D-Wave QPU later.
  The free QPU minute is never touched.

## Run 1 — "quantum computing breakthroughs 2026"

Advanced depth, 3 wave rounds, mantra + meta-search on. Nov 14, ~12:00pm PT.

- Telem: 15 results, providers tavily / exa / seltz (auto-routed).
- Tavily: 3 wave rounds x 8 results + 1 meta pass → 28 candidates, 8 extracted.
- QUBO: 12 variables, 49 redundancy couplings, 100 annealing reads.
- Best energy: −1.4529. Best set: 6 articles. Converged: 100/100 reads.
- Total run time: ~38 s.

## Run 2 — "AI search personalization memory"

- Candidates: 29. Best set: 5 articles.
- Best energy: −1.4125. Converged: 99/100 reads.
- Total run time: ~19 s.
- The redundancy penalty visibly worked: two near-duplicate articles were
  both kept out of the best set.

## Run 3 — "AI search agents 2026" (scaled run)

Advanced depth, 3 wave rounds, mantra + meta-search on. Nov 14, ~12:20pm PT.

- Candidates retrieved: 111 unique (Telem 50 across tavily/exa/seltz +
  Tavily 3 rounds x 20 + 2 meta passes, deduped).
- Extracted: 36.
- QUBO: 111 variables, 3,013 couplings, 100 reads.
- Best energy: −2.9565. Converged: 31/100 reads. Best set: 17 articles.
- Run time: 19.5 s.
- Reliability: 57 High / 51 Medium / 3 Low.

### Top 10 by relevance (all mantra grounding 1.0, all High)

| Rank | Relevance | Article | Selected |
| --- | --- | --- | --- |
| 1 | 0.868 | Best AI Search Engines for Agents and Workflows in 2026 | No |
| 2 | 0.861 | Best AI Search APIs for Agents 2026 \| Context Studios | No |
| 3 | 0.859 | Web Search for Agents in 2026 | No |
| 4 | 0.857 | Best Web Search APIs & MCPs for AI Agents 2026 | No |
| 5 | 0.847 | AI agents news 2026: Key Trends and Developments | No |
| 6 | 0.844 | Best web search APIs and MCPs for AI agents in 2026, Braintrust | Yes |
| 7 | 0.837 | The 10 Best AI Agent Search Tools (August 2026) | No |
| 8 | 0.833 | The Best AI Tools for Research in 2026 | No |
| 9 | 0.813 | How to use Google's new AI agents… \| TechCrunch | No |
| 10 | 0.799 | AI agent trends 2026 report | Yes |

Note: the top 5 are near-identical "best AI search APIs" listicles and only
one of them made the best set — the redundancy penalty doing its job. The
annealer picks a SET, not just the top-ranked singles.

### Scale checks (same query, more rounds)

| Rounds | Candidates | Variables / couplings | Best energy | Converged | Selected | Time |
| --- | --- | --- | --- | --- | --- | --- |
| 3 | 111 | 111 / 3,013 | −2.9565 | 31/100 | 17 | 19.5 s |
| 5 (new default) | 140 | 140 / 4,324 | −3.2046 | 24/100 | 19 | 11.6 s |
| 10 (max) | 194 | 194 / 8,410 | −4.0921 | 42/100 | 20 | 16.0 s |

### Honest caveats

- Convergence drops at scale: 31/100 on the 111-variable run vs 100/100 on
  the old 12-variable runs. The annealer still finds the optimum, just less
  often per read — expected on a larger landscape.
- ~200 unique articles is the practical ceiling for one query: raw calls grow
  faster than unique candidates because Tavily returns heavily overlapping
  results across angles.
- Mantra grounding saturates at 1.0 on the top 10 for this broad query (all
  query tokens appear in every top article) — the metric discriminates better
  on narrower queries.
- Meta passes are merged into the candidate pool but aren't itemized in the
  dashboard's per-round stage list yet.

## Run 4 — "AI search agents 2026" (redesigned dashboard verification)

Advanced depth, 3 wave rounds, mantra + meta-search on. Nov 14, ~12:35pm PT.
First run against the redesigned dashboard (per-article feature scores,
bell-curve grading, Ann Nealer mascot).

- Candidates retrieved: 124 unique (Telem 50 across tavily/exa/seltz +
  Tavily 3 rounds x 20 + 2 meta passes, deduped).
- Extracted: 37.
- QUBO: 124 variables, 3,776 couplings, 100 reads.
- Best energy: −3.0795. Converged: 14/100 reads. Best set: 16 articles.
- Run time: 9.7 s.
- Grading distributions (this run): Tavily mean 0.544, σ 0.139 (n=74 —
  Telem-routed articles have no Tavily score); mantra mean 0.804,
  σ 0.203; relevance mean 0.637, σ 0.120; redundancy mean 0.129, σ 0.060.
- Relevance tier counts: super frickin' amazing 24, amazing 26, good 8,
  medium 14, medium rare 43, really frickin' bad 9.
- Top 10 by relevance: all real source URLs, all 10 with extract text,
  1 selected. #1: 0.868, "Best AI Search Engines for Agents and
  Workflows in 2026" (z +1.92, super frickin' amazing, not selected —
  redundancy vs the other listicles kept it out).

## How to add a new result (running-document protocol)

1. Run the query in the dashboard (or via the API) and record: prompt,
   settings (depth, wave rounds, mantra/meta on/off), candidates retrieved,
   extracted, QUBO variables/couplings, best energy, convergence (x/100),
   best-set size, run time, reliability counts.
2. Record the top 10 by relevance with scores and selected/not.
3. Note anything the run proves (e.g. duplicates excluded, grounding
   behaviour) and any caveat.
4. Append as a new use-case section; do not rewrite earlier sections.
