import hashlib, os
import networkx as nx
from typing import List, Dict, Tuple

def detect_duplicates_and_order(rows: List[Dict], key_cols: List[str]) -> Tuple[List[Dict], List[Dict]]:
    seen = {}
    duplicates = []
    for row in rows:
        try:
            key = tuple(row['values'][row['columns'].index(col)] for col in key_cols)
        except ValueError:
            key = None
        key_hash = hashlib.sha256(str(key).encode()).hexdigest()
        if key_hash in seen:
            duplicates.append(row)
        else:
            seen[key_hash] = row
    order_issues: List[Dict] = []
    return duplicates, order_issues

def reorder_tables(rows_by_table: Dict[str, List[Dict]]) -> List[str]:
    G = nx.DiGraph()
    for table in rows_by_table:
        G.add_node(table)
    for table, rows in rows_by_table.items():
        cols = rows[0]['columns'] if rows else []
        for col in cols:
            if col.upper().endswith('_ID'):
                ref = col[:-3]
                if ref in rows_by_table:
                    G.add_edge(ref, table)
    try:
        return list(nx.topological_sort(G))
    except Exception:
        return list(rows_by_table.keys()) 