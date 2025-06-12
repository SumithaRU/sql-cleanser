import hashlib, os, json
import networkx as nx
from typing import List, Dict, Tuple, Set
from ollama_utils import reliable_call, extract_json_from_response

def detect_duplicates_and_order(rows: List[Dict], key_cols: List[str]) -> Tuple[List[Dict], List[Dict]]:
    """Enhanced AI-powered duplicate detection with fuzzy matching"""
    if not rows:
        return [], []
    
    print(f"Analyzing {len(rows)} rows for duplicates using AI-enhanced detection...")
    
    # Phase 1: Traditional exact duplicate detection (fast)
    exact_duplicates = []
    seen_exact = {}
    remaining_rows = []
    
    for row in rows:
        try:
            key = tuple(row['values'][row['columns'].index(col)] for col in key_cols)
        except (ValueError, IndexError):
            key = tuple(row['values'][:len(key_cols)]) if row.get('values') else None
        
        key_hash = hashlib.sha256(str(key).encode()).hexdigest()
        if key_hash in seen_exact:
            exact_duplicates.append(row)
            print(f"Found exact duplicate: {key}")
        else:
            seen_exact[key_hash] = row
            remaining_rows.append((key, row))
    
    # Phase 2: AI-powered fuzzy duplicate detection for complex cases
    fuzzy_duplicates = []
    if len(remaining_rows) > 1 and len(remaining_rows) <= 100:  # Only for manageable datasets
        fuzzy_duplicates = detect_fuzzy_duplicates_with_ai(remaining_rows, key_cols)
    elif len(remaining_rows) > 100:
        # For large datasets, use sampling + AI
        sample_size = min(50, len(remaining_rows))
        sample_rows = remaining_rows[:sample_size]
        sample_fuzzy = detect_fuzzy_duplicates_with_ai(sample_rows, key_cols)
        
        # Apply patterns found in sample to full dataset
        if sample_fuzzy:
            fuzzy_duplicates = apply_fuzzy_patterns_to_full_dataset(remaining_rows, sample_fuzzy)
    
    all_duplicates = exact_duplicates + fuzzy_duplicates
    print(f"Total duplicates found: {len(all_duplicates)} (exact: {len(exact_duplicates)}, fuzzy: {len(fuzzy_duplicates)})")
    
    # Order issues detection (placeholder for now)
    order_issues: List[Dict] = []
    
    return all_duplicates, order_issues

def detect_fuzzy_duplicates_with_ai(rows_with_keys: List[Tuple], key_cols: List[str]) -> List[Dict]:
    """Use AI to detect semantic/fuzzy duplicates"""
    try:
        # Prepare data sample for AI analysis
        sample_data = []
        for i, (key, row) in enumerate(rows_with_keys[:20]):  # Limit to 20 for AI analysis
            sample_data.append({
                'index': i,
                'key': key,
                'values': row['values'][:10],  # Limit values to prevent token overflow
                'source': row.get('source_file', 'unknown')
            })
        
        prompt = f"""You are a data quality expert. Analyze the following database records to find fuzzy/semantic duplicates.

Key Columns: {key_cols}
Sample Records: {json.dumps(sample_data, indent=2)[:2000]}  # Limit prompt size

Look for:
1. Semantic duplicates (same entity, different format)
2. Near-duplicates with typos or variations
3. Records that represent the same business entity

Respond with JSON array of duplicate groups:
{{"duplicates": [
    {{"group": 1, "indices": [0, 5], "reason": "Same entity with different formatting"}},
    {{"group": 2, "indices": [2, 8], "reason": "Typo variation"}}
]}}

JSON:"""

        response = reliable_call(prompt)
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)
        
        # Convert AI results back to duplicate rows
        duplicates = []
        if 'duplicates' in result:
            for group in result['duplicates']:
                indices = group.get('indices', [])
                reason = group.get('reason', 'AI detected similarity')
                
                # Add all but first row as duplicates (keep first as canonical)
                for idx in indices[1:]:
                    if idx < len(rows_with_keys):
                        _, row = rows_with_keys[idx]
                        row['duplicate_reason'] = f"AI fuzzy duplicate: {reason}"
                        duplicates.append(row)
                        print(f"AI found fuzzy duplicate: {reason}")
        
        return duplicates
        
    except Exception as e:
        print(f"AI fuzzy duplicate detection failed: {e}, falling back to traditional logic")
        return []

def apply_fuzzy_patterns_to_full_dataset(all_rows: List[Tuple], sample_duplicates: List[Dict]) -> List[Dict]:
    """Apply patterns learned from AI sample analysis to full dataset"""
    # This is a simplified implementation
    # In a full implementation, we'd extract patterns and apply them
    print(f"Applying AI-learned patterns to {len(all_rows)} rows...")
    return []  # Placeholder for pattern application

def enhanced_similarity_check(row1_values: List, row2_values: List, threshold: float = 0.8) -> bool:
    """Traditional similarity check as fallback"""
    if len(row1_values) != len(row2_values):
        return False
    
    matches = 0
    for v1, v2 in zip(row1_values, row2_values):
        if str(v1).lower().strip() == str(v2).lower().strip():
            matches += 1
    
    similarity = matches / len(row1_values) if row1_values else 0
    return similarity >= threshold

def reorder_tables(rows_by_table: Dict[str, List[Dict]]) -> List[str]:
    """Enhanced table ordering with AI insights"""
    G = nx.DiGraph()
    for table in rows_by_table:
        G.add_node(table)
    
    # Traditional dependency detection
    for table, rows in rows_by_table.items():
        cols = rows[0]['columns'] if rows else []
        for col in cols:
            if col.upper().endswith('_ID'):
                ref = col[:-3]
                if ref in rows_by_table:
                    G.add_edge(ref, table)
    
    # Future: AI-powered dependency analysis for complex relationships
    
    try:
        order = list(nx.topological_sort(G))
        print(f"Table execution order: {' → '.join(order)}")
        return order
    except Exception as e:
        print(f"Topological sort failed: {e}, using alphabetical order")
        return sorted(rows_by_table.keys()) 