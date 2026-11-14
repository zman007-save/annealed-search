#!/bin/bash
# annealed-search — one-command start
# Requires: .env with TELEM_API_KEY and TAVILY_API_KEY (see README)
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q -r requirements.txt
fi
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
