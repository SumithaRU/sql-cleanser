import os, re, sqlparse
from typing import List, Dict

INSERT_REGEX = re.compile(r"INSERT\s+INTO\s+['\"]?(\w+)['\"]?\s*\((.*?)\)\s*VALUES\s*(\(.+\));", re.IGNORECASE | re.DOTALL)

def parse_sql_file(path: str) -> List[Dict]:
    rows = []
    with open(path, 'r') as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line.upper().startswith('INSERT'):
                continue
            m = INSERT_REGEX.match(line)
            if not m:
                continue
            table = m.group(1)
            cols = [c.strip().strip("'") for c in m.group(2).split(',')]
            vals_str = m.group(3)
            val_groups = re.findall(r"\((.*?)\)", vals_str)
            for vg in val_groups:
                values = [v.strip().strip("'") for v in vg.split(',')]
                rows.append({'table': table, 'columns': cols, 'values': values, 'source_file': path, 'lineno': lineno})
    return rows

def parse_all(input_dir: str) -> Dict[str, List[Dict]]:
    rows_by_table: Dict[str, List[Dict]] = {}
    for fname in os.listdir(input_dir):
        if not fname.lower().endswith('.sql'):
            continue
        path = os.path.join(input_dir, fname)
        for row in parse_sql_file(path):
            rows_by_table.setdefault(row['table'], []).append(row)
    return rows_by_table 