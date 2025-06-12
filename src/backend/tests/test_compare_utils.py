import sys
import os
import pytest
import tempfile
import json

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from compare_utils import compute_bidirectional_diffs, compute_diffs, generate_conversion_sql
from transform import convert_insert_statements, convert_postgres_to_oracle_datatype, convert_oracle_to_postgres_datatype


class TestBidirectionalDiffs:
    """Test bidirectional diff computation"""
    
    def test_compute_diffs_missing_pg2ora(self):
        """Test missing records in PostgreSQL to Oracle direction"""
        source_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}
        target_rows = {}
        pks = {'t1': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "pg2ora")
        
        assert diff['metadata']['direction'] == 'pg2ora'
        assert diff['metadata']['source_type'] == 'PostgreSQL'
        assert diff['metadata']['target_type'] == 'Oracle'
        assert len(diff['summary']['missing_in_oracle']) == 1
        assert diff['summary']['missing_in_oracle'][0]['row'] == source_rows['t1'][0]
        assert diff['summary']['extra_in_oracle'] == []
        assert diff['summary']['mismatches'] == []
        assert 't1' in diff['tables']
        assert len(diff['tables']['t1']['missing_in_target']) == 1

    def test_compute_diffs_missing_ora2pg(self):
        """Test missing records in Oracle to PostgreSQL direction"""
        source_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}
        target_rows = {}
        pks = {'t1': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "ora2pg")
        
        assert diff['metadata']['direction'] == 'ora2pg'
        assert diff['metadata']['source_type'] == 'Oracle'
        assert diff['metadata']['target_type'] == 'PostgreSQL'
        assert len(diff['summary']['missing_in_postgresql']) == 1
        assert diff['summary']['missing_in_postgresql'][0]['row'] == source_rows['t1'][0]
        assert diff['summary']['extra_in_postgresql'] == []
        assert diff['summary']['mismatches'] == []

    def test_compute_diffs_mismatch_pg2ora(self):
        """Test mismatched records in PostgreSQL to Oracle direction"""
        source_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}
        target_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'b']}]}
        pks = {'t1': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "pg2ora")
        
        assert diff['summary']['missing_in_oracle'] == []
        assert diff['summary']['extra_in_oracle'] == []
        assert len(diff['summary']['mismatches']) == 1
        mismatch = diff['summary']['mismatches'][0]
        assert mismatch['postgresql_values'] == [1, 'a']
        assert mismatch['oracle_values'] == [1, 'b']

    def test_compute_diffs_mismatch_ora2pg(self):
        """Test mismatched records in Oracle to PostgreSQL direction"""
        source_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}
        target_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'b']}]}
        pks = {'t1': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "ora2pg")
        
        assert diff['summary']['missing_in_postgresql'] == []
        assert diff['summary']['extra_in_postgresql'] == []
        assert len(diff['summary']['mismatches']) == 1
        mismatch = diff['summary']['mismatches'][0]
        assert mismatch['oracle_values'] == [1, 'a']
        assert mismatch['postgresql_values'] == [1, 'b']

    def test_compute_diffs_extra_records(self):
        """Test extra records detection"""
        source_rows = {}
        target_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'extra']}]}
        pks = {'t1': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "pg2ora")
        
        assert diff['summary']['missing_in_oracle'] == []
        assert len(diff['summary']['extra_in_oracle']) == 1
        assert diff['summary']['extra_in_oracle'][0]['row'] == target_rows['t1'][0]
        assert diff['summary']['mismatches'] == []

    def test_legacy_compute_diffs_compatibility(self):
        """Test backward compatibility with legacy compute_diffs function"""
        base_rows = {'t1': [{'table': 't1', 'columns': ['id', 'val'], 'values': [1, 'a']}]}
        oracle_rows = {}
        pks = {'t1': ['id']}
        
        legacy_diff = compute_diffs(base_rows, oracle_rows, pks)
        new_diff = compute_bidirectional_diffs(base_rows, oracle_rows, pks, "pg2ora")
        
        # Legacy should have same summary structure as new for pg2ora
        assert len(legacy_diff['summary']['missing_in_oracle']) == len(new_diff['summary']['missing_in_oracle'])
        assert len(legacy_diff['summary']['extra_in_oracle']) == len(new_diff['summary']['extra_in_oracle'])


class TestConversionSQL:
    """Test SQL conversion functionality"""
    
    def test_generate_conversion_sql_pg2ora(self):
        """Test conversion SQL generation for PostgreSQL to Oracle"""
        missing_rows = [
            {
                'table': 'users',
                'row': {'table': 'users', 'columns': ['id', 'name'], 'values': [1, 'john']}
            },
            {
                'table': 'orders',
                'row': {'table': 'orders', 'columns': ['id', 'user_id'], 'values': [100, 1]}
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_file = generate_conversion_sql(missing_rows, "pg2ora", temp_dir)
            
            assert sql_file == "missing_records_pg2ora.sql"
            
            # Check file content
            sql_path = os.path.join(temp_dir, sql_file)
            assert os.path.exists(sql_path)
            
            with open(sql_path, 'r') as f:
                content = f.read()
                assert "-- Direction: pg2ora" in content
                assert "INSERT INTO USERS" in content
                assert "INSERT INTO ORDERS" in content

    def test_generate_conversion_sql_ora2pg(self):
        """Test conversion SQL generation for Oracle to PostgreSQL"""
        missing_rows = [
            {
                'table': 'USERS',
                'row': {'table': 'USERS', 'columns': ['ID', 'NAME'], 'values': [1, 'JOHN']}
            }
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_file = generate_conversion_sql(missing_rows, "ora2pg", temp_dir)
            
            assert sql_file == "missing_records_ora2pg.sql"
            
            # Check file content
            sql_path = os.path.join(temp_dir, sql_file)
            with open(sql_path, 'r') as f:
                content = f.read()
                assert "-- Direction: ora2pg" in content
                assert "INSERT INTO users" in content

    def test_generate_conversion_sql_empty(self):
        """Test conversion SQL generation with no missing rows"""
        missing_rows = []
        
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_file = generate_conversion_sql(missing_rows, "pg2ora", temp_dir)
            
            assert sql_file == ""


class TestInsertConversion:
    """Test INSERT statement conversion"""
    
    def test_convert_insert_statements_pg2ora(self):
        """Test PostgreSQL to Oracle INSERT conversion"""
        rows = [
            {'table': 'users', 'columns': ['id', 'name', 'active'], 'values': [1, 'john', 'true']},
            {'table': 'orders', 'columns': ['id', 'created'], 'values': [100, 'now()']}
        ]
        
        converted = convert_insert_statements(rows, "pg2ora")
        
        assert len(converted) == 2
        assert "INSERT INTO USERS" in converted[0]
        assert "INSERT INTO ORDERS" in converted[1]
        assert "SYSDATE" in converted[1]  # now() should be converted to SYSDATE

    def test_convert_insert_statements_ora2pg(self):
        """Test Oracle to PostgreSQL INSERT conversion"""
        rows = [
            {'table': 'USERS', 'columns': ['ID', 'NAME', 'ACTIVE'], 'values': [1, 'JOHN', '1']},
            {'table': 'ORDERS', 'columns': ['ID', 'CREATED'], 'values': [100, 'SYSDATE']}
        ]
        
        converted = convert_insert_statements(rows, "ora2pg")
        
        assert len(converted) == 2
        assert "INSERT INTO users" in converted[0]
        assert "INSERT INTO orders" in converted[1]
        assert "NOW()" in converted[1]  # SYSDATE should be converted to NOW()

    def test_convert_insert_statements_invalid_direction(self):
        """Test invalid direction raises error"""
        rows = [{'table': 'test', 'columns': ['id'], 'values': [1]}]
        
        with pytest.raises(ValueError, match="Unsupported direction"):
            convert_insert_statements(rows, "invalid")


class TestDataTypeConversion:
    """Test data type conversion utilities"""
    
    def test_postgres_to_oracle_datatypes(self):
        """Test PostgreSQL to Oracle data type conversion"""
        assert convert_postgres_to_oracle_datatype("integer") == "NUMBER"
        assert convert_postgres_to_oracle_datatype("varchar(50)") == "VARCHAR2(50)"
        assert convert_postgres_to_oracle_datatype("text") == "CLOB"
        assert convert_postgres_to_oracle_datatype("boolean") == "NUMBER(1)"
        assert convert_postgres_to_oracle_datatype("timestamp") == "TIMESTAMP"
        assert convert_postgres_to_oracle_datatype("numeric(10,2)") == "NUMBER(10,2)"

    def test_oracle_to_postgres_datatypes(self):
        """Test Oracle to PostgreSQL data type conversion"""
        assert convert_oracle_to_postgres_datatype("NUMBER") == "NUMERIC"
        assert convert_oracle_to_postgres_datatype("NUMBER(1)") == "BOOLEAN"
        assert convert_oracle_to_postgres_datatype("VARCHAR2(50)") == "VARCHAR(50)"
        assert convert_oracle_to_postgres_datatype("CLOB") == "TEXT"
        assert convert_oracle_to_postgres_datatype("DATE") == "TIMESTAMP"
        assert convert_oracle_to_postgres_datatype("NUMBER(10,2)") == "NUMERIC(10,2)"
        assert convert_oracle_to_postgres_datatype("NUMBER(5,0)") == "INTEGER"

    def test_postgres_to_oracle_edge_cases(self):
        """Test edge cases in PostgreSQL to Oracle conversion"""
        assert convert_postgres_to_oracle_datatype("character varying(100)") == "VARCHAR2(100)"
        assert convert_postgres_to_oracle_datatype("double precision") == "BINARY_DOUBLE"
        assert convert_postgres_to_oracle_datatype("timestamp with time zone") == "TIMESTAMP WITH TIME ZONE"

    def test_oracle_to_postgres_edge_cases(self):
        """Test edge cases in Oracle to PostgreSQL conversion"""
        assert convert_oracle_to_postgres_datatype("NUMBER(19,0)") == "BIGINT"
        assert convert_oracle_to_postgres_datatype("NUMBER(4,0)") == "SMALLINT"
        assert convert_oracle_to_postgres_datatype("TIMESTAMP WITH TIME ZONE") == "TIMESTAMP WITH TIME ZONE"


class TestIntegration:
    """Integration tests for bidirectional functionality"""
    
    def test_full_bidirectional_workflow_pg2ora(self):
        """Test complete workflow for PostgreSQL to Oracle conversion"""
        source_rows = {'users': [
            {'table': 'users', 'columns': ['id', 'name'], 'values': [1, 'alice']},
            {'table': 'users', 'columns': ['id', 'name'], 'values': [2, 'bob']}
        ]}
        target_rows = {'users': [
            {'table': 'users', 'columns': ['id', 'name'], 'values': [1, 'alice']}
        ]}
        pks = {'users': ['id']}
        
        # Compute diff
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "pg2ora")
        
        # Verify structure
        assert diff['metadata']['direction'] == 'pg2ora'
        assert len(diff['summary']['missing_in_oracle']) == 1
        assert diff['summary']['missing_in_oracle'][0]['row']['values'] == [2, 'bob']
        
        # Generate conversion SQL
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_file = generate_conversion_sql(diff['summary']['missing_in_oracle'], "pg2ora", temp_dir)
            assert sql_file == "missing_records_pg2ora.sql"

    def test_full_bidirectional_workflow_ora2pg(self):
        """Test complete workflow for Oracle to PostgreSQL conversion"""
        source_rows = {'USERS': [
            {'table': 'USERS', 'columns': ['ID', 'NAME'], 'values': [1, 'ALICE']},
            {'table': 'USERS', 'columns': ['ID', 'NAME'], 'values': [2, 'BOB']}
        ]}
        target_rows = {'USERS': [
            {'table': 'USERS', 'columns': ['ID', 'NAME'], 'values': [1, 'ALICE']}
        ]}
        pks = {'USERS': ['ID']}
        
        # Compute diff
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "ora2pg")
        
        # Verify structure
        assert diff['metadata']['direction'] == 'ora2pg'
        assert len(diff['summary']['missing_in_postgresql']) == 1
        assert diff['summary']['missing_in_postgresql'][0]['row']['values'] == [2, 'BOB']
        
        # Generate conversion SQL
        with tempfile.TemporaryDirectory() as temp_dir:
            sql_file = generate_conversion_sql(diff['summary']['missing_in_postgresql'], "ora2pg", temp_dir)
            assert sql_file == "missing_records_ora2pg.sql"

    def test_multiple_tables_different_states(self):
        """Test handling multiple tables with different states"""
        source_rows = {
            'table1': [{'table': 'table1', 'columns': ['id'], 'values': [1]}],
            'table2': [{'table': 'table2', 'columns': ['id'], 'values': [10]}]
        }
        target_rows = {
            'table1': [{'table': 'table1', 'columns': ['id'], 'values': [1]}],
            'table3': [{'table': 'table3', 'columns': ['id'], 'values': [100]}]
        }
        pks = {'table1': ['id'], 'table2': ['id'], 'table3': ['id']}
        
        diff = compute_bidirectional_diffs(source_rows, target_rows, pks, "pg2ora")
        
        # table1: no differences
        assert len(diff['tables']['table1']['missing_in_target']) == 0
        assert len(diff['tables']['table1']['extra_in_target']) == 0
        
        # table2: missing in target (Oracle)
        assert len(diff['tables']['table2']['missing_in_target']) == 1
        
        # table3: extra in target (Oracle)
        assert len(diff['tables']['table3']['extra_in_target']) == 1


if __name__ == '__main__':
    pytest.main([__file__]) 