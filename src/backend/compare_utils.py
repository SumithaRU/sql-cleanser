import os
import json
import uuid
import zipfile
import datetime
import subprocess
import re
from typing import List, Dict, Any, Tuple

from ingest import parse_sql_file
from ollama_utils import infer_primary_keys, extract_json_from_response
from config_loader import config

# Configuration from YAML
OLLAMA_HOST = config.get('ollama.host', 'http://localhost:11434')
OLLAMA_MODEL = config.get('ollama.model', 'llama3:8b')
LLM_CALL_TIMEOUT = config.get('ollama.timeout_seconds', 600)
OLLAMA_MAX_TOKENS = config.get('ollama.max_tokens', 16384)
OLLAMA_RETRIES = config.get('ollama.retry_attempts', 3)


def load_rows_from_dir(dir_path: str) -> Dict[str, List[Dict[str, Any]]]:
    rows_by_table: Dict[str, List[Dict[str, Any]]] = {}
    for fname in os.listdir(dir_path):
        if not fname.lower().endswith((".sql", ".txt")):
            continue
        path = os.path.join(dir_path, fname)
        for row in parse_sql_file(path):
            rows_by_table.setdefault(row['table'], []).append(row)
    return rows_by_table


def infer_and_sort(rows_by_table: Dict[str, List[Dict[str, Any]]]) -> Tuple[Dict[str, List[Dict[str, Any]]], Dict[str, List[str]]]:
    sorted_rows: Dict[str, List[Dict[str, Any]]] = {}
    primary_keys: Dict[str, List[str]] = {}
    for table, rows in rows_by_table.items():
        sample = rows[:10]
        cols = rows[0]['columns'] if rows else []
        pk_cols = infer_primary_keys(sample, cols)
        primary_keys[table] = pk_cols
        def key_fn(row: Dict[str, Any]) -> Tuple:
            try:
                return tuple(row['values'][row['columns'].index(col)] for col in pk_cols)
            except Exception:
                return tuple()
        sorted_rows[table] = sorted(rows, key=key_fn)
    return sorted_rows, primary_keys


def compute_diffs(
    base_rows: Dict[str, List[Dict[str, Any]]],
    oracle_rows: Dict[str, List[Dict[str, Any]]],
    primary_keys: Dict[str, List[str]]
) -> Dict[str, Any]:
    table_diffs: Dict[str, Dict[str, Any]] = {}
    summary_missing: List[Dict[str, Any]] = []
    summary_extra: List[Dict[str, Any]] = []
    summary_mismatch: List[Dict[str, Any]] = []
    all_tables = set(base_rows) | set(oracle_rows)
    for table in all_tables:
        b_list = base_rows.get(table, [])
        o_list = oracle_rows.get(table, [])
        pk_cols = primary_keys.get(table, [])
        # Build maps by PK tuple
        b_map = {}
        for row in b_list:
            try:
                key = tuple(row['values'][row['columns'].index(col)] for col in pk_cols)
            except Exception:
                key = tuple()
            b_map[key] = row
        o_map = {}
        for row in o_list:
            try:
                key = tuple(row['values'][row['columns'].index(col)] for col in pk_cols)
            except Exception:
                key = tuple()
            o_map[key] = row
        missing_keys = set(b_map) - set(o_map)
        extra_keys = set(o_map) - set(b_map)
        common_keys = set(b_map) & set(o_map)
        missing = [b_map[k] for k in missing_keys]
        extra = [o_map[k] for k in extra_keys]
        mismatches = []
        for k in common_keys:
            b_vals = b_map[k]['values']
            o_vals = o_map[k]['values']
            if b_vals != o_vals:
                mismatches.append({'pk': k, 'base_values': b_vals, 'oracle_values': o_vals})
        table_diffs[table] = {
            'missing': missing,
            'extra': extra,
            'mismatches': mismatches
        }
        for row in missing:
            summary_missing.append({'table': table, 'row': row})
        for row in extra:
            summary_extra.append({'table': table, 'row': row})
        for m in mismatches:
            summary_mismatch.append({'table': table, **m})
    diff = {
        'summary': {
            'missing_in_oracle': summary_missing,
            'extra_in_oracle': summary_extra,
            'mismatches': summary_mismatch
        },
        'tables': table_diffs
    }
    return diff


def call_ollama_langchain(prompt: str, max_tokens: int = 512) -> str:
    # Implementation of call_ollama_langchain function
    pass


def call_llm_with_retry(prompt: str) -> str:
    last_exc = None
    for attempt in range(OLLAMA_RETRIES):
        try:
            # Use simple ollama run command without unsupported flags
            proc = subprocess.Popen(
                ['ollama', 'run', OLLAMA_MODEL],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Use configurable timeout for LLM calls
            out, err = proc.communicate(prompt.encode(), timeout=LLM_CALL_TIMEOUT)
            if proc.returncode != 0:
                raise RuntimeError(f"LLM process failed with error: {err.decode()}")
            return out.decode()
        except subprocess.TimeoutExpired as e:
            proc.kill()
            last_exc = e
            print(f"LLM call attempt {attempt + 1} timed out after {LLM_CALL_TIMEOUT}s")
        except Exception as e:
            last_exc = e
            print(f"LLM call attempt {attempt + 1} failed with error: {str(e)}")
    raise RuntimeError(f"LLM call failed after {OLLAMA_RETRIES} attempts. Last error: {str(last_exc)}")


def run_compare(
    base_dir: str,
    oracle_dir: str,
    output_dir: str,
    progress_callback=None
) -> Tuple[str, str, Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    
    if progress_callback:
        progress_callback(15, "📊 Parsing SQL structures...")
    
    # Load and sort
    base_rows_raw = load_rows_from_dir(base_dir)
    oracle_rows_raw = load_rows_from_dir(oracle_dir)
    
    if progress_callback:
        progress_callback(30, "🔧 Inferring primary keys...")
    
    base_rows, base_pks = infer_and_sort(base_rows_raw)
    oracle_rows, oracle_pks = infer_and_sort(oracle_rows_raw)
    
    if progress_callback:
        progress_callback(45, "🔍 Analyzing differences...")
    
    # Merge PK definitions
    pks = {**oracle_pks, **base_pks}
    # Compute diffs
    diff_json = compute_diffs(base_rows, oracle_rows, pks)
    if progress_callback:
        progress_callback(60, "📋 Creating reports...")
    
    # Write diff.json
    diff_path = os.path.join(output_dir, 'diff.json')
    with open(diff_path, 'w') as f:
        json.dump(diff_json, f, default=str, indent=2)
    # Generate Markdown report
    lines: List[str] = []
    lines.append('# Diff Report')
    lines.append('## Summary')
    lines.append(f"- Missing in Oracle: {len(diff_json['summary']['missing_in_oracle'])}")
    lines.append(f"- Extra in Oracle: {len(diff_json['summary']['extra_in_oracle'])}")
    lines.append(f"- Mismatches: {len(diff_json['summary']['mismatches'])}")
    lines.append('\n')
    for table, diffs in diff_json['tables'].items():
        lines.append(f"### Table: {table}")
        lines.append(f"- Missing: {len(diffs['missing'])}")
        lines.append(f"- Extra: {len(diffs['extra'])}")
        lines.append(f"- Mismatches: {len(diffs['mismatches'])}\n")
    report_md = '\n'.join(lines)
    report_path = os.path.join(output_dir, 'diff_report.md')
    with open(report_path, 'w') as f:
        f.write(report_md)
    # Call LLM for migration plan with reduced payload
    # Create a summary instead of full diff JSON to avoid token limits
    diff_summary = {
        'total_missing': len(diff_json['summary']['missing_in_oracle']),
        'total_extra': len(diff_json['summary']['extra_in_oracle']),
        'total_mismatches': len(diff_json['summary']['mismatches']),
        'tables_affected': list(diff_json['tables'].keys()),
        'sample_missing': diff_json['summary']['missing_in_oracle'][:3],  # Only first 3 samples
        'sample_extra': diff_json['summary']['extra_in_oracle'][:3],
        'sample_mismatches': diff_json['summary']['mismatches'][:3]
    }
    
    prompt = (
        "You are a senior database architect. Using the diff summary below, generate:\n"
        "(A) a Markdown migration guide (datatype mapping, sequence handling, SQL rewrite tips);\n"
        "(B) a JSON object with keys: steps[], risk_level, estimated_effort, warnings[].\n"
        "Return both in one response, clearly delimited.\n\n"
        f"Diff Summary: {json.dumps(diff_summary, indent=2)}"
    )
    
    if progress_callback:
        progress_callback(75, "🤖 AI processing duplicates...")
    
    try:
        llm_resp = call_llm_with_retry(prompt)
        # Split JSON and Markdown
        json_part = extract_json_from_response(llm_resp)
        try:
            plan_json = json.loads(json_part)
        except Exception as e:
            print(f"LLM JSON parsing failed: {e}, using fallback plan")
            # Fallback migration plan
            plan_json = {
                "steps": [
                    "Review diff_report.md for detailed differences",
                    "Identify missing records and add them to Oracle environment",
                    "Review extra records in Oracle for removal or verification",
                    "Resolve data mismatches by updating Oracle records"
                ],
                "risk_level": "MEDIUM",
                "estimated_effort": "4-8 hours",
                "warnings": [
                    "LLM analysis failed - manual review required",
                    "Verify all data transformations manually",
                    "Test migration in staging environment first"
                ]
            }
    except Exception as e:
        print(f"LLM call completely failed: {e}, using minimal fallback")
        llm_resp = "# Migration Guide\n\nLLM service unavailable. Please review diff_report.md manually."
        plan_json = {
            "steps": ["Manual review required - LLM service unavailable"],
            "risk_level": "HIGH", 
            "estimated_effort": "Manual assessment needed",
            "warnings": ["LLM service failed - all analysis must be done manually"]
        }
    # Safely extract markdown part
    try:
        md_part = llm_resp.replace(json_part, '').strip() if json_part in llm_resp else llm_resp.strip()
    except:
        md_part = llm_resp.strip()
    # Write migration plan files
    plan_md_path = os.path.join(output_dir, 'migration_plan.md')
    with open(plan_md_path, 'w') as f:
        f.write(md_part)
    plan_json_path = os.path.join(output_dir, 'migration_plan.json')
    with open(plan_json_path, 'w') as f:
        json.dump(plan_json, f, default=str, indent=2)
    
    if progress_callback:
        progress_callback(90, "📦 Finalizing results...")
    
    # Package into ZIP
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"compare_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in ['diff.json', 'diff_report.md', 'migration_plan.md', 'migration_plan.json']:
            zf.write(os.path.join(output_dir, fname), arcname=fname)
    return zip_path, zip_filename, diff_json


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Dev CLI for compare & migrate')
    parser.add_argument('--base', required=True, help='Path to base scripts directory')
    parser.add_argument('--oracle', required=True, help='Path to oracle scripts directory')
    parser.add_argument('--out', required=False, default='', help='Output directory override')
    args = parser.parse_args()
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = args.out if args.out else os.path.join('results', f"compare_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    zip_path, zip_filename, diff_json = run_compare(args.base, args.oracle, out_dir)
    stub = {'status': 'ok', 'zip_filename': zip_filename}
    print(json.dumps(stub)) 