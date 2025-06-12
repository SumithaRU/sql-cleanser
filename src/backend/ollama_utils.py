import os, json, subprocess, re
from langchain_community.llms import Ollama
from typing import Any, Dict, List

OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

def call_ollama_langchain(prompt: str, max_tokens: int = 512) -> str:
    llm = Ollama(model='llama3:8b', base_url=OLLAMA_HOST, max_tokens=max_tokens)
    return llm(prompt)

def call_ollama_subprocess(prompt: str) -> str:
    p = subprocess.Popen(['ollama', 'run', 'llama3:8b'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out, _ = p.communicate(prompt.encode())
    return out.decode()

def reliable_call(prompt: str) -> str:
    try:
        return call_ollama_langchain(prompt)
    except Exception:
        return call_ollama_subprocess(prompt)

def extract_json_from_response(response: str) -> str:
    """Extract JSON from LLM response that might contain extra text"""
    # Look for JSON objects or arrays in the response
    json_pattern = r'(\[.*?\]|\{.*?\})'
    matches = re.findall(json_pattern, response, re.DOTALL)
    
    for match in matches:
        try:
            # Test if it's valid JSON
            json.loads(match)
            return match
        except:
            continue
    
    # If no valid JSON found, return the original response
    return response.strip()

def infer_primary_keys(sample_rows: List[Dict[str, Any]], columns: List[str]) -> List[str]:
    """Use LLM to intelligently infer primary keys from sample data"""
    try:
        # Create a more structured prompt for better LLM understanding
        prompt = f"""You are a database expert. Analyze the following table structure and sample data to identify the primary key columns.

Table Columns: {columns}
Sample Data (first few rows): {sample_rows[:3]}

Rules:
1. Primary keys are usually named 'id', 'pk', or end with '_id' 
2. Primary key values should be unique across rows
3. Primary keys are typically numeric or UUID
4. Look for patterns in the data values

Respond with ONLY a JSON array of column names that form the primary key.
Example: ["id"] or ["user_id", "order_id"]

JSON Response:"""

        response = reliable_call(prompt)
        json_str = extract_json_from_response(response)
        
        # Parse the JSON response
        primary_keys = json.loads(json_str)
        
        # Validate the response
        if isinstance(primary_keys, list) and all(pk in columns for pk in primary_keys):
            return primary_keys
        else:
            raise ValueError("Invalid primary key response")
            
    except Exception as e:
        print(f"LLM primary key inference failed: {e}, using fallback")
        # Intelligent fallback strategy
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