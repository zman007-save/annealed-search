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
- Net score per article (from Run 5c on) = relevance − redundancy_avg
  (mean Jaccard similarity to the other articles) + meta bonus + wave
  bonus. Meta bonus +0.05 for articles found by BOTH a wave round and the
  meta pass (opposite profile — cross-validation, tracked at ingest).
  Wave bonus +0.01 per extra distinct wave round, max +0.05. The top 10
  is ranked by net score from Run 5c on; earlier runs ranked it by
  relevance. Every component stays visible per article.
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

## Run 5 — "AI search agents 2026" (1,010 articles, scale run)

Advanced depth, 40 wave rounds, max_results 50, mantra + meta-search on.
Nov 14, ~12:53pm PT. Scale-up: per-call max_results 20 → 50, 30 distinct
query angles, 4 meta passes, inverted-index QUBO build (identical mapping,
identical 0.05 threshold). Breaks the ~200-article ceiling claimed in Run 3's
caveats — that was a retrieval-rounds limit, not a provider limit. A first
35-round attempt landed at 887 unique; 40 rounds with broader angles
cleared 1,010.

- Telem: 50 results, providers tavily / exa / seltz (auto-routed).
- Tavily: 40 wave rounds x up to 50 results + 4 meta passes → 1,010 unique
  candidates after dedupe, 35 extracted (top 40 by preliminary relevance).
- QUBO: 1,010 variables, 244,395 redundancy couplings, 100 annealing reads.
- Best energy: −10.9985. Best set: 55 articles. Converged: 3/100 reads.
- Total run time: ~43.8 s.
- Reliability: 668 High / 297 Medium / 45 Low.

### Top 10 by relevance (all mantra grounding 1.0, all High)

| Rank | Relevance | Article | Selected |
| --- | --- | --- | --- |
| 1 | 0.909 | Latest News & Trends in Search Agents | IndianWeb2.com — https://www.indianweb2.com/search/label/Search%20Agents | No |
| 2 | 0.907 | 10 Best AI Search Tools for Agents in 2026: Ranked — https://www.scrapeless.com/en/blog/best-ai-search-tools-for-agents | No |
| 3 | 0.906 | Google I/O 2026: Google Revamps Search Experience With AI Agents, Multi-Modal Queries | Technology News — https://www.gadgets360.com/ai/news/google-io-2026-search-box-ai-agents-multi-modal-queries-gemini-11521202 | No |
| 4 | 0.906 | AI search news June 2026: Google agents and fragmentation — https://www.bushnote.com/articles/ai-search-news-june-2026 | No |
| 5 | 0.905 | Google I/O 2026: AI Agents in Search to Deliver Smarter Personalised Results | Technology News — https://www.gadgets360.com/how-to/news/google-io-2026-search-information-agents-rollout-features-news-11521074 | No |
| 6 | 0.904 | Google I/O 2026: AI Agents in Search to Deliver Smarter Personalised Results | Technology News — https://www.gadgets360.com/how-to/news/google-io-2026-search-information-agents-rollout-features-11521074/amp | No |
| 7 | 0.904 | Best Search Tools for AI Agents in 2026 - Plushcap — https://plushcap.com/content/firecrawl/blog/firecrawl-best-search-tools-for-ai-agents-in-2026 | No |
| 8 | 0.902 | Google I/O 2026: AI Agents in Search to Deliver Smarter Personalised Results | Technology News — https://www.gadgets360.com/how-to/news/google-io-2026-search-information-agents-rollout-features-11521074 | No |
| 9 | 0.902 | How to Use Google Search Agents: 24/7 AI Monitors | AgenticWire News — https://www.agenticwire.news/article/google-search-agents-how-to-use | No |
| 10 | 0.899 | AI News May 21 2026: Google IO Gemini 3.5 & AI Search Agents — https://mrreviewai.com/ai-news-digest-may-21-2026 | No |

Top-10 quality problem (found by Zach, fixed in Run 5b): the #1 "article"
above is a Blogger label page (indianweb2.com/search/label/Search Agents),
not an article, and ranks 5, 6 and 8 are the same Gadgets360 story in three
URL variants. None of the top 10 made the best set — the 55-article best set
is drawn entirely from outside the top 10.

## Run 5b — "AI search agents 2026" (filtered re-run, 921 articles)

Same prompt and settings as Run 5, ~1:15pm PT, with one change: a URL filter
that runs before scoring. It drops listing pages (search/label/tag/category/
archive index pages), canonicalizes /amp URLs onto the real article URL, and
collapses near-identical titles (title-token Jaccard ≥ 0.85) so one syndicated
story can't take several top-10 slots.

- Filter removed: 29 listing pages, 647 exact-URL duplicates after
  canonicalization, 148 same/near-identical titles → 921 unique candidates
  (vs 1,010 unfiltered), 33 extracted.
- QUBO: 921 variables, 183,289 redundancy couplings, 100 annealing reads.
- Best energy: −9.8295. Best set: 52 articles. Converged: 4/100 reads.
- Total run time: ~34.9 s.
- Reliability: 562 High / 302 Medium / 57 Low.

### Top 10 by relevance (all mantra grounding 1.0, all High)

| Rank | Relevance | Article | Selected |
| --- | --- | --- | --- |
| 1 | 0.906 | Google I/O 2026: Google Revamps Search Experience With AI Agents, Multi-Modal Queries | Technology News — https://www.gadgets360.com/ai/news/google-io-2026-search-box-ai-agents-multi-modal-queries-gemini-11521202 | No |
| 2 | 0.906 | AI search news June 2026: Google agents and fragmentation — https://www.bushnote.com/articles/ai-search-news-june-2026 | No |
| 3 | 0.902 | How to Use Google Search Agents: 24/7 AI Monitors | AgenticWire News — https://www.agenticwire.news/article/google-search-agents-how-to-use | No |
| 4 | 0.899 | AI News May 21 2026: Google IO Gemini 3.5 & AI Search Agents — https://mrreviewai.com/ai-news-digest-may-21-2026 | No |
| 5 | 0.897 | Google's New AI Agents: Revolutionizing Search with Continuous Updates (2026) — https://promisedlanddesign.com/article/google-s-new-ai-agents-revolutionizing-search-with-continuous-updates | No |
| 6 | 0.893 | AI search and agents news, 22 October 2026 | Aiso — https://www.getaiso.com/news/2026-10-22 | No |
| 7 | 0.892 | Top 5 AI search trends for 2026 - Blue Ocean Media — https://blueoceanmedia.co.uk/blog/top-5-ai-search-trends-for-2026 | No |
| 8 | 0.89 | 10 Best AI Search Tools for Agents in 2026 — https://oxylabs.io/blog/top-ai-search-tools | No |
| 9 | 0.89 | Best AI Agent Software for Enterprise Search (2026 Guide) — https://www.gosearch.ai/blog?p=5091 | No |
| 10 | 0.886 | Best Web Search APIs for AI Agents in 2026: Honest Comparison | Parallel — https://parallel.ai/ai/articles/the-honest-2026-comparison-web-search-apis-for-ai-agents | No |

Verified clean: ten real articles from ten distinct domains — no listing
pages, no /amp URLs, no duplicate titles. Top article: "Google I/O 2026:
Google Revamps Search Experience With AI Agents, Multi-Modal Queries |
Technology News" (Gadgets360), 0.906. None of the top 10 made the best set —
same pattern as Run 5; the 52-article best set is drawn entirely from
outside the top 10. Mantra grounding is still 1.0 across the whole top 10.

### Two honest iterations

- v1 (844 candidates): the first filter dropped real articles whose paths
  contain a /search/ directory (e.g. Google's own Search I/O 2026 blog
  post). The rule was narrowed so "search" only counts with a label segment,
  a search query parameter, or a bare /search path. Log:
  runs/run-1000-filtered-v1-2026-11-14.json.
- v2 (908 candidates): still showed one syndicated story three times under
  slightly different titles ("Google's New AI Agents…" vs "Google's AI
  Agents…", title Jaccard 0.875; the pair's content redundancy was 0.585),
  which the title-Jaccard rule then collapsed. Log:
  runs/run-1000-filtered-v2-2026-11-14.json.

## Run 5c — "AI search agents 2026" (combined net score, 926 articles)

Same prompt and settings as Run 5b, ~1:22pm PT, with one change: every
article now carries ONE combined net score and the top 10 is ranked by it.

**net = relevance − redundancy_avg + meta bonus + wave bonus.** Meta bonus
+0.05 for articles found by BOTH a wave round and the meta pass (opposite
profile — cross-validation, tracked from real ingest provenance: the meta
results are now ingested separately instead of being merged into the wave
rounds). Wave bonus +0.01 per extra distinct wave round, max +0.05
(distinct rounds are tracked at ingest — dedupe used to throw reappearances
away). Both bonuses are small nudges by design. The Tavily parameter
controls are NOT a score component: they shape the pool, not the article.

- Candidates: 926 unique (33 extracted). Meta pass found 136 of them;
  61 cross-validated (wave + meta); 231 in 2+ distinct wave rounds.
- QUBO: 926 variables, 184,278 redundancy couplings, 100 annealing reads.
- Best energy: −9.8576. Best set: 53 articles. Converged: 10/100 reads.
- Total run time: ~36.5 s.
- Reliability: 563 High / 305 Medium / 58 Low.
- Net-score distribution: mean 0.596, σ 0.171 (n=926); range −0.001 to 0.921.

### Top 10 by net score (all High, all real articles, ten distinct domains)

| Rank | Net | Rel. | Red. avg | Meta+ | Wave+ | Rounds | Article | Selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.921 | 0.881 | 0.060 | 0.05 | 0.05 | 12 | AI Search Agents in 2026: The Future of Google Search \| Xenors — https://xenors.in/tech/ai-search-agents-future-of-search-2026 | No |
| 2 | 0.884 | 0.844 | 0.060 | 0.05 | 0.05 | 14 | 7 Best AI Search Engines for Developers & AI Agents (2026) \| TinyFish Blog — https://www.tinyfish.ai/blog/best-ai-search-engine | No |
| 3 | 0.881 | 0.836 | 0.055 | 0.05 | 0.05 | 13 | Best Web Search APIs & MCPs for AI Agents 2026 — https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents | No |
| 4 | 0.875 | 0.882 | 0.057 | 0.05 | 0.00 | 1 | Get Cited by AI in 60 Days. AI Search Trends 2026 for Teams - Cairrot — https://cairrot.com/blog/ai-search-trends | No |
| 5 | 0.873 | 0.837 | 0.064 | 0.05 | 0.05 | 12 | The 10 Best AI Agent Search Tools (August 2026): Features, Tradeoffs, and Use Cases — https://mastra.ai/articles/best-ai-agent-search-tools | No |
| 6 | 0.859 | 0.861 | 0.062 | 0.05 | 0.01 | 2 | Ai agents news 2026: Key Trends and Developments- Drive Cool Cars — https://drivecoolcars.co.uk/ai-agents-news-2026 | No |
| 7 | 0.857 | 0.868 | 0.061 | 0.00 | 0.05 | 14 | Best AI Search Engines for Agents and Workflows in 2026 — https://www.firecrawl.dev/blog/best-ai-search-engines-agents | No |
| 8 | 0.852 | 0.906 | 0.054 | 0.00 | 0.00 | 1 | Google I/O 2026: Google Revamps Search Experience With AI Agents, Multi-Modal Queries \| Technology News — https://www.gadgets360.com/ai/news/google-io-2026-search-box-ai-agents-multi-modal-queries-gemini-11521202 | No |
| 9 | 0.852 | 0.906 | 0.054 | 0.00 | 0.00 | 1 | AI search news June 2026: Google agents and fragmentation — https://www.bushnote.com/articles/ai-search-news-june-2026 | No |
| 10 | 0.847 | 0.899 | 0.052 | 0.00 | 0.00 | 1 | AI News May 21 2026: Google IO Gemini 3.5 & AI Search Agents — https://mrreviewai.com/ai-news-digest-may-21-2026 | No |

### Honest result: top-10 / best-set overlap is still 0/10

None of the new top 10 made the best set. The best-selected article by net
ranks 22nd; only 1 selected article is in the top 25 by net, 3 in the top
50, 8 in the top 100. The best set's mean net (0.657) is above the run mean
(0.596), but the head of the net ranking and the annealer's set still
diverge. Only 1 of the 53 selected articles is cross-validated and only 8
carry a wave bonus — the bonuses lift articles up the net ranking, but the
annealer still does not select them.

Why: net uses redundancy_avg — the MEAN similarity to all 925 other
articles — which barely varies among top articles (0.052–0.064), because
most pairwise similarities are zero. So net is still mostly a relevance
ranking with a bonus tilt. The annealer penalizes similarity to the
*selected* articles specifically (1.2 × pairwise Jaccard): one near-twin
(redundancy_max 0.121–0.227 for the top 10) is enough to knock a top
article out. Net is a per-article standalone approximation; the QUBO is a
joint optimization over the set — "good on its own" vs "a good addition to
this set". Likely next step if the lists should agree: rank by
redundancy_max (worst twin) instead of the mean. Log:
runs/run-1000-combined-2026-11-14.json.

## Run 5d — "AI search agents 2026" (net score uses worst-twin redundancy, 902 articles)

Same prompt and settings as Run 5c, ~1:32pm PT, with two changes: the net
score's redundancy term is now redundancy_max (worst twin) instead of
redundancy_avg, and articles with an empty title are dropped from the
candidate pool before scoring (the combined run had five empty-title
ppc.land Telem hits, one of which sat at position 46 of the best-set
headline; the dashboard's URL-as-title fallback is now only a safety net
and no longer triggers).

**net = relevance − redundancy_max + meta bonus + wave bonus.** Meta bonus
+0.05 for cross-validation (wave + meta); wave bonus +0.01 per extra
distinct wave round, max +0.05. Both bonuses unchanged.

- Candidates: 902 unique (34 extracted). Filter dropped 32 listing pages,
  663 duplicate URLs, 132 duplicate titles, and 20 empty-title results.
  Zero empty-title articles remain in the candidates or the best set.
- QUBO: 902 variables, 172,063 redundancy couplings, 100 annealing reads.
- Best energy: −9.1684. Best set: 50 articles. Converged: 6/100 reads.
- Total run time: ~39.5 s.
- Reliability: 539 High / 313 Medium / 50 Low.
- Net-score distribution: mean 0.489, σ 0.188 (n=902); range −0.400 to 0.823.

### Top 10 by net score (all High, all real articles, ten distinct domains)

| Rank | Net | Rel. | Red. max | Red. avg | Meta+ | Wave+ | Rounds | Article | Selected |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.823 | 0.881 | 0.158 | 0.060 | 0.05 | 0.05 | 9 | AI Search Agents in 2026: The Future of Google Search \| Xenors — https://xenors.in/tech/ai-search-agents-future-of-search-2026 | No |
| 2 | 0.800 | 0.869 | 0.089 | 0.042 | 0.00 | 0.02 | 3 | AI Search Agents — AI Pulse — https://inblix.com/article/ai-search-agents-c30899 | Yes |
| 3 | 0.795 | 0.882 | 0.137 | 0.056 | 0.05 | 0.00 | 1 | Get Cited by AI in 60 Days. AI Search Trends 2026 for Teams - Cairrot — https://cairrot.com/blog/ai-search-trends | No |
| 4 | 0.784 | 0.893 | 0.109 | 0.048 | 0.00 | 0.00 | 1 | AI search and agents news, 22 October 2026 \| Aiso — https://www.getaiso.com/news/2026-10-22 | No |
| 5 | 0.776 | 0.812 | 0.096 | 0.048 | 0.05 | 0.01 | 2 | 2026 AI Agents Insight Report \| G2 Insights — https://sell.g2.com/g2-2026-ai-agents-insight-report | No |
| 6 | 0.769 | 0.872 | 0.103 | 0.046 | 0.00 | 0.00 | 1 | Conversational Search Agents Transform Google Search Box - AI CERTs News — https://www.aicerts.ai/news/conversational-search-agents-transform-google-search-box | Yes |
| 7 | 0.768 | 0.899 | 0.131 | 0.050 | 0.00 | 0.00 | 1 | AI News May 21 2026: Google IO Gemini 3.5 & AI Search Agents — https://mrreviewai.com/ai-news-digest-may-21-2026 | No |
| 8 | 0.766 | 0.837 | 0.131 | 0.065 | 0.05 | 0.01 | 2 | Best AI Agents in 2026: Tested, Compared, and Ranked — https://mastra.ai/articles/best-ai-agents | No |
| 9 | 0.760 | 0.892 | 0.132 | 0.054 | 0.00 | 0.00 | 1 | Top 5 AI search trends for 2026 - Blue Ocean Media — https://blueoceanmedia.co.uk/blog/top-5-ai-search-trends-for-2026 | No |
| 10 | 0.759 | 0.852 | 0.093 | 0.041 | 0.00 | 0.00 | 1 | BrightEdge Data: AI Search is Reaching a Tipping Point – by End of 2026 Most Online Customers will be AI Agents \| BrightEdge — https://www.brightedge.com/news/press-releases/brightedge-data-ai-search-reaching-tipping-point-ai-agents-2026 | No |

### Honest result: top-10 / best-set overlap improved from 0/10 to 2/10

Two of the top 10 are in the best set (ranks 2 and 6). The best-selected
article by net now ranks 2nd — up from 22nd. 4 selected articles are in
the top 25 by net (was 1), 5 in the top 50 (was 3), 8 in the top 100
(unchanged). The best set's mean net (0.561) is above the run mean (0.489).
The lists still diverge: charging the worst twin moved the ranking toward
the set, but net remains a per-article standalone number while the QUBO is
a joint optimization — it penalizes similarity to the *selected* set as it
forms, which no single-article score can reproduce. No further terms were
stacked on to force the overlap; this is the measured result of the one
formula change plus the empty-title filter. Log:
runs/run-1000-maxred-2026-11-14.json.

Dashboard render check: the actual dashboard JS was executed in node
against this run's log — the headline is exactly the 50 selected articles
in net-descending order, the separate section is exactly the log's top 10
by net, and no card falls back to a bare URL as its title.

1. Run the query in the dashboard (or via the API) and record: prompt,
   settings (depth, wave rounds, mantra/meta on/off), candidates retrieved,
   extracted, QUBO variables/couplings, best energy, convergence (x/100),
   best-set size, run time, reliability counts.
2. Record the top 10 by net score (by relevance for runs before 5c) with
   scores and selected/not.
3. Note anything the run proves (e.g. duplicates excluded, grounding
   behaviour) and any caveat.
4. Append as a new use-case section; do not rewrite earlier sections.
