#!/usr/bin/env python3
"""Ham batch: run many dashboard searches, stopping at ~75% Tavily plan usage.

- Loads the Tavily key from .env (never printed, never in this file).
- After each run, checks Tavily plan usage and stops at TARGET (750/1000).
- The app auto-logs every run (runs/*.json + runs/dashboard-searches.md).
- Safety rails: MAX_RUNS, MAX_MIN.
"""
import json, os, sys, time, urllib.request

BASE = "http://localhost:8000"
HERE = os.path.dirname(os.path.abspath(__file__))

for line in open(os.path.join(HERE, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

TAVILY_KEY = os.environ["TAVILY_API_KEY"]

BIG = [
    # NOTE: "quantum error correction 2026" and
    # "protein folding AI drug discovery 2026" already ran (runs 1-2) before
    # the driver was restarted with estimated-spend tracking.
    "fusion energy startups 2026",
    "CRISPR gene therapy clinical trials 2026",
    "solid-state batteries electric vehicles 2026",
    "AI agents enterprise adoption 2026",
    "carbon removal climate tech 2026",
    "reusable rockets space launch 2026",
]
MED = [
    "semiconductor chiplet design 2026",
    "longevity aging research 2026",
    "autonomous vehicles robotaxi 2026",
    "quantum computing startups funding 2026",
]
EXTRA = [
    "AI chip startups 2026", "robotics humanoid 2026", "synthetic biology 2026",
    "quantum sensors 2026", "EV charging infrastructure 2026", "AI music generation 2026",
    "brain computer interfaces 2026", "vertical farming 2026", "hydrogen energy 2026",
    "AI drug discovery clinical trials 2026", "edge AI devices 2026", "space debris removal 2026",
    "lab grown meat 2026", "AI cybersecurity 2026", "ocean carbon capture 2026",
    "fusion plasma confinement 2026", "neuromorphic computing 2026", "digital twins manufacturing 2026",
]

TARGET = 750        # 75% of the 1000-credit Researcher plan
# The Tavily /usage counter is STALE (stuck at 268 through 2 big runs), so
# the driver tracks spend by estimate instead. Per-run estimate, derived
# from today's totals (206 search credits over ~206 search calls, 62 extract
# credits over ~265 extracted URLs): 1 credit per Tavily search call +
# 0.25 per extracted URL.
EST_START = 372     # 268 measured + ~104 estimated for the 2 completed runs
EST_STOP = 740      # stop a little under 750; estimates are rough
MAX_RUNS = 20
MAX_MIN = 30


def tavily_usage():
    req = urllib.request.Request(
        "https://api.tavily.com/usage",
        headers={"Authorization": f"Bearer {TAVILY_KEY}"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.load(r)["account"]["plan_usage"]


def search(query, rounds, max_results):
    body = json.dumps({
        "query": query, "search_depth": "advanced",
        "frequency_rounds": rounds, "max_results": max_results,
        "mantra": True, "meta_search": True}).encode()
    req = urllib.request.Request(
        BASE + "/api/search", data=body,
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r), time.time() - t0


def main():
    log = open(os.path.join(HERE, "runs", "batch-ham-2026-11-14.log"), "a")

    def note(s):
        print(s, flush=True)
        log.write(s + "\n")
        log.flush()

    t_start = time.time()
    plan = ([(q, 40, 50) for q in BIG] + [(q, 15, 30) for q in MED]
            + [(q, 40, 50) for q in EXTRA])
    runs = 0
    est_spent = 0.0
    try:
        usage = tavily_usage()
    except Exception as e:
        note(f"usage check failed at start: {e}; proceeding on estimates")
        usage = None
    note(f"START usage={usage} est_start={EST_START} est_stop={EST_STOP} "
         f"max_runs={MAX_RUNS}")
    for query, rounds, mx in plan:
        if runs >= MAX_RUNS:
            note("STOP max runs")
            break
        if (time.time() - t_start) / 60 >= MAX_MIN:
            note("STOP time")
            break
        if usage is not None and usage >= TARGET:
            note(f"STOP live counter reached target usage={usage}")
            break
        if EST_START + est_spent >= EST_STOP:
            note(f"STOP estimated spend reached "
                 f"projected={EST_START + est_spent:.0f}")
            break
        try:
            d, dt = search(query, rounds, mx)
        except Exception as e:
            note(f"RUN FAIL {query!r}: {e}")
            continue
        runs += 1
        try:
            usage = tavily_usage()
        except Exception as e:
            note(f"usage check failed after run {runs}: {e}")
        q = d.get("qubo", {})
        calls = rounds + 4  # wave rounds + 4 meta passes (meta always on here)
        extracted = d.get("stages", {}).get("extracted", 0) or 0
        est = calls * 1.0 + extracted * 0.25
        est_spent += est
        note(f"RUN {runs} {query!r} rounds={rounds} "
             f"cands={len(d.get('articles', []))} energy={q.get('best_energy')} "
             f"conv={q.get('converged')}/{q.get('reads')} "
             f"selected={sum(1 for a in d.get('articles', []) if a.get('selected'))} "
             f"took={dt:.1f}s usage={usage} est_run={est:.0f} "
             f"projected={EST_START + est_spent:.0f}")
    note(f"DONE runs={runs} usage={usage} projected={EST_START + est_spent:.0f} "
         f"elapsed={(time.time() - t_start) / 60:.1f}min")


main()
