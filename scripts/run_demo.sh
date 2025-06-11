#!/usr/bin/env bash
# Demo script to ingest SQL files from input/ and show progress using rich

set -e
export $(grep -v '^#' .env.example | xargs)
INPUT_DIR='input'
OUTPUT_DIR='output_demo'
mkdir -p $OUTPUT_DIR

python3 - <<'PYCODE'
import os
from rich.progress import Progress
from backend.ingest import parse_sql_file

files = [f for f in os.listdir('input') if f.endswith('.sql')]
with Progress() as progress:
    task = progress.add_task('Processing SQL files...', total=len(files))
    for fname in files:
        parse_sql_file(os.path.join('input', fname))
        progress.update(task, advance=1)
print('Demo complete. Parsed SQL files.')
PYCODE 