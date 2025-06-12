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
    source_file = tmp_path / 'source.sql'
    target_file = tmp_path / 'target.sql'
    content = "INSERT INTO t (id,val) VALUES (1,'a');"
    source_file.write_text(content)
    target_file.write_text(content)

    # Test the new bidirectional endpoint
    response = client.post('/compare', 
        data={'direction': 'pg2ora'},
        files=[
            ('source_files', ('source.sql', source_file.read_bytes(), 'text/sql')),
            ('target_files', ('target.sql', target_file.read_bytes(), 'text/sql'))
        ]
    )
    
    # Should return 202 for async processing
    assert response.status_code == 202
    data = response.json()
    assert 'job_id' in data
    assert data['status'] == 'started'
    assert data['direction'] == 'pg2ora'


def test_compare_legacy_endpoint(client, tmp_path):
    # Test the legacy endpoint for backward compatibility
    base_file = tmp_path / 'base.sql'
    oracle_file = tmp_path / 'oracle.sql'
    content = "INSERT INTO t (id,val) VALUES (1,'a');"
    base_file.write_text(content)
    oracle_file.write_text(content)

    response = client.post('/compare-legacy', 
        files=[
            ('base_files', ('base.sql', base_file.read_bytes(), 'text/sql')),
            ('oracle_files', ('oracle.sql', oracle_file.read_bytes(), 'text/sql'))
        ]
    )
    
    # Should return 202 for async processing 
    assert response.status_code == 202
    data = response.json()
    assert 'job_id' in data
    assert data['status'] == 'started'
    assert data['direction'] == 'pg2ora'


def test_compare_endpoint_invalid_direction(client, tmp_path):
    # Test invalid direction parameter
    source_file = tmp_path / 'source.sql'
    target_file = tmp_path / 'target.sql'
    content = "INSERT INTO t (id,val) VALUES (1,'a');"
    source_file.write_text(content)
    target_file.write_text(content)

    response = client.post('/compare', 
        data={'direction': 'invalid'},
        files=[
            ('source_files', ('source.sql', source_file.read_bytes(), 'text/sql')),
            ('target_files', ('target.sql', target_file.read_bytes(), 'text/sql'))
        ]
    )
    
    assert response.status_code == 400
    data = response.json()
    assert 'Direction must be' in data['detail']


def test_compare_endpoint_missing_files(client):
    # Test missing files
    response = client.post('/compare', 
        data={'direction': 'pg2ora'},
        files=[]
    )
    
    assert response.status_code == 422  # FastAPI validation error
    data = response.json()
    assert 'detail' in data


def test_progress_endpoint_not_found(client):
    # Test progress endpoint with non-existent job
    response = client.get('/progress/non-existent-job-id')
    assert response.status_code == 404
    data = response.json()
    assert 'Job progress not found' in data['detail'] 