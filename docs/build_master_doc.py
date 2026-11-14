#!/usr/bin/env python3
"""Fold new annealed-search run JSONs into the use-case master docx.

Appends a new Use Case section per run JSON in runs/ that has not been
folded yet, inserted above the "Template — add the next run here"
heading so the newest use case sits last in run order. Existing pages
are never rewritten or reformatted — only appended to.

State lives in docs/.master-doc-folded.json:
  {"folded": [<basenames already in the doc>],
   "skipped": {<basename>: <reason>},
   "next_use_case": <int>}

Usage:
  docs/build_master_doc.py [--run <basename.json> ...] [--dry-run]

With no --run, folds every unfolded run JSON in runs/ (oldest first).
After folding it regenerates the PDF with LibreOffice headless and
copies both the docx and the PDF into docs/ (the repo copies).
"""
import argparse
import json
import shutil
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

PROJECT = Path(__file__).resolve().parent.parent
RUNS_DIR = PROJECT / "runs"
MASTER_DIR = Path.home() / "workspace" / "your_files" / "annealed-search-use-cases-master"
DOCX = MASTER_DIR / "annealed-search-use-cases-master.docx"
PDF = MASTER_DIR / "annealed-search-use-cases-master.pdf"
STATE_FILE = PROJECT / "docs" / ".master-doc-folded.json"
PT = ZoneInfo("America/Los_Angeles")

# Runs already covered by a section in the master doc (Use Cases 1-5d).
# Runs 1-4 have no JSON logs (aggregates only); the 1,010-article family
# is covered by Use Cases 5 / 5b / 5c / 5d.
INITIAL_FOLDED = [
    "run-1000-2026-11-14.json",
    "run-1000-filtered-2026-11-14.json",
    "run-1000-combined-2026-11-14.json",
    "run-1000-maxred-2026-11-14.json",
]
# Intermediate iterations — covered by their final run's section.
INITIAL_SKIPPED = {
    "run-887-2026-11-14.json": "first 1,010 attempt; superseded by run-1000",
    "run-1000-filtered-v1-2026-11-14.json": "filter iteration; superseded by run-1000-filtered",
    "run-1000-filtered-v2-2026-11-14.json": "filter iteration; superseded by run-1000-filtered",
}

# Per-run notes: (section subtitle, why-this-run-matters paragraph).
# Runs without an entry get an auto-generated note from their settings.
NOTES = {
    "run-hack-endpoint-2026-11-14.json": (
        "dedicated-server verification (hack.telem.ai)",
        "This run proves the pipeline on the hackathon's dedicated server. "
        "The key issued on app.telem.ai returned 401 on hack.telem.ai/api, "
        "so a new key was issued on hack.telem.ai and the app was pointed "
        "at it (TELEM_BASE_URL). Telem returned 50 results through the "
        "dedicated endpoint, and 27 of the 40 candidates are Telem-sourced "
        "— Telem is genuinely in the pool, not just called.",
    ),
}


def fmt(x, nd=3):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:.{nd}f}"
    return str(x)


def pt_time(path: Path) -> str:
    dt = datetime.fromtimestamp(path.stat().st_mtime, PT)
    return dt.strftime("%B %-d, %Y, at about %-I:%M %p PT")


def add_hyperlink(paragraph, url, text):
    """Add a real clickable hyperlink run to a paragraph."""
    part = paragraph.part
    r_id = part.relate_to(url, RT.HYPERLINK, is_external=True)
    hyperlink = OxmlElement("w:hyperlink")
    hyperlink.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    rPr.append(color)
    u = OxmlElement("w:u")
    u.set(qn("w:val"), "single")
    rPr.append(u)
    run.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    run.append(t)
    hyperlink.append(run)
    paragraph._p.append(hyperlink)


def insert_before(doc, anchor, element):
    anchor._element.addprevious(element)


def add_para(doc, anchor, text, style="Normal"):
    p = doc.add_paragraph(style=style)
    p.add_run(text)
    insert_before(doc, anchor, p._element)
    return p


def build_section(doc, anchor, n, run_path, payload):
    """Append one Use Case section (paragraphs + top-10 table) before anchor."""
    query = payload.get("query", "")
    params = payload.get("params", {}) or {}
    stages = payload.get("stages", {}) or {}
    qubo = payload.get("qubo", {}) or {}
    articles = payload.get("articles", []) or []
    top10 = payload.get("top10", []) or []
    filt = stages.get("filtered", {}) or {}
    selected = [a for a in articles if a.get("selected")]
    by_net = sorted(articles, key=lambda a: -(a.get("net_score") or 0))

    subtitle, why = NOTES.get(
        run_path.name,
        (
            f"small live run ({payload.get('frequency_rounds')} wave rounds, "
            f"meta-search {'on' if payload.get('meta_search') else 'off'}, "
            "recorded automatically from the dashboard)",
            "A dashboard run recorded automatically: every search on the "
            "dashboard now lands in this document with the prompt, the "
            "scores individually and together, and a hyperlink on every "
            "article title.",
        ),
    )
    add_para(doc, anchor,
             f"Use Case {n} — “{query}”, {subtitle}", style="Heading 1")
    add_para(doc, anchor, f"Prompt: “{query}”")
    add_para(doc, anchor,
             f"{params.get('search_depth', 'advanced').capitalize()} search "
             f"depth, {payload.get('frequency_rounds')} wave rounds, "
             f"max_results {params.get('max_results')}, mantra grounding "
             f"{'on' if payload.get('mantra') else 'off'}, meta-search "
             f"{'on' if payload.get('meta_search') else 'off'}. "
             f"{pt_time(run_path)}. "
             f"{stages.get('candidates')} candidates "
             f"({stages.get('extracted')} extracted); Telem returned "
             f"{stages.get('telem_results')} results "
             f"({', '.join(stages.get('telem_providers') or [])}); "
             f"filtered out {filt.get('listing', 0)} listing pages, "
             f"{filt.get('dup_url', 0)} duplicate URLs, "
             f"{filt.get('dup_title', 0)} duplicate titles, "
             f"{filt.get('empty_title', 0)} empty titles.")
    note = payload.get("net_score_note") or ""
    if note:
        add_para(doc, anchor, "The net score. " + note)
    mantra_full = sum(1 for a in top10 if a.get("mantra_grounding") == 1.0)
    add_para(doc, anchor,
             f"The top 10 is ranked by net score, not relevance — and the "
             f"Selected column is still the point of the demo. {mantra_full} "
             f"of the ten scored mantra grounding 1.0.")
    # Top-10 table (same 9 columns as Use Case 5d).
    table = doc.add_table(rows=1, cols=9)
    table.style = "Table Grid"
    hdr = ["#", "Net", "Rel.", "Red. max", "Red. avg", "Meta+", "Wave+",
           "Article", "Selected?"]
    for cell, h in zip(table.rows[0].cells, hdr):
        cell.text = h
    for i, a in enumerate(top10, 1):
        row = table.add_row().cells
        vals = [str(i), fmt(a.get("net_score")), fmt(a.get("relevance")),
                fmt(a.get("redundancy_max")), fmt(a.get("redundancy_avg")),
                fmt(a.get("meta_bonus"), 2), fmt(a.get("wave_bonus"), 2)]
        for cell, v in zip(row[:7], vals):
            cell.text = v
        title = (a.get("title") or a.get("url") or "—").strip()
        url = (a.get("url") or "").strip()
        p = row[7].paragraphs[0]
        if url:
            add_hyperlink(p, url, title)
        else:
            p.text = title
        row[8].text = "Yes" if a.get("selected") else "No"
    insert_before(doc, anchor, table._tbl)

    add_para(doc, anchor, "Why this run matters. " + why)
    overlap = sum(1 for a in top10 if a.get("selected"))
    best_rank = None
    for i, a in enumerate(by_net, 1):
        if a.get("selected"):
            best_rank = i
            break
    sel_nets = [a["net_score"] for a in selected
                if a.get("net_score") is not None]
    all_nets = [a["net_score"] for a in articles
                if a.get("net_score") is not None]
    set_mean = round(statistics.fmean(sel_nets), 3) if sel_nets else None
    run_mean = round(statistics.fmean(all_nets), 3) if all_nets else None
    add_para(doc, anchor,
             f"Honest result. The top-10 / best-set overlap is "
             f"{overlap} / 10. The best-selected article by net ranks "
             f"{best_rank if best_rank is not None else '—'} of "
             f"{len(articles)}. The best set's mean net ({fmt(set_mean)}) "
             f"is {'above' if set_mean is not None and run_mean is not None and set_mean >= run_mean else 'below'} "
             f"the run mean ({fmt(run_mean)}). Best energy "
             f"{qubo.get('best_energy')} with {qubo.get('converged')} / "
             f"{qubo.get('reads')} reads converged and "
             f"{len(selected)} articles in the best set.")
    caveats = []
    conv = qubo.get("converged")
    reads = qubo.get("reads")
    if conv is not None and reads:
        caveats.append(
            f"Convergence was {conv} / {reads} — the best set is still the "
            "best found, with most reads landing on worse optima.")
    if mantra_full == len(top10) and top10:
        caveats.append(
            "Mantra grounding is 1.0 across the whole top 10, so it does "
            "not discriminate among the best articles on this broad query.")
    if len(articles) < 100:
        caveats.append(
            f"This is a small verification run ({len(articles)} candidates), "
            "not a scale run — the numbers prove the pipeline end to end, "
            "not the 1,000-article behaviour.")
    if qubo.get("fallback"):
        caveats.append(
            "The annealer picked no articles, so the run fell back to the "
            "top 3 by relevance as the best set.")
    add_para(doc, anchor,
             "Caveats. " + (" ".join(caveats) if caveats
                             else "Nothing surprising recorded."))
    return f"Use Case {n}"


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"folded": list(INITIAL_FOLDED),
            "skipped": dict(INITIAL_SKIPPED),
            "next_use_case": 6}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", default=[],
                    help="specific run JSON basename(s) to fold")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    state = load_state()
    folded = set(state["folded"])
    skipped = state["skipped"]

    if args.run:
        targets = [RUNS_DIR / b for b in args.run]
        missing = [str(p) for p in targets if not p.exists()]
        if missing:
            print("missing run JSON(s):", ", ".join(missing))
            return 1
    else:
        targets = sorted(
            (p for p in RUNS_DIR.glob("run-*.json")
             if p.name not in folded and p.name not in skipped),
            key=lambda p: p.stat().st_mtime)
    if not targets:
        print("Nothing new to fold.")
        return 0

    if args.dry_run:
        print("DRY RUN — would fold:")
        for path in targets:
            print(f"  {path.name} -> Use Case {state['next_use_case']}")
        return 0

    doc = docx.Document(str(DOCX))
    anchor = None
    for p in doc.paragraphs:
        if p.style.name == "Heading 1" and p.text.startswith("Template —"):
            anchor = p
            break
    if anchor is None:
        print("ERROR: template heading not found in master docx.")
        return 1

    added = []
    n = state["next_use_case"]
    for path in targets:
        payload = json.loads(path.read_text())
        label = build_section(doc, anchor, n, path, payload)
        added.append((path.name, label))
        folded.add(path.name)
        n += 1
    state["next_use_case"] = n

    doc.save(str(DOCX))
    # Regenerate the PDF with LibreOffice headless.
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["soffice", "--headless",
             "-env:UserInstallation=file:///tmp/soffice-masterdoc",
             "--convert-to", "pdf", "--outdir", tmp, str(DOCX)],
            check=True, capture_output=True, text=True, timeout=300)
        pdf_tmp = Path(tmp) / (DOCX.stem + ".pdf")
        shutil.copyfile(pdf_tmp, PDF)
    # Repo copies.
    (PROJECT / "docs" / DOCX.name).write_bytes(DOCX.read_bytes())
    (PROJECT / "docs" / PDF.name).write_bytes(PDF.read_bytes())
    STATE_FILE.parent.mkdir(exist_ok=True)
    state["folded"] = sorted(folded)
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")
    print(f"Folded {len(added)} run(s) into {DOCX.name}:")
    for name, label in added:
        print(f"  {name} -> {label}")
    print(f"PDF regenerated: {PDF.name}")
    print("Repo copies updated in docs/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
