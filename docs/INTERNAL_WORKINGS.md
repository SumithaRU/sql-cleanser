# Internal Workings

This document dives into the core implementation details of the `/compare` module.

## 1. Parsing & Loading

- **`load_rows_from_dir`**: Scans `.sql` and `.txt` files in a directory and applies `parse_sql_file` to extract row dicts `{table, columns, values, source_file, lineno}`.

## 2. Primary Key Inference & Sorting

- **`infer_primary_keys`** (in `ollama_utils.py`): Invokes Ollama LLaMA 3 8B via LangChain or subprocess to identify likely PK columns based on sample rows.
- **Sorting**: Rows for each table are sorted by the inferred PK tuple to guarantee deterministic ordering before comparison.

## 3. Diff Computation

- **Key Mapping**: For each table, rows are mapped by their PK tuples into two dicts (`b_map`, `o_map`).
- **Missing / Extra**: Keys present in one map and not the other are categorized as **missing** (in Oracle) or **extra** (in Oracle).
- **Mismatches**: For common PK keys, a value-level comparison flags any divergent rows.
- **Summary + Per-Table**: Results are aggregated into both a global `summary` and per-`tables` section in `diff.json`.

## 4. LLM Migration Plan

- **Prompt Template**: A single combined prompt delivers both the full JSON diff and instructions to generate:
  1. A detailed Markdown migration guide (datatype mapping, sequences, SQL rewrite tips).<br/>
  2. A structured JSON plan with `steps[]`, `risk_level`, `estimated_effort`, and `warnings[]`.
- **Retries & Timeout**: The `call_llm_with_retry` function spawns `ollama run llama3:8b` up to **3×**, each with a **120s** timeout; failures bubble up as HTTP 500.

## 5. Packaging & Delivery

- **Artifacts**: `diff.json`, `diff_report.md`, `migration_plan.md`, `migration_plan.json`.
- **ZIP Creation**: All artifacts are zipped into `compare_<timestamp>.zip` and streamed back in the `/compare` response via `StreamingResponse`.
