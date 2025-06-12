import os, json, subprocess, re
from typing import Any, Dict, List
from config_loader import config

try:
    from langchain_ollama import OllamaLLM
except ImportError:
    try:
        from langchain_community.llms import Ollama as OllamaLLM
    except ImportError:
        # Fallback if neither is available
        OllamaLLM = None

# Configuration from YAML
OLLAMA_HOST = config.get('ollama.host', 'http://localhost:11434')
OLLAMA_MODEL = config.get('ollama.model', 'llama3:8b')
OLLAMA_MAX_TOKENS = config.get('ollama.max_tokens', 16384)
OLLAMA_TIMEOUT = config.get('ollama.timeout_seconds', 600)
OLLAMA_RETRIES = config.get('ollama.retry_attempts', 3)

def call_ollama_langchain(prompt: str, max_tokens: int = None) -> str:
    if OllamaLLM is None:
        raise ImportError("Neither langchain_ollama nor langchain_community is available")
    if max_tokens is None:
        max_tokens = OLLAMA_MAX_TOKENS
    llm = OllamaLLM(model=OLLAMA_MODEL, base_url=OLLAMA_HOST, max_tokens=max_tokens)
    return llm(prompt)

def call_ollama_subprocess(prompt: str) -> str:
    p = subprocess.Popen(['ollama', 'run', OLLAMA_MODEL], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = p.communicate(prompt.encode())
    return out.decode()

def reliable_call(prompt: str) -> str:
    try:
        return call_ollama_langchain(prompt)
    except Exception:
        return call_ollama_subprocess(prompt)

def extract_json_from_response(response: str) -> str:
    """Extract JSON object or array from LLM response text by brace matching."""
    resp = response.strip()
    # Find start of JSON object or array
    idx_obj = resp.find('{')
    idx_arr = resp.find('[')
    # Choose earliest if both exist
    if idx_obj == -1 and idx_arr == -1:
        return resp
    if idx_obj == -1 or (idx_arr != -1 and idx_arr < idx_obj):
        start = idx_arr
        open_char, close_char = '[', ']'
    else:
        start = idx_obj
        open_char, close_char = '{', '}'
    # Brace/bracket matching
    depth = 0
    for i in range(start, len(resp)):
        if resp[i] == open_char:
            depth += 1
        elif resp[i] == close_char:
            depth -= 1
            if depth == 0:
                candidate = resp[start:i+1]
                # Validate JSON
                try:
                    json.loads(candidate)
                    return candidate
                except json.JSONDecodeError:
                    break
    # Fallback: return full response
    return resp

def infer_primary_keys(sample_rows: List[Dict[str, Any]], columns: List[str]) -> List[str]:
    """Use enhanced fallback logic first, then LLM as last resort"""
    try:
        # Enhanced intelligent fallback strategy (try first to avoid LLM calls)
        print(f"Inferring primary keys for columns: {columns}")
        
        # Rule 1: Look for obvious primary key names
        for col in columns:
            col_lower = col.lower()
            if col_lower in ['id', 'pk', 'primary_key', 'key']:
                print(f"Found obvious primary key: {col}")
                return [col]
        
        # Rule 2: Look for columns ending with '_id' (but only if there's one)
        id_columns = [col for col in columns if col.lower().endswith('_id')]
        if len(id_columns) == 1:
            print(f"Found single ID column: {id_columns[0]}")
            return id_columns
        
        # Rule 3: For composite keys, look for common patterns
        if len(id_columns) >= 2:
            print(f"Found multiple ID columns, using composite key: {id_columns}")
            return id_columns[:2]  # Limit to 2 for performance
        
        # Rule 4: If we have sample data, check for numeric/unique patterns
        if sample_rows and len(sample_rows) > 1:
            for col in columns:
                try:
                    col_idx = sample_rows[0]['columns'].index(col) if 'columns' in sample_rows[0] else columns.index(col)
                    values = [row['values'][col_idx] for row in sample_rows if 'values' in row and len(row['values']) > col_idx]
                    # Check if values are numeric and appear unique
                    if len(set(values)) == len(values) and all(str(v).isdigit() for v in values):
                        print(f"Found unique numeric column: {col}")
                        return [col]
                except (IndexError, ValueError, KeyError):
                    continue
        
        # Only use LLM if fallback fails and we have small sample data
        if len(sample_rows) <= 5 and len(columns) <= 10:
            print("Using LLM for primary key inference...")
            # Create a smaller, more focused prompt
            prompt = f"""Database table columns: {columns}
            
Find primary key. Respond with JSON array only: ["column_name"]

JSON:"""

            response = reliable_call(prompt)
            json_str = extract_json_from_response(response)
            
            # Parse the JSON response
            primary_keys = json.loads(json_str)
            
            # Validate the response
            if isinstance(primary_keys, list) and all(pk in columns for pk in primary_keys):
                print(f"LLM suggested primary keys: {primary_keys}")
                return primary_keys
            else:
                raise ValueError("Invalid primary key response")
        
        # Final fallback: use first column
        print(f"Using fallback: first column {columns[0] if columns else 'none'}")
        return [columns[0]] if columns else []
            
    except Exception as e:
        print(f"LLM primary key inference failed: {e}, using fallback")
        # Final intelligent fallback strategy
        for col in columns:
            if col.lower() in ['id', 'pk', 'primary_key']:
                return [col]
            if col.lower().endswith('_id') and not any(other.lower().endswith('_id') and other != col for other in columns):
                return [col]
        return [columns[0]] if columns else []

def explain_anomalies(anomalies: Dict[str, Any]) -> Dict[str, Any]:
    """Use LLM to provide intelligent analysis of data anomalies"""
    try:
        duplicates = anomalies.get('duplicates', [])
        order_issues = anomalies.get('order_issues', [])
        
        prompt = f"""You are a database consultant analyzing SQL data quality issues. Provide recommendations for the following anomalies:

Duplicate Records Found: {len(duplicates)}
Ordering Issues Found: {len(order_issues)}

Sample Duplicate Data: {duplicates[:2] if duplicates else "None"}
Sample Order Issues: {order_issues[:2] if order_issues else "None"}

Provide a JSON response with:
1. "plan": A brief action plan (1-2 sentences)
2. "markdown": A detailed markdown explanation with recommendations

The markdown should include:
- Root cause analysis
- Impact assessment  
- Specific remediation steps
- Prevention strategies

Respond with ONLY valid JSON in this format:
{{"plan": "action plan text", "markdown": "detailed markdown explanation"}}

JSON Response:"""

        response = reliable_call(prompt)
        json_str = extract_json_from_response(response)
        
        result = json.loads(json_str)
        
        # Validate the response structure
        if isinstance(result, dict) and 'plan' in result and 'markdown' in result:
            return result
        else:
            raise ValueError("Invalid anomaly explanation response")
            
    except Exception as e:
        print(f"LLM anomaly explanation failed: {e}, using fallback")
        # Enhanced fallback with more detailed analysis
        total_issues = len(duplicates) + len(order_issues)
        severity = "HIGH" if total_issues > 10 else "MEDIUM" if total_issues > 0 else "LOW"
        
        plan = f"Manual review required - {severity} priority" if total_issues > 0 else "No critical issues detected"
        
        markdown = f"""## Data Quality Analysis

**Severity Level:** {severity}

### Issues Detected:
- **Duplicate Records:** {len(duplicates)} found
- **Ordering Issues:** {len(order_issues)} found

### Impact Assessment:
{"- Data integrity compromised by duplicate entries" if duplicates else "- No duplicate data detected"}
{"- Table dependency order may cause referential integrity issues" if order_issues else "- Table ordering appears correct"}

### Recommended Actions:
1. **Immediate:** Review and remove duplicate entries before migration
2. **Data Validation:** Implement unique constraints on primary keys
3. **Process Improvement:** Add data validation checks in source system
4. **Monitoring:** Set up alerts for future duplicate detection

### Prevention Strategies:
- Implement proper primary key constraints
- Add data validation at application level
- Regular data quality audits
- Consider implementing soft deletes instead of hard deletes
"""
        
        return {
            'plan': plan,
            'markdown': markdown
        }

def analyze_data_quality_with_ai(sample_data: List[Dict], table_name: str) -> Dict[str, Any]:
    """AI-powered comprehensive data quality analysis"""
    try:
        # Create focused prompt for data quality analysis
        prompt = f"""You are a data quality expert analyzing SQL data for the table: {table_name}

Sample Data: {json.dumps(sample_data[:10], indent=2)[:1500]}

Analyze for:
1. Potential duplicate patterns (semantic, formatting, typos)
2. Data inconsistencies (case, spacing, format variations)
3. Primary key candidates based on data patterns
4. Foreign key relationships
5. Data quality issues

Respond with JSON:
{{
    "primary_key_suggestions": ["column_name"],
    "duplicate_patterns": [
        {{"pattern": "description", "columns": ["col1"], "example": "value"}}
    ],
    "quality_issues": [
        {{"issue": "description", "severity": "HIGH|MEDIUM|LOW", "columns": ["col1"]}}
    ],
    "recommended_actions": ["action1", "action2"]
}}

JSON:"""

        response = reliable_call(prompt)
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)
        
        # Validate and enhance the response
        if not isinstance(result, dict):
            raise ValueError("Invalid AI response format")
            
        # Ensure all required keys exist
        result.setdefault('primary_key_suggestions', [])
        result.setdefault('duplicate_patterns', [])
        result.setdefault('quality_issues', [])
        result.setdefault('recommended_actions', ['Manual review recommended'])
        
        print(f"AI data quality analysis completed for {table_name}")
        return result
        
    except Exception as e:
        print(f"AI data quality analysis failed: {e}, using fallback analysis")
        return {
            'primary_key_suggestions': [],
            'duplicate_patterns': [],
            'quality_issues': [{'issue': 'AI analysis unavailable', 'severity': 'LOW', 'columns': []}],
            'recommended_actions': ['Manual data quality review required']
        }

def smart_duplicate_detection(rows: List[Dict], columns: List[str]) -> Dict[str, Any]:
    """AI-enhanced duplicate detection with business logic understanding"""
    try:
        if len(rows) > 50:
            # Sample for large datasets
            sample_rows = rows[:20]
        else:
            sample_rows = rows
            
        # Prepare data for AI analysis
        analysis_data = []
        for i, row in enumerate(sample_rows):
            analysis_data.append({
                'row_id': i,
                'values': row.get('values', [])[:8],  # Limit to 8 columns
                'source': row.get('source_file', 'unknown')
            })
        
        prompt = f"""You are a database expert. Find duplicates in this SQL data:

Columns: {columns}
Data: {json.dumps(analysis_data, indent=2)[:1200]}

Identify:
1. Exact duplicates (same values)
2. Semantic duplicates (same meaning, different format)
3. Near-duplicates (typos, case differences)

Return JSON:
{{
    "exact_duplicates": [
        {{"group": 1, "rows": [0, 5], "reason": "identical values"}}
    ],
    "fuzzy_duplicates": [
        {{"group": 2, "rows": [1, 3], "reason": "same entity, different format", "confidence": 0.9}}
    ]
}}

JSON:"""

        response = reliable_call(prompt)
        json_str = extract_json_from_response(response)
        result = json.loads(json_str)
        
        return result
        
    except Exception as e:
        print(f"Smart duplicate detection failed: {e}")
        return {'exact_duplicates': [], 'fuzzy_duplicates': []} 