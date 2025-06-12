import sys
import os
import pytest

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compare_utils import compute_diffs


def test_compute_diffs_missing():
    base_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}  # one row in base
    oracle_rows = {}
    pks = {'t1': ['id']}
    diff = compute_diffs(base_rows, oracle_rows, pks)
    assert len(diff['summary']['missing_in_oracle']) == 1
    assert diff['summary']['missing_in_oracle'][0]['row'] == base_rows['t1'][0]
    assert diff['summary']['extra_in_oracle'] == []
    assert diff['summary']['mismatches'] == []
    assert 't1' in diff['tables']
    assert len(diff['tables']['t1']['missing']) == 1


def test_compute_diffs_mismatch():
    base_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}  # base has 'a'
    oracle_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'b']}]}  # oracle has 'b'
    pks = {'t1': ['id']}
    diff = compute_diffs(base_rows, oracle_rows, pks)
    # no missing or extra, only mismatch
    assert diff['summary']['missing_in_oracle'] == []
    assert diff['summary']['extra_in_oracle'] == []
    assert len(diff['summary']['mismatches']) == 1
    mismatch = diff['summary']['mismatches'][0]
    assert mismatch['base_values'] == [1, 'a']
    assert mismatch['oracle_values'] == [1, 'b']
    assert 't1' in diff['tables']
    assert len(diff['tables']['t1']['mismatches']) == 1 