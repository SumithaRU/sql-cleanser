#!/usr/bin/env bash
# Demo script to ingest SQL files from sample-input-scripts and show progress using rich

set -e

# Ensure backend module can be imported
export PYTHONPATH=$(pwd)/src

INPUT_DIR="../sample-input-scripts/base"
OUTPUT_DIR="output_demo"
mkdir -p "$OUTPUT_DIR"

python3 - <<'PYCODE'
import os
from rich.progress import Progress
from backend.ingest import parse_sql_file

input_dir = os.environ.get('INPUT_DIR')
files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.sql', '.txt'))]
with Progress() as progress:
    task = progress.add_task('Processing SQL files...', total=len(files))
    for fname in files:
        parse_sql_file(os.path.join(input_dir, fname))
        progress.update(task, advance=1)
print(f"Demo complete. Parsed SQL files from {input_dir}")
PYCODE 