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
from transform import convert_insert_statements

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


def compute_bidirectional_diffs(
    source_rows: Dict[str, List[Dict[str, Any]]],
    target_rows: Dict[str, List[Dict[str, Any]]],
    primary_keys: Dict[str, List[str]],
    direction: str
) -> Dict[str, Any]:
    """
    Compute differences between source and target datasets.
    Direction-aware labeling for better clarity.
    """
    source_type = "PostgreSQL" if direction == "pg2ora" else "Oracle"
    target_type = "Oracle" if direction == "pg2ora" else "PostgreSQL"
    
    table_diffs: Dict[str, Dict[str, Any]] = {}
    summary_missing: List[Dict[str, Any]] = []
    summary_extra: List[Dict[str, Any]] = []
    summary_mismatch: List[Dict[str, Any]] = []
    
    all_tables = set(source_rows) | set(target_rows)
    
    for table in all_tables:
        s_list = source_rows.get(table, [])
        t_list = target_rows.get(table, [])
        pk_cols = primary_keys.get(table, [])
        
        # Build maps by PK tuple
        s_map = {}
        for row in s_list:
            try:
                key = tuple(row['values'][row['columns'].index(col)] for col in pk_cols)
            except Exception:
                key = tuple()
            s_map[key] = row
            
        t_map = {}
        for row in t_list:
            try:
                key = tuple(row['values'][row['columns'].index(col)] for col in pk_cols)
            except Exception:
                key = tuple()
            t_map[key] = row
        
        missing_keys = set(s_map) - set(t_map)
        extra_keys = set(t_map) - set(s_map)
        common_keys = set(s_map) & set(t_map)
        
        missing = [s_map[k] for k in missing_keys]
        extra = [t_map[k] for k in extra_keys]
        mismatches = []
        
        for k in common_keys:
            s_vals = s_map[k]['values']
            t_vals = t_map[k]['values']
            if s_vals != t_vals:
                mismatches.append({
                    'pk': k, 
                    f'{source_type.lower()}_values': s_vals, 
                    f'{target_type.lower()}_values': t_vals
                })
        
        table_diffs[table] = {
            'missing_in_target': missing,
            'extra_in_target': extra,
            'mismatches': mismatches
        }
        
        for row in missing:
            summary_missing.append({'table': table, 'row': row})
        for row in extra:
            summary_extra.append({'table': table, 'row': row})
        for m in mismatches:
            summary_mismatch.append({'table': table, **m})
    
    diff = {
        'metadata': {
            'direction': direction,
            'source_type': source_type,
            'target_type': target_type,
            'generated_at': datetime.datetime.now().isoformat()
        },
        'summary': {
            f'missing_in_{target_type.lower()}': summary_missing,
            f'extra_in_{target_type.lower()}': summary_extra,
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


def generate_conversion_sql(
    missing_rows: List[Dict[str, Any]], 
    direction: str,
    output_dir: str
) -> str:
    """
    Generate INSERT statements for missing rows, converted to target dialect.
    """
    if not missing_rows:
        return ""
    
    # Group rows by table
    rows_by_table = {}
    for item in missing_rows:
        table = item['table']
        row = item['row']
        if table not in rows_by_table:
            rows_by_table[table] = []
        rows_by_table[table].append(row)
    
    # Generate converted SQL
    converted_sql_lines = []
    converted_sql_lines.append(f"-- Converted INSERT statements for missing records")
    converted_sql_lines.append(f"-- Direction: {direction}")
    converted_sql_lines.append(f"-- Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    converted_sql_lines.append("")
    
    for table, rows in rows_by_table.items():
        converted_sql_lines.append(f"-- Table: {table}")
        converted_sql_lines.append(f"-- Records: {len(rows)}")
        converted_sql_lines.append("")
        
        # Convert each row
        for row in rows:
            converted_insert = convert_insert_statements([row], direction)[0]
            converted_sql_lines.append(converted_insert)
        
        converted_sql_lines.append("")
    
    # Write to file
    sql_filename = f"missing_records_{direction}.sql"
    sql_path = os.path.join(output_dir, sql_filename)
    with open(sql_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(converted_sql_lines))
    
    return sql_filename


def run_compare(
    source_dir: str,
    target_dir: str,
    output_dir: str,
    direction: str,
    progress_callback=None
) -> Tuple[str, str, Dict[str, Any]]:
    os.makedirs(output_dir, exist_ok=True)
    
    if progress_callback:
        progress_callback(15, "📊 Parsing SQL structures...")
    
    # Load and sort
    source_rows_raw = load_rows_from_dir(source_dir)
    target_rows_raw = load_rows_from_dir(target_dir)
    
    if progress_callback:
        progress_callback(30, "🔧 Inferring primary keys...")
    
    source_rows, source_pks = infer_and_sort(source_rows_raw)
    target_rows, target_pks = infer_and_sort(target_rows_raw)
    
    if progress_callback:
        progress_callback(45, "🔍 Analyzing differences...")
    
    # Merge PK definitions
    pks = {**target_pks, **source_pks}
    
    # Compute bidirectional diffs
    diff_json = compute_bidirectional_diffs(source_rows, target_rows, pks, direction)
    
    if progress_callback:
        progress_callback(60, "📋 Creating reports...")
    
    # Write diff.json
    diff_path = os.path.join(output_dir, 'diff.json')
    with open(diff_path, 'w', encoding='utf-8') as f:
        json.dump(diff_json, f, default=str, indent=2)
    
    # Generate bidirectional Markdown report
    source_type = diff_json['metadata']['source_type']
    target_type = diff_json['metadata']['target_type']
    
    lines: List[str] = []
    lines.append(f'# {direction.upper()} Migration Diff Report')
    lines.append(f'**Direction:** {source_type} → {target_type}')
    lines.append(f'**Generated:** {diff_json["metadata"]["generated_at"]}')
    lines.append('')
    lines.append('## Summary')
    missing_key = f'missing_in_{target_type.lower()}'
    extra_key = f'extra_in_{target_type.lower()}'
    lines.append(f"- Missing in {target_type}: {len(diff_json['summary'][missing_key])}")
    lines.append(f"- Extra in {target_type}: {len(diff_json['summary'][extra_key])}")
    lines.append(f"- Mismatches: {len(diff_json['summary']['mismatches'])}")
    lines.append('')
    
    for table, diffs in diff_json['tables'].items():
        lines.append(f"### Table: {table}")
        lines.append(f"- Missing in {target_type}: {len(diffs['missing_in_target'])}")
        lines.append(f"- Extra in {target_type}: {len(diffs['extra_in_target'])}")
        lines.append(f"- Mismatches: {len(diffs['mismatches'])}")
        lines.append('')
    
    report_md = '\n'.join(lines)
    report_path = os.path.join(output_dir, 'diff_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    if progress_callback:
        progress_callback(70, "🔄 Generating conversion SQL...")
    
    # Generate conversion SQL for missing records
    missing_records = diff_json['summary'][missing_key]
    conversion_sql_file = generate_conversion_sql(missing_records, direction, output_dir)
    
    # Call LLM for migration plan with reduced payload
    diff_summary = {
        'direction': direction,
        'source_type': source_type,
        'target_type': target_type,
        'total_missing': len(diff_json['summary'][missing_key]),
        'total_extra': len(diff_json['summary'][extra_key]),
        'total_mismatches': len(diff_json['summary']['mismatches']),
        'tables_affected': list(diff_json['tables'].keys()),
        'sample_missing': diff_json['summary'][missing_key][:3],
        'sample_extra': diff_json['summary'][extra_key][:3],
        'sample_mismatches': diff_json['summary']['mismatches'][:3]
    }
    
    prompt = (
        f"You are a senior database architect. Using the diff summary below for {direction.upper()} migration, generate:\n"
        f"(A) a Markdown migration guide ({source_type}→{target_type} datatype mapping, sequence handling, SQL rewrite tips);\n"
        "(B) a JSON object with keys: steps[], risk_level, estimated_effort, warnings[].\n"
        "Return both in one response, clearly delimited.\n\n"
        f"Diff Summary: {json.dumps(diff_summary, indent=2)}"
    )
    
    if progress_callback:
        progress_callback(80, "🤖 AI processing migration plan...")
    
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
                "direction": direction,
                "source_type": source_type,
                "target_type": target_type,
                "steps": [
                    f"Review diff_report.md for detailed {direction} differences",
                    f"Apply {conversion_sql_file} to add missing records to {target_type}",
                    f"Review extra records in {target_type} for removal or verification",
                    "Resolve data mismatches by updating target records",
                    f"Test {source_type}→{target_type} conversion in staging environment"
                ],
                "risk_level": "MEDIUM",
                "estimated_effort": "4-8 hours",
                "warnings": [
                    "LLM analysis failed - manual review required",
                    f"Verify all {direction} transformations manually",
                    "Test migration in staging environment first"
                ]
            }
    except Exception as e:
        print(f"LLM call completely failed: {e}, using minimal fallback")
        llm_resp = f"# {direction.upper()} Migration Guide\n\nLLM service unavailable. Please review diff_report.md manually."
        plan_json = {
            "direction": direction,
            "source_type": source_type,
            "target_type": target_type,
            "steps": [f"Manual review required - LLM service unavailable for {direction} migration"],
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
    with open(plan_md_path, 'w', encoding='utf-8') as f:
        f.write(md_part)
    
    plan_json_path = os.path.join(output_dir, 'migration_plan.json')
    with open(plan_json_path, 'w', encoding='utf-8') as f:
        json.dump(plan_json, f, default=str, indent=2)
    
    if progress_callback:
        progress_callback(90, "📦 Finalizing results...")
    
    # Package into ZIP
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"compare_{direction}_{timestamp}.zip"
    zip_path = os.path.join(output_dir, zip_filename)
    
    # List of files to include in ZIP
    files_to_zip = ['diff.json', 'diff_report.md', 'migration_plan.md', 'migration_plan.json']
    if conversion_sql_file:
        files_to_zip.append(conversion_sql_file)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in files_to_zip:
            file_path = os.path.join(output_dir, fname)
            if os.path.exists(file_path):
                zf.write(file_path, arcname=fname)
    
    return zip_path, zip_filename, diff_json


# Legacy function name for backward compatibility
def compute_diffs(base_rows, oracle_rows, primary_keys):
    """Legacy function for backward compatibility"""
    return compute_bidirectional_diffs(base_rows, oracle_rows, primary_keys, "pg2ora")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Dev CLI for bidirectional compare & migrate')
    parser.add_argument('--source', required=True, help='Path to source scripts directory')
    parser.add_argument('--target', required=True, help='Path to target scripts directory')
    parser.add_argument('--direction', required=True, choices=['pg2ora', 'ora2pg'], help='Conversion direction')
    parser.add_argument('--out', required=False, default='', help='Output directory override')
    args = parser.parse_args()
    
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    out_dir = args.out if args.out else os.path.join('results', f"compare_{args.direction}_{ts}")
    os.makedirs(out_dir, exist_ok=True)
    
    zip_path, zip_filename, diff_json = run_compare(args.source, args.target, out_dir, args.direction)
    stub = {'status': 'ok', 'zip_filename': zip_filename, 'direction': args.direction}
    print(json.dumps(stub)) 