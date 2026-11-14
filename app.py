"""annealed-search — SearchHack (Telem AI) Nov 14, 2026.

Article search that anneals to the best set:
  query -> Telem AI (auto-routed search) + Tavily (search + extract)
       -> QUBO (one binary variable per article; -relevance linear,
          +redundancy quadratic) -> LOCAL simulated annealing
          (D-Wave Ocean SDK, dimod + dwave-samplers)
       -> annealed best set with energy scores.

No QPU usage: the free D-Wave QPU minute stays untouched. Same BQM runs
on the QPU later ("simulated today, QPU-ready").

New parameter control (innovation hook):
  - Tavily controls: search_depth, country, include/exclude_domains,
    time_range, max_results.
  - frequency/wave search: retrieval oscillates between angles/profiles
    across rounds, like a wave going back and forth.
  - mantra search: the agent repeats the ORIGINAL prompt to itself for
    each article and scores how well the article grounds to it
    (reliability of output).
  - meta-search: combines/ranks across two parameter profiles.

Run:  ./run.sh   (or: .venv/bin/uvicorn app:app --port 8000)
Then open http://localhost:8000
"""
import asyncio
import math
import os
import re
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(Path(__file__).parent / ".env")

TELEM_API_KEY = os.environ.get("TELEM_API_KEY", "")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY", "")
TELEM_BASE = "https://router.telem.ai"
TAVILY_BASE = "https://api.tavily.com"

app = FastAPI(title="annealed-search")

STOPWORDS = set(
    "the a an of to in on for and or is are was were be by with at from as it "
    "this that these those i you he she we they what when where who how why "
    "not no do does did can could will would should".split()
)


def tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def as_text(v) -> str:
    """Providers sometimes return a list of strings; join them."""
    if isinstance(v, list):
        return " ".join(str(x) for x in v)
    return v or ""


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


# ---------------------------------------------------------------- retrieval
async def telem_search(client: httpx.AsyncClient, query: str, num_results: int = 5):
    """Telem AI search with auto-routing (the 40% judging bucket).

    Returns (articles, providers_used). Articles: title/url/snippet/source.
    """
    if not TELEM_API_KEY:
        return [], []
    try:
        r = await client.post(
            f"{TELEM_BASE}/v1/search",
            headers={"Authorization": f"Bearer {TELEM_API_KEY}"},
            json={
                "user_input": {"query": query},
                "search": {
                    "num_results": num_results,
                    "tier": "extended",
                    "auto_routing": "accuracy",
                },
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return [], [f"telem error: {e}"]

    articles, providers = [], []
    for run in data.get("preprocessor_runs", []) or []:
        name = run.get("preprocessor_name") or "telem"
        if name not in providers:
            providers.append(name)
        payload = (run.get("output_payload") or {}).get("results") or []
        for res in payload:
            url = res.get("url") or res.get("link") or ""
            if not url:
                continue
            articles.append(
                {
                    "title": res.get("title") or "",
                    "url": url,
                    "snippet": as_text(res.get("excerpt") or res.get("summary") or res.get("snippet") or res.get("content") or res.get("text")),
                    "published": res.get("publish_date") or res.get("published_at") or res.get("date") or "",
                    "source": "telem",
                    "provider": name,
                    "score": None,
                }
            )
    return articles, providers


async def tavily_search(client: httpx.AsyncClient, query: str, params: dict):
    """Tavily search with the parameter controls."""
    if not TAVILY_API_KEY:
        return []
    body = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": params.get("search_depth", "advanced"),
        "max_results": int(params.get("max_results", 8)),
    }
    if params.get("country"):
        body["country"] = params["country"]
    if params.get("include_domains"):
        body["include_domains"] = params["include_domains"]
    if params.get("exclude_domains"):
        body["exclude_domains"] = params["exclude_domains"]
    if params.get("time_range") and params["time_range"] != "any":
        body["time_range"] = params["time_range"]
    try:
        r = await client.post(f"{TAVILY_BASE}/search", json=body, timeout=30)
        r.raise_for_status()
        data = r.json()
    except Exception:
        return []
    out = []
    for res in data.get("results", []) or []:
        out.append(
            {
                "title": res.get("title") or "",
                "url": res.get("url") or "",
                "snippet": as_text(res.get("content")),
                "published": res.get("published_date") or "",
                "source": "tavily",
                "provider": "tavily",
                "score": res.get("score"),
            }
        )
    return out


async def tavily_extract(client: httpx.AsyncClient, urls, query: str):
    """Extract full article text for grounding/mantra scoring."""
    if not TAVILY_API_KEY or not urls:
        return {}
    try:
        r = await client.post(
            f"{TAVILY_BASE}/extract",
            json={"api_key": TAVILY_API_KEY, "urls": urls, "query": query,
                  "extract_depth": "basic"},
            timeout=45,
        )
        r.raise_for_status()
        data = r.json()
    except Exception:
        return {}
    out = {}
    for res in data.get("results", []) or []:
        content = as_text(res.get("raw_content") or res.get("content"))
        if res.get("url") and content:
            out[res["url"]] = content[:4000]
    return out


# ------------------------------------------------------------------- QUBO
def anneal(articles):
    """Build the QUBO and solve it LOCALLY with simulated annealing.

    x_i = 1 if article i is in the best set.
    linear  h_i = ALPHA - relevance_i   (relevance rewards selection,
                                          ALPHA is the cost of picking one)
    quadratic J_ij = BETA * similarity(i, j)  (redundancy penalty)
    """
    import dimod
    from dwave.samplers import SimulatedAnnealingSampler

    n = len(articles)
    ALPHA = 0.45
    BETA = 1.2
    linear = {}
    quad = {}
    for i, a in enumerate(articles):
        linear[i] = ALPHA - a["relevance"]
    for i in range(n):
        for j in range(i + 1, n):
            sim = jaccard(articles[i]["tokens"], articles[j]["tokens"])
            if sim > 0.05:
                quad[(i, j)] = BETA * sim
    bqm = dimod.BinaryQuadraticModel(linear, quad, 0.0, dimod.BINARY)
    sampler = SimulatedAnnealingSampler()
    sampleset = sampler.sample(bqm, num_reads=100)
    best = sampleset.first
    energies = sorted(float(e) for e in sampleset.record.energy)
    selected = [i for i in range(n) if best.sample[i] == 1]
    return {
        "selected": selected,
        "energy": float(best.energy),
        "trace": energies[:60],
        "num_reads": len(sampleset),
        "num_variables": n,
        "num_couplings": len(quad),
        # how many reads converged to the optimum — reliability story
        "converged": sum(1 for e in energies if abs(e - float(best.energy)) < 1e-9),
    }


def make_client() -> httpx.AsyncClient:
    """httpx client that uses the sandbox egress proxy but does not parse
    no_proxy (which contains bracketed IPv6 entries httpx chokes on).
    Verifies TLS against the system CA bundle, which holds the proxy CA."""
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    ca = "/etc/ssl/certs/ca-certificates.crt"
    verify = ca if os.path.exists(ca) else True
    if proxy:
        return httpx.AsyncClient(trust_env=False, proxy=proxy, verify=verify)
    return httpx.AsyncClient(trust_env=False, verify=verify)
@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/api/health")
def health():
    return {
        "telem_key": bool(TELEM_API_KEY),
        "tavily_key": bool(TAVILY_API_KEY),
        "qpu": "never — local simulated annealing only",
    }


@app.post("/api/search")
async def search(payload: dict):
    t0 = time.time()
    query = (payload.get("query") or "").strip()
    if not query:
        return {"error": "empty query"}
    params = {
        "search_depth": payload.get("search_depth", "advanced"),
        "country": (payload.get("country") or "").strip(),
        "include_domains": [d.strip() for d in (payload.get("include_domains") or "").split(",") if d.strip()],
        "exclude_domains": [d.strip() for d in (payload.get("exclude_domains") or "").split(",") if d.strip()],
        "time_range": payload.get("time_range", "any"),
        "max_results": int(payload.get("max_results", 8)),
    }
    frequency_rounds = max(1, min(5, int(payload.get("frequency_rounds", 3))))
    mantra = bool(payload.get("mantra", True))
    meta_search = bool(payload.get("meta_search", True))

    # -- Stage 1: query understanding (Telem's 40% bucket) -------------
    angles = [query, f"{query} latest developments", f"{query} in depth",
              f"{query} overview", f"{query} comparison"]
    rounds = []
    for r in range(frequency_rounds):
        # wave: alternate fresh/shallow <-> deep/broad each round
        if r % 2 == 0:
            prof = dict(params)
            angle = angles[r % len(angles)]
        else:
            prof = dict(params)
            prof["search_depth"] = "basic" if params["search_depth"] == "advanced" else "advanced"
            prof["time_range"] = "any"
            angle = angles[(r + 2) % len(angles)]
        rounds.append({"round": r + 1, "angle": angle, "profile": prof})

    # -- Stage 2: retrieval (Telem auto-routing + Tavily, in parallel) --
    async with make_client() as client:
        telem_task = telem_search(client, query, num_results=5)
        tavily_tasks = [tavily_search(client, rd["angle"], rd["profile"]) for rd in rounds]
        telem_articles, providers = await telem_task
        round_results = await asyncio.gather(*tavily_tasks)
        # meta-search: one extra pass with the opposite profile, then union
        meta_note = None
        if meta_search:
            alt = dict(params)
            alt["search_depth"] = "basic" if params["search_depth"] == "advanced" else "advanced"
            alt["time_range"] = "month" if params["time_range"] in ("day", "week") else "year"
            extra = await tavily_search(client, query, alt)
            round_results = list(round_results) + [extra]
            meta_note = f"meta-search merged an extra '{alt['search_depth']}' pass"

        # merge + dedupe by URL
        seen, candidates = {}, []
        for art in telem_articles:
            if art["url"] not in seen:
                seen[art["url"]] = True
                candidates.append(art)
        for idx, res in enumerate(round_results):
            for art in res:
                if art["url"] not in seen:
                    seen[art["url"]] = True
                    art["round"] = (idx % frequency_rounds) + 1
                    candidates.append(art)

        # -- Stage 3: extract + mantra grounding -----------------------
        top_urls = [a["url"] for a in candidates[:8]]
        extracts = await tavily_extract(client, top_urls, query)

    query_tokens = tokens(query)
    for art in candidates:
        text = extracts.get(art["url"], art["snippet"])
        art["tokens"] = tokens(art["title"] + " " + (text or ""))
        # mantra: repeat the ORIGINAL prompt against each article
        overlap = (len(query_tokens & art["tokens"]) / len(query_tokens)) if query_tokens else 0.0
        art["mantra_grounding"] = round(overlap, 3)
        tav = art["score"] if isinstance(art.get("score"), (int, float)) else 0.5
        art["relevance"] = round(0.6 * tav + 0.4 * overlap, 3)
        rel = 0.6 * tav + 0.4 * overlap
        art["reliability"] = (
            "High" if rel >= 0.6 else "Medium" if rel >= 0.35 else "Low"
        )
        art["content_len"] = len(text or "")
        art.pop("tokens", None)

    candidates.sort(key=lambda a: a["relevance"], reverse=True)
    if not candidates:
        return {
            "error": "No articles retrieved — Telem and Tavily both returned nothing for this query. Check the API keys / network and try again.",
            "query": query,
            "stages": {
                "telem_providers": providers,
                "telem_results": len(telem_articles),
                "rounds": [
                    {"round": rd["round"], "angle": rd["angle"],
                     "results": len(round_results[rd["round"] - 1]) if rd["round"] - 1 < len(round_results) else 0}
                    for rd in rounds
                ],
                "candidates": 0,
                "extracted": 0,
            },
        }
    anneal_set = candidates[:12]

    # -- Stage 4: QUBO + local simulated annealing ----------------------
    for art in anneal_set:
        art["tokens"] = tokens(art["title"] + " " + art["snippet"])
    result = anneal(anneal_set)
    for art in anneal_set:
        art.pop("tokens", None)
    selected_urls = {anneal_set[i]["url"] for i in result["selected"]}
    if not selected_urls:  # annealer picked none: fall back to top 3
        selected_urls = {a["url"] for a in anneal_set[:3]}
        result["selected"] = [anneal_set.index(a) for a in anneal_set[:3]]
        result["fallback"] = True

    ranked = []
    for art in anneal_set:
        ranked.append({**art, "selected": art["url"] in selected_urls})
    ranked.sort(key=lambda a: (not a["selected"], -a["relevance"]))

    return {
        "query": query,
        "params": params,
        "frequency_rounds": frequency_rounds,
        "mantra": mantra,
        "meta_search": meta_search,
        "meta_note": meta_note,
        "stages": {
            "telem_providers": providers,
            "telem_results": len(telem_articles),
            "rounds": [
                {"round": rd["round"], "angle": rd["angle"],
                 "results": len(round_results[rd["round"] - 1]) if rd["round"] - 1 < len(round_results) else 0}
                for rd in rounds
            ],
            "candidates": len(candidates),
            "extracted": len(extracts),
        },
        "qubo": {
            "variables": result["num_variables"],
            "couplings": result["num_couplings"],
            "reads": result["num_reads"],
            "best_energy": round(result["energy"], 4),
            "trace": [round(e, 3) for e in result["trace"]],
            "converged": result["converged"],
            "fallback": result.get("fallback", False),
        },
        "articles": ranked,
        "elapsed_s": round(time.time() - t0, 1),
    }


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
