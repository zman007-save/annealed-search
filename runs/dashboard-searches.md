# Dashboard searches — living log

Every search run from the dashboard is recorded here automatically: the prompt, the settings, the scores individually (per article) and together (the annealed best set), with a hyperlink on every article title. The full JSON for each run is in runs/run-<YYYY-MM-DD-HHMMSS>.json.

## 2026-11-14 14:08:57 PT — "AI search agents 2026"

Settings: advanced depth, 2 wave rounds, max_results 10, mantra on, meta-search off. Time range: any. Country: none. Include domains: none. Exclude domains: none.

Telem: 50 results (tavily, exa, seltz). Candidates: 41 (38 extracted). Filtered out: 0 listing pages, 9 duplicate URLs, 0 duplicate titles, 20 empty titles. Meta cross-validated: 0. In 2+ wave rounds: 5.

QUBO: 41 variables, 524 couplings, 100 reads, best energy -1.9336, 40/100 converged, 10 in the best set, 7.4s.

### Scores — individually (41 articles, by net score)

| # | Article | Source | Tavily | Mantra | Relevance | Red. max | Meta+ | Wave+ | Net | Selected? |
|---|---------|--------|--------|--------|-----------|----------|-------|-------|-----|-----------|
| 1 | [AI Search Agents in 2026: The Future of Google Search \| Xenors](<https://xenors.in/tech/ai-search-agents-future-of-search-2026>) | tavily | 0.819 | 1.000 | 0.892 | 0.140 | 0.00 | 0.00 | 0.752 | Yes |
| 2 | [AI agent trends 2026 report](<https://cloud.google.com/resources/content/ai-agent-trends-2026>) | tavily | 0.665 | 1.000 | 0.799 | 0.091 | 0.00 | 0.01 | 0.718 | Yes |
| 3 | [7 Best AI Search Engines for Developers & AI Agents (2026) \| TinyFish Blog](<https://www.tinyfish.ai/blog/best-ai-search-engine>) | tavily | 0.739 | 1.000 | 0.844 | 0.137 | 0.00 | 0.01 | 0.717 | No |
| 4 | [Web Search for Agents in 2026](<https://michaellivs.com/blog/web-search-for-agents-2026>) | tavily | 0.765 | 1.000 | 0.859 | 0.164 | 0.00 | 0.00 | 0.695 | No |
| 5 | [Best AI Search APIs for Agents 2026 \| Context Studios](<https://www.contextstudios.ai/guides/best-ai-search-apis-agents-2026>) | tavily | 0.768 | 1.000 | 0.861 | 0.174 | 0.00 | 0.00 | 0.687 | Yes |
| 6 | [Best AI Search Engines for Agents and Workflows in 2026](<https://www.firecrawl.dev/blog/best-ai-search-engines-agents>) | tavily | 0.780 | 1.000 | 0.868 | 0.197 | 0.00 | 0.01 | 0.681 | No |
| 7 | [Best Web Search APIs & MCPs for AI Agents 2026](<https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents>) | tavily | 0.762 | 1.000 | 0.857 | 0.197 | 0.00 | 0.01 | 0.670 | No |
| 8 | [Best web search APIs and MCPs for AI agents in 2026 - Articles - Braintrust](<https://www.braintrust.dev/articles/best-web-search-apis-mcps-ai-agents-2026>) | tavily | 0.740 | 1.000 | 0.844 | 0.174 | 0.00 | 0.00 | 0.670 | No |
| 9 | [Best AI Search APIs for Agents and LLM Apps in 2026](<https://sfailabs.com/guides/best-ai-search-apis-for-agents-2026>) | tavily | 0.598 | 1.000 | 0.759 | 0.093 | 0.00 | 0.00 | 0.666 | Yes |
| 10 | [AI Updates: Latest Developments, Breakthroughs & Trends in 2026](<https://thebizaihub.com/ai-updates>) | tavily | 0.603 | 1.000 | 0.762 | 0.122 | 0.00 | 0.00 | 0.640 | No |
| 11 | [A Survey of Large Language Model-Based Search Agents - ACL Anthology](<https://aclanthology.org/2026.acl-long.374>) | telem | — | 1.000 | 0.700 | 0.063 | 0.00 | 0.00 | 0.637 | Yes |
| 12 | [Evaluating AI Research Agents: SwarmEvolve vs. Scientist World – Forkast](<https://forkast.news/evaluating-ai-research-agents-swarmevolve-vs-scientist-world>) | telem | — | 1.000 | 0.700 | 0.070 | 0.00 | 0.00 | 0.630 | Yes |
| 13 | [A new era for AI Search](<https://blog.google/products-and-platforms/products/search/search-io-2026>) | telem | — | 1.000 | 0.700 | 0.097 | 0.00 | 0.01 | 0.613 | No |
| 14 | [Marketers deploying AI agents faster than they can measure them](<https://martech.org/marketers-deploying-ai-agents-faster-than-they-can-measure-them>) | telem | — | 1.000 | 0.700 | 0.092 | 0.00 | 0.00 | 0.608 | No |
| 15 | [Diffbot Search Agent: A new SOTA for web question answering \| Diffbot](<https://www.diffbot.com/blog/introducing-diffbot-search-agent>) | telem | — | 1.000 | 0.700 | 0.097 | 0.00 | 0.00 | 0.603 | No |
| 16 | [10 trends and predictions for retail in 2026](<https://nrf.com/blog/10-trends-and-predictions-for-retail-in-2026>) | telem | — | 1.000 | 0.700 | 0.098 | 0.00 | 0.00 | 0.602 | Yes |
| 17 | [Web search for agents is here: Why ranking still decides the answer - The New Stack](<https://thenewstack.io/ai-agent-search-ranking>) | telem | — | 1.000 | 0.700 | 0.098 | 0.00 | 0.00 | 0.602 | No |
| 18 | [5 Key Enterprise SEO And AI Trends For 2026](<https://www.searchenginejournal.com/key-enterprise-seo-and-ai-trends/532337>) | telem | — | 1.000 | 0.700 | 0.100 | 0.00 | 0.00 | 0.600 | No |
| 19 | [United Airlines AI Agents Ban: What Still Works in 2026 - Memeburn](<https://memeburn.com/united-airlines-ai-agents>) | telem | — | 1.000 | 0.700 | 0.104 | 0.00 | 0.00 | 0.596 | No |
| 20 | [United Requires Permission For AI Agents, Keeps Search Indexing Open](<https://www.searchenginejournal.com/united-ai-agents-permission-search-indexing/597418>) | telem | — | 1.000 | 0.700 | 0.104 | 0.00 | 0.00 | 0.596 | No |
| 21 | [State of AI Agents](<https://www.langchain.com/state-of-agent-engineering>) | tavily | 0.508 | 1.000 | 0.705 | 0.112 | 0.00 | 0.00 | 0.593 | No |
| 22 | [The 10 best AI agent tools for 2026 (and how tool calling works)](<https://exa.ai/blog/best-ai-agent-tools>) | telem | — | 1.000 | 0.700 | 0.119 | 0.00 | 0.00 | 0.581 | No |
| 23 | [Databricks Launches New Always-on Genie: Autonomous AI for Complex Enterprise Work - Databricks](<https://www.databricks.com/company/newsroom/press-releases/databricks-launches-new-always-genie-autonomous-ai-complex>) | telem | — | 1.000 | 0.700 | 0.119 | 0.00 | 0.00 | 0.581 | No |
| 24 | [Best AI agent for web search: 4 in 2026](<https://www.aiagentsinfo.com/best/ai-agents-for-web-search>) | telem | — | 1.000 | 0.700 | 0.124 | 0.00 | 0.00 | 0.576 | No |
| 25 | [AI Search: the search primitive for your agents \| Cloudflare Blog](<https://blog.cloudflare.com/ai-search-agent-primitive>) | tavily | 0.684 | 0.667 | 0.677 | 0.107 | 0.00 | 0.00 | 0.570 | Yes |
| 26 | [Why 2026 Is the Year Enterprise AI Agents Get Real \| Cirrius Solutions](<https://cirriussolutions.com/why-2026-is-the-year-enterprise-ai-agents-get-real>) | telem | — | 1.000 | 0.700 | 0.131 | 0.00 | 0.00 | 0.569 | No |
| 27 | [The trends that will shape AI and tech in 2026](<https://www.ibm.com/think/news/ai-tech-trends-predictions-2026>) | telem | — | 1.000 | 0.700 | 0.131 | 0.00 | 0.00 | 0.569 | No |
| 28 | [11 Best AI Browser Agents in 2026](<https://www.firecrawl.dev/blog/best-browser-agents>) | telem | — | 1.000 | 0.700 | 0.136 | 0.00 | 0.00 | 0.564 | No |
| 29 | [The 8 best web search tools for AI agents in 2026 \| Exa Blog](<https://exa.ai/blog/best-web-search-tools-for-ai-agents>) | telem | — | 1.000 | 0.700 | 0.165 | 0.00 | 0.00 | 0.535 | No |
| 30 | [The Best AI Search Engine Agents Review in 2026](<https://www.nstdata.io/blog/best-ai-search-engine-agents>) | telem | — | 1.000 | 0.700 | 0.173 | 0.00 | 0.00 | 0.527 | No |
| 31 | [10 AI Marketing Trends for 2026](<https://www.adweek.com/brand-marketing/10-ai-marketing-trends-for-2026-agentic-ai-and-search-shifts>) | telem | — | 0.667 | 0.567 | 0.068 | 0.00 | 0.00 | 0.499 | No |
| 32 | [The Landscape of LLM-based Search Agents: A Survey](<https://doi.org/10.20944/preprints202608.0572.v1>) | telem | — | 0.667 | 0.567 | 0.074 | 0.00 | 0.00 | 0.493 | No |
| 33 | [The 2026 AI Agent Transition \| Compoze Labs](<https://blog.compozelabs.com/the-2026-ai-agent-transition>) | tavily | 0.515 | 0.667 | 0.575 | 0.096 | 0.00 | 0.00 | 0.479 | Yes |
| 34 | [Stanford AI Experts Predict What Will Happen in 2026 \| Stanford HAI](<https://hai.stanford.edu/news/stanford-ai-experts-predict-what-will-happen-in-2026>) | telem | — | 0.667 | 0.567 | 0.090 | 0.00 | 0.00 | 0.477 | No |
| 35 | [The AI Agents Can't Find Anyone to Help Yet](<https://gizmodo.com/the-ai-agents-cant-find-anyone-to-help-yet-2000839258>) | telem | — | 0.667 | 0.567 | 0.097 | 0.00 | 0.00 | 0.470 | Yes |
| 36 | [Introducing the Web Search API on Amazon Bedrock AgentCore \| Artificial Intelligence](<https://aws.amazon.com/blogs/machine-learning/introducing-the-web-search-api-on-amazon-bedrock-agentcore>) | telem | — | 0.667 | 0.567 | 0.099 | 0.00 | 0.00 | 0.468 | No |
| 37 | [Top AI Statistics And Trends: Updated For 2026](<https://www.forbes.com/advisor/business/ai-statistics>) | telem | — | 0.667 | 0.567 | 0.101 | 0.00 | 0.00 | 0.466 | No |
| 38 | [McKinsey technology trends outlook 2026 \| McKinsey](<https://www.mckinsey.com/capabilities/tech-and-ai/our-insights/the-top-trends-in-tech>) | telem | — | 0.667 | 0.567 | 0.110 | 0.00 | 0.00 | 0.457 | No |
| 39 | [What’s next in AI: 7 trends to watch in 2026](<https://news.microsoft.com/source/features/ai/whats-next-in-ai-7-trends-to-watch-in-2026>) | telem | — | 0.667 | 0.567 | 0.124 | 0.00 | 0.00 | 0.443 | No |
| 40 | [How to dominate SEO & AI Search results in 2026 (Beginner Semrush Tutorial with AI Agent support)](<https://www.youtube.com/watch?v=lZ38LexlJTA>) | tavily | 0.489 | 0.667 | 0.560 | 0.122 | 0.00 | 0.00 | 0.438 | No |
| 41 | [What is a search agent? How they work and how to build one \| Exa Blog](<https://exa.ai/blog/what-is-a-search-agent>) | telem | — | 0.333 | 0.433 | 0.112 | 0.00 | 0.00 | 0.321 | No |

### Together — the annealed best set (10 articles)

Best energy -1.9336; 40/100 reads converged; 7.4s. Mean net of the set 0.621 vs run mean 0.577. Overlap with the top 10 by net: 4/10.

| # | Article | Net |
|---|---------|-----|
| 1 | [AI Search Agents in 2026: The Future of Google Search \| Xenors](<https://xenors.in/tech/ai-search-agents-future-of-search-2026>) | 0.752 |
| 2 | [AI agent trends 2026 report](<https://cloud.google.com/resources/content/ai-agent-trends-2026>) | 0.718 |
| 3 | [Best AI Search APIs for Agents 2026 \| Context Studios](<https://www.contextstudios.ai/guides/best-ai-search-apis-agents-2026>) | 0.687 |
| 4 | [Best AI Search APIs for Agents and LLM Apps in 2026](<https://sfailabs.com/guides/best-ai-search-apis-for-agents-2026>) | 0.666 |
| 5 | [A Survey of Large Language Model-Based Search Agents - ACL Anthology](<https://aclanthology.org/2026.acl-long.374>) | 0.637 |
| 6 | [Evaluating AI Research Agents: SwarmEvolve vs. Scientist World – Forkast](<https://forkast.news/evaluating-ai-research-agents-swarmevolve-vs-scientist-world>) | 0.630 |
| 7 | [10 trends and predictions for retail in 2026](<https://nrf.com/blog/10-trends-and-predictions-for-retail-in-2026>) | 0.602 |
| 8 | [AI Search: the search primitive for your agents \| Cloudflare Blog](<https://blog.cloudflare.com/ai-search-agent-primitive>) | 0.570 |
| 9 | [The 2026 AI Agent Transition \| Compoze Labs](<https://blog.compozelabs.com/the-2026-ai-agent-transition>) | 0.479 |
| 10 | [The AI Agents Can't Find Anyone to Help Yet](<https://gizmodo.com/the-ai-agents-cant-find-anyone-to-help-yet-2000839258>) | 0.470 |

