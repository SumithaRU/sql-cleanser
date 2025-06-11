import os, json, subprocess
from langchain.llms import Ollama
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

def infer_primary_keys(sample_rows: List[Dict[str, Any]], columns: List[str]) -> List[str]:
    payload = {'columns': columns, 'sample_rows': sample_rows}
    prompt = f"### Input\n{json.dumps(payload)}\n### Task\nReturn the most likely primary key columns as JSON list.\n### Output"
    response = reliable_call(prompt)
    return json.loads(response)

def explain_anomalies(anomalies: Dict[str, Any]) -> Dict[str, Any]:
    prompt = f"### Input\n{json.dumps(anomalies)}\n### Task\nReturn remediation plan and markdown explanation in JSON with keys 'plan' and 'markdown'.\n### Output"
    response = reliable_call(prompt)
    return json.loads(response) 