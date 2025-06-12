import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure backend package is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main  # FastAPI app

@pytest.fixture
def client(monkeypatch):
    # Monkeypatch the LLM call to return deterministic output
    import compare_utils
    def fake_llm(prompt: str) -> str:
        json_part = '{"steps": ["step1"], "risk_level": "low", "estimated_effort": 1, "warnings": []}'
        md_part = '# Migration Guide'
        # Return markdown then explicit delimiter and JSON
        return md_part + '\nJSON_RESPONSE:' + json_part
    monkeypatch.setattr(compare_utils, 'call_llm_with_retry', fake_llm)
    return TestClient(main.app)


def test_compare_endpoint_success(client, tmp_path):
    # Create minimal SQL files
    base_file = tmp_path / 'b.sql'
    oracle_file = tmp_path / 'o.sql'
    content = "INSERT INTO t (id,val) VALUES (1,'a');"
    base_file.write_text(content)
    oracle_file.write_text(content)

    files = [
        ('base_files', ('b.sql', base_file.read_bytes(), 'text/sql')),
        ('oracle_files', ('o.sql', oracle_file.read_bytes(), 'text/sql'))
    ]
    response = client.post('/compare', files=files)
    assert response.status_code == 200
    # Check headers and zip content
    cd = response.headers.get('Content-Disposition', '')
    assert 'attachment' in cd and cd.endswith('.zip"')

    from io import BytesIO
    import zipfile
    z = zipfile.ZipFile(BytesIO(response.content))
    names = z.namelist()
    assert 'diff.json' in names
    assert 'migration_plan.json' in names
    assert 'migration_plan.md' in names 