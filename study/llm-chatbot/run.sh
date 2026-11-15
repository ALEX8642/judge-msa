#!/bin/sh
# Run rejudge.py with the few packages LLM-chatbot's grader imports (pymupdf pinned as in its lock).
# Usage: ./run.sh --llm-chatbot PATH --arm A --judge phi4:14b --out data/trials-A.jsonl
cd "$(dirname "$0")" && exec uv run -q --isolated --no-project --python 3.12 \
  --with requests --with "pymupdf==1.26.4" --with pillow --with rapidfuzz -- python rejudge.py "$@"
