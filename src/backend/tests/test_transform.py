import sys
import os
import pytest
import tempfile

# Add backend directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transform import (
    convert_postgres_to_oracle_datatype,
    convert_oracle_to_postgres_datatype,
    convert_postgres_value_to_oracle,
    convert_oracle_value_to_postgres,
    convert_insert_statement_pg_to_oracle,
    convert_insert_statement_oracle_to_pg,
    convert_insert_statements,
    generate_schema_conversion_ddl,
    transform_and_write,
    transform_and_write_oracle
)


class TestDataTypeConversions:
    """Test data type conversions"""
    
    def test_postgres_to_oracle_basic_types(self):
        """Test basic PostgreSQL to Oracle type conversions"""
        assert convert_postgres_to_oracle_datatype("integer") == "NUMBER"
        assert convert_postgres_to_oracle_datatype("varchar(50)") == "VARCHAR2(50)"
        assert convert_postgres_to_oracle_datatype("boolean") == "NUMBER(1)"
        assert convert_postgres_to_oracle_datatype("text") == "CLOB"
    
    def test_oracle_to_postgres_basic_types(self):
        """Test basic Oracle to PostgreSQL type conversions"""
        assert convert_oracle_to_postgres_datatype("NUMBER") == "NUMERIC"
        assert convert_oracle_to_postgres_datatype("VARCHAR2(50)") == "VARCHAR(50)"
        assert convert_oracle_to_postgres_datatype("NUMBER(1)") == "BOOLEAN"
        assert convert_oracle_to_postgres_datatype("CLOB") == "TEXT"


class TestValueConversions:
    """Test value conversions"""
    
    def test_postgres_to_oracle_values(self):
        """Test PostgreSQL to Oracle value conversions"""
        assert convert_postgres_value_to_oracle("true", "boolean") == "1"
        assert convert_postgres_value_to_oracle("false", "boolean") == "0"
        assert convert_postgres_value_to_oracle("now()") == "SYSDATE"
        assert convert_postgres_value_to_oracle("NULL") == "NULL"
    
    def test_oracle_to_postgres_values(self):
        """Test Oracle to PostgreSQL value conversions"""
        assert convert_oracle_value_to_postgres("1", "number(1)") == "TRUE"
        assert convert_oracle_value_to_postgres("0", "number(1)") == "FALSE"
        assert convert_oracle_value_to_postgres("SYSDATE") == "NOW()"
        assert convert_oracle_value_to_postgres("NULL") == "NULL"


class TestInsertConversions:
    """Test INSERT statement conversions"""
    
    def test_postgres_to_oracle_insert(self):
        """Test PostgreSQL to Oracle INSERT conversion"""
        row = {
            'table': 'users',
            'columns': ['id', 'name'],
            'values': [1, 'test']
        }
        result = convert_insert_statement_pg_to_oracle(row)
        assert "INSERT INTO USERS" in result
        assert result.endswith(";")
    
    def test_oracle_to_postgres_insert(self):
        """Test Oracle to PostgreSQL INSERT conversion"""
        row = {
            'table': 'USERS',
            'columns': ['ID', 'NAME'],
            'values': [1, 'TEST']
        }
        result = convert_insert_statement_oracle_to_pg(row)
        assert "INSERT INTO users" in result
        assert result.endswith(";")
    
    def test_convert_insert_statements_pg2ora(self):
        """Test converting multiple statements pg2ora"""
        rows = [
            {'table': 'users', 'columns': ['id'], 'values': [1]},
            {'table': 'orders', 'columns': ['id'], 'values': [100]}
        ]
        results = convert_insert_statements(rows, "pg2ora")
        assert len(results) == 2
        assert "INSERT INTO USERS" in results[0]
        assert "INSERT INTO ORDERS" in results[1]
    
    def test_convert_insert_statements_ora2pg(self):
        """Test converting multiple statements ora2pg"""
        rows = [
            {'table': 'USERS', 'columns': ['ID'], 'values': [1]},
            {'table': 'ORDERS', 'columns': ['ID'], 'values': [100]}
        ]
        results = convert_insert_statements(rows, "ora2pg")
        assert len(results) == 2
        assert "INSERT INTO users" in results[0]
        assert "INSERT INTO orders" in results[1]
    
    def test_convert_insert_statements_invalid_direction(self):
        """Test invalid direction raises error"""
        rows = [{'table': 'test', 'columns': ['id'], 'values': [1]}]
        with pytest.raises(ValueError):
            convert_insert_statements(rows, "invalid")


class TestSchemaConversion:
    """Test schema conversion DDL"""
    
    def test_generate_schema_ddl_pg2ora(self):
        """Test PostgreSQL to Oracle DDL generation"""
        metadata = {'users': {}, 'orders': {}}
        ddl = generate_schema_conversion_ddl(metadata, "pg2ora")
        assert len(ddl) > 0
        ddl_text = ' '.join(ddl)
        assert "USERS_SEQ" in ddl_text
        assert "CREATE SEQUENCE" in ddl_text
    
    def test_generate_schema_ddl_ora2pg(self):
        """Test Oracle to PostgreSQL DDL generation"""
        metadata = {'USERS': {}, 'ORDERS': {}}
        ddl = generate_schema_conversion_ddl(metadata, "ora2pg")
        assert len(ddl) > 0
        ddl_text = ' '.join(ddl)
        assert "users_id_seq" in ddl_text
        assert "CREATE SEQUENCE" in ddl_text


class TestTransformAndWrite:
    """Test file transformation and writing"""
    
    def test_transform_and_write_pg2ora(self):
        """Test transform and write for pg2ora"""
        rows_by_table = {
            'users': [
                {'table': 'users', 'columns': ['id', 'name'], 'values': [1, 'test']}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            transform_and_write(rows_by_table, ['users'], temp_dir, "pg2ora")
            
            file_path = os.path.join(temp_dir, "USERS.sql")
            assert os.path.exists(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
                assert "-- Oracle SQL for table: USERS" in content
                assert "CREATE SEQUENCE USERS_SEQ" in content
                assert "INSERT INTO USERS" in content
    
    def test_transform_and_write_ora2pg(self):
        """Test transform and write for ora2pg"""
        rows_by_table = {
            'USERS': [
                {'table': 'USERS', 'columns': ['ID', 'NAME'], 'values': [1, 'TEST']}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            transform_and_write(rows_by_table, ['USERS'], temp_dir, "ora2pg")
            
            file_path = os.path.join(temp_dir, "users.sql")
            assert os.path.exists(file_path)
            
            with open(file_path, 'r') as f:
                content = f.read()
                assert "-- PostgreSQL SQL for table: users" in content
                assert "CREATE SEQUENCE users_id_seq" in content
                assert "INSERT INTO users" in content
    
    def test_transform_and_write_default_direction(self):
        """Test default direction (pg2ora)"""
        rows_by_table = {
            'users': [
                {'table': 'users', 'columns': ['id'], 'values': [1]}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            transform_and_write(rows_by_table, ['users'], temp_dir)
            
            file_path = os.path.join(temp_dir, "USERS.sql")
            assert os.path.exists(file_path)
    
    def test_transform_and_write_oracle_legacy(self):
        """Test legacy Oracle function"""
        rows_by_table = {
            'users': [
                {'table': 'users', 'columns': ['id'], 'values': [1]}
            ]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            transform_and_write_oracle(rows_by_table, ['users'], temp_dir)
            
            file_path = os.path.join(temp_dir, "USERS.sql")
            assert os.path.exists(file_path)
    
    def test_transform_missing_table(self):
        """Test handling missing tables"""
        rows_by_table = {
            'users': [{'table': 'users', 'columns': ['id'], 'values': [1]}]
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Include missing table in order
            transform_and_write(rows_by_table, ['users', 'missing'], temp_dir, "pg2ora")
            
            # Only existing table should have file
            assert os.path.exists(os.path.join(temp_dir, "USERS.sql"))
            assert not os.path.exists(os.path.join(temp_dir, "MISSING.sql"))


if __name__ == '__main__':
    pytest.main([__file__]) 