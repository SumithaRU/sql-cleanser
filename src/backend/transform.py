import os
import datetime
import re
from typing import Dict, List, Any


def convert_postgres_to_oracle_datatype(pg_type: str) -> str:
    """Convert PostgreSQL data type to Oracle equivalent"""
    pg_type_lower = pg_type.lower()
    
    # Common type mappings
    type_map = {
        'integer': 'NUMBER',
        'int': 'NUMBER', 
        'int4': 'NUMBER',
        'bigint': 'NUMBER(19)',
        'int8': 'NUMBER(19)',
        'smallint': 'NUMBER(5)',
        'int2': 'NUMBER(5)',
        'serial': 'NUMBER',
        'bigserial': 'NUMBER(19)',
        'real': 'BINARY_FLOAT',
        'float4': 'BINARY_FLOAT',
        'double precision': 'BINARY_DOUBLE',
        'float8': 'BINARY_DOUBLE',
        'numeric': 'NUMBER',
        'decimal': 'NUMBER',
        'money': 'NUMBER(15,2)',
        'text': 'CLOB',
        'char': 'CHAR',
        'character': 'CHAR',
        'varchar': 'VARCHAR2',
        'character varying': 'VARCHAR2',
        'boolean': 'NUMBER(1)',
        'bool': 'NUMBER(1)',
        'date': 'DATE',
        'timestamp': 'TIMESTAMP',
        'timestamp without time zone': 'TIMESTAMP',
        'timestamp with time zone': 'TIMESTAMP WITH TIME ZONE',
        'time': 'DATE',
        'time without time zone': 'DATE',
        'time with time zone': 'TIMESTAMP WITH TIME ZONE',
        'interval': 'INTERVAL DAY TO SECOND',
        'bytea': 'BLOB',
        'uuid': 'VARCHAR2(36)',
        'json': 'CLOB',
        'jsonb': 'CLOB',
        'xml': 'XMLTYPE',
        'point': 'SDO_GEOMETRY',
        'line': 'SDO_GEOMETRY',
        'lseg': 'SDO_GEOMETRY',
        'box': 'SDO_GEOMETRY',
        'path': 'SDO_GEOMETRY',
        'polygon': 'SDO_GEOMETRY',
        'circle': 'SDO_GEOMETRY'
    }
    
    # Handle VARCHAR with length
    if pg_type_lower.startswith('varchar(') or pg_type_lower.startswith('character varying('):
        length = re.search(r'\((\d+)\)', pg_type_lower)
        if length:
            return f"VARCHAR2({length.group(1)})"
        return "VARCHAR2(4000)"
    
    # Handle CHAR with length
    if pg_type_lower.startswith('char(') or pg_type_lower.startswith('character('):
        length = re.search(r'\((\d+)\)', pg_type_lower)
        if length:
            return f"CHAR({length.group(1)})"
        return "CHAR(1)"
    
    # Handle NUMERIC/DECIMAL with precision and scale
    if pg_type_lower.startswith(('numeric(', 'decimal(')):
        params = re.search(r'\(([^)]+)\)', pg_type_lower)
        if params:
            return f"NUMBER({params.group(1)})"
        return "NUMBER"
    
    return type_map.get(pg_type_lower, pg_type.upper())


def convert_oracle_to_postgres_datatype(oracle_type: str) -> str:
    """Convert Oracle data type to PostgreSQL equivalent"""
    oracle_type_lower = oracle_type.lower()
    
    # Common type mappings
    type_map = {
        'number': 'NUMERIC',
        'number(1)': 'BOOLEAN',
        'binary_float': 'REAL',
        'binary_double': 'DOUBLE PRECISION',
        'float': 'DOUBLE PRECISION',
        'char': 'CHAR',
        'varchar2': 'VARCHAR',
        'nchar': 'CHAR',
        'nvarchar2': 'VARCHAR',
        'clob': 'TEXT',
        'nclob': 'TEXT',
        'blob': 'BYTEA',
        'raw': 'BYTEA',
        'long raw': 'BYTEA',
        'date': 'TIMESTAMP',
        'timestamp': 'TIMESTAMP',
        'timestamp with time zone': 'TIMESTAMP WITH TIME ZONE',
        'timestamp with local time zone': 'TIMESTAMP WITH TIME ZONE',
        'interval year to month': 'INTERVAL',
        'interval day to second': 'INTERVAL',
        'xmltype': 'XML',
        'sdo_geometry': 'GEOMETRY',
        'rowid': 'VARCHAR(18)',
        'urowid': 'VARCHAR(4000)'
    }
    
    # Handle NUMBER with precision and scale
    if oracle_type_lower.startswith('number('):
        params = re.search(r'\(([^)]+)\)', oracle_type_lower)
        if params:
            param_parts = params.group(1).split(',')
            if len(param_parts) == 2:
                precision, scale = param_parts[0].strip(), param_parts[1].strip()
                if scale == '0':
                    # Special case for NUMBER(1) -> BOOLEAN
                    if int(precision) == 1:
                        return 'BOOLEAN'
                    elif int(precision) <= 4:
                        return 'SMALLINT'
                    elif int(precision) <= 9:
                        return 'INTEGER'
                    elif int(precision) <= 18:
                        return 'BIGINT'
                    else:
                        return 'BIGINT'
                return f"NUMERIC({params.group(1)})"
            elif len(param_parts) == 1:
                precision = int(param_parts[0].strip())
                # Special case for NUMBER(1) -> BOOLEAN
                if precision == 1:
                    return 'BOOLEAN'
                elif precision <= 4:
                    return 'SMALLINT'
                elif precision <= 9:
                    return 'INTEGER'
                elif precision <= 18:
                    return 'BIGINT'
                else:
                    return 'BIGINT'
        return "NUMERIC"
    
    # Handle VARCHAR2 with length
    if oracle_type_lower.startswith('varchar2('):
        length = re.search(r'\((\d+)\)', oracle_type_lower)
        if length:
            return f"VARCHAR({length.group(1)})"
        return "VARCHAR"
    
    # Handle CHAR with length
    if oracle_type_lower.startswith('char('):
        length = re.search(r'\((\d+)\)', oracle_type_lower)
        if length:
            return f"CHAR({length.group(1)})"
        return "CHAR(1)"
    
    return type_map.get(oracle_type_lower, oracle_type.upper())


def convert_postgres_value_to_oracle(value: str, column_type: str = "") -> str:
    """Convert PostgreSQL value to Oracle equivalent"""
    if not value or str(value).lower() in ('null', 'none', ''):
        return 'NULL'
    
    value_str = str(value)
    value_lower = value_str.lower()
    
    # Boolean conversions
    if value_lower in ('true', 't', 'yes', 'y', '1') and column_type.lower() in ('boolean', 'bool'):
        return '1'
    elif value_lower in ('false', 'f', 'no', 'n', '0') and column_type.lower() in ('boolean', 'bool'):
        return '0'
    
    # Timestamp conversions
    if value_lower in ('now()', 'current_timestamp', 'current_date'):
        return 'SYSDATE'
    elif value_lower == 'current_time':
        return 'SYSTIMESTAMP'
    
    # Handle sequences/serials
    if 'nextval(' in value_lower:
        # Convert PostgreSQL nextval('seq_name') to Oracle SEQ_NAME.NEXTVAL
        seq_match = re.search(r"nextval\(['\"]?([^'\"]+)['\"]?\)", value_str, re.IGNORECASE)
        if seq_match:
            seq_name = seq_match.group(1).upper()
            return f"{seq_name}.NEXTVAL"
    
    # Handle numeric values (no quotes needed)
    try:
        # Try to parse as number (handles integers, floats, negative numbers)
        float(value_str)
        return value_str
    except ValueError:
        pass
    
    # Handle NULL values
    if value_lower == 'null':
        return 'NULL'
    
    # Handle string values - properly quote and escape
    if not (value_str.startswith("'") and value_str.endswith("'")):
        # Need to quote the value and escape single quotes
        escaped_value = value_str.replace("'", "''")
        return f"'{escaped_value}'"
    else:
        # Already quoted, but ensure proper escaping
        inner_value = value_str[1:-1]  # Remove outer quotes
        escaped_value = inner_value.replace("'", "''")
        return f"'{escaped_value}'"


def convert_oracle_value_to_postgres(value: str, column_type: str = "") -> str:
    """Convert Oracle value to PostgreSQL equivalent"""
    if not value or str(value).lower() in ('null', 'none', ''):
        return 'NULL'
    
    value_str = str(value)
    value_lower = value_str.lower()
    
    # Boolean conversions
    if value_str in ('1',) and column_type.lower() in ('number(1)', 'boolean'):
        return 'TRUE'
    elif value_str in ('0',) and column_type.lower() in ('number(1)', 'boolean'):
        return 'FALSE'
    
    # Timestamp conversions
    if value_lower in ('sysdate', 'systimestamp'):
        return 'NOW()'
    elif value_lower == 'current_date':
        return 'CURRENT_DATE'
    elif value_lower == 'current_timestamp':
        return 'CURRENT_TIMESTAMP'
    
    # Handle sequences
    if '.nextval' in value_lower:
        # Convert Oracle SEQ_NAME.NEXTVAL to PostgreSQL nextval('seq_name')
        seq_match = re.search(r"([^.]+)\.nextval", value_str, re.IGNORECASE)
        if seq_match:
            seq_name = seq_match.group(1).lower()
            return f"nextval('{seq_name}_seq')"
    
    # Handle numeric values (no quotes needed)
    try:
        # Try to parse as number (handles integers, floats, negative numbers)
        float(value_str)
        return value_str
    except ValueError:
        pass
    
    # Handle NULL values
    if value_lower == 'null':
        return 'NULL'
    
    # Handle string values - properly quote and escape
    if not (value_str.startswith("'") and value_str.endswith("'")):
        # Need to quote the value and escape single quotes
        escaped_value = value_str.replace("'", "''")
        return f"'{escaped_value}'"
    else:
        # Already quoted, but ensure proper escaping
        inner_value = value_str[1:-1]  # Remove outer quotes
        escaped_value = inner_value.replace("'", "''")
        return f"'{escaped_value}'"


def convert_insert_statement_pg_to_oracle(row: Dict[str, Any]) -> str:
    """Convert a PostgreSQL INSERT statement to Oracle format"""
    table = row['table'].upper()
    columns = [col.upper() for col in row['columns']]
    
    # Convert values
    converted_values = []
    for i, (col, val) in enumerate(zip(row['columns'], row['values'])):
        col_type = ""  # We don't have type info in row, but could be enhanced
        
        # Clean up malformed expressions
        if val and str(val).startswith('(') and not str(val).endswith(')'):
            # Fix incomplete expressions like "(Biller ID(" -> "'Biller ID'"
            clean_val = str(val).strip('(').strip()
            if clean_val:
                converted_val = convert_postgres_value_to_oracle(clean_val, col_type)
            else:
                converted_val = 'NULL'
        elif val and str(val).endswith('()') and not str(val).startswith('('):
            # Fix expressions like "Market Segment()" -> "'Market Segment'"
            clean_val = str(val).replace('()', '').strip()
            if clean_val:
                converted_val = convert_postgres_value_to_oracle(clean_val, col_type)
            else:
                converted_val = 'NULL'
        else:
            converted_val = convert_postgres_value_to_oracle(str(val), col_type)
        
        # Handle sequence generation for ID columns only if val is None/NULL
        if col.upper().endswith('_ID') and (val is None or str(val).lower() in ('null', 'none')):
            seq_name = f"{table}_SEQ"
            converted_val = f"{seq_name}.NEXTVAL"
        
        converted_values.append(converted_val)
    
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(converted_values)});"


def convert_insert_statement_oracle_to_pg(row: Dict[str, Any]) -> str:
    """Convert an Oracle INSERT statement to PostgreSQL format"""
    table = row['table'].lower()
    columns = [col.lower() for col in row['columns']]
    
    # Convert values
    converted_values = []
    for i, (col, val) in enumerate(zip(row['columns'], row['values'])):
        col_type = ""  # We don't have type info in row, but could be enhanced
        
        # Clean up malformed expressions
        if val and str(val).startswith('(') and not str(val).endswith(')'):
            # Fix incomplete expressions like "(Biller ID(" -> "'Biller ID'"
            clean_val = str(val).strip('(').strip()
            if clean_val:
                converted_val = convert_oracle_value_to_postgres(clean_val, col_type)
            else:
                converted_val = 'NULL'
        elif val and str(val).endswith('()') and not str(val).startswith('('):
            # Fix expressions like "Market Segment()" -> "'Market Segment'"
            clean_val = str(val).replace('()', '').strip()
            if clean_val:
                converted_val = convert_oracle_value_to_postgres(clean_val, col_type)
            else:
                converted_val = 'NULL'
        else:
            converted_val = convert_oracle_value_to_postgres(str(val), col_type)
        
        # Handle sequence generation for ID columns only if val is None/NULL
        if col.lower().endswith('_id') and (val is None or str(val).lower() in ('null', 'none')):
            seq_name = table + '_id_seq'
            converted_val = f"nextval('{seq_name}')"
        elif '.nextval' in str(val).lower():
            seq_name = table + '_id_seq'
            converted_val = f"nextval('{seq_name}')"
        
        converted_values.append(converted_val)
    
    return f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(converted_values)});"


def convert_insert_statements(rows: List[Dict[str, Any]], direction: str) -> List[str]:
    """
    Convert INSERT statements between PostgreSQL and Oracle formats.
    
    Args:
        rows: List of row dictionaries with table, columns, and values
        direction: 'pg2ora' for PostgreSQL→Oracle, 'ora2pg' for Oracle→PostgreSQL
    
    Returns:
        List of converted INSERT statements
    """
    converted_statements = []
    
    for row in rows:
        if direction == "pg2ora":
            converted_stmt = convert_insert_statement_pg_to_oracle(row)
        elif direction == "ora2pg":
            converted_stmt = convert_insert_statement_oracle_to_pg(row)
        else:
            raise ValueError(f"Unsupported direction: {direction}. Use 'pg2ora' or 'ora2pg'")
        
        converted_statements.append(converted_stmt)
    
    return converted_statements


def generate_schema_conversion_ddl(tables_metadata: Dict[str, Dict], direction: str) -> List[str]:
    """
    Generate DDL statements for schema conversion between PostgreSQL and Oracle.
    
    Args:
        tables_metadata: Dictionary containing table schema information
        direction: 'pg2ora' for PostgreSQL→Oracle, 'ora2pg' for Oracle→PostgreSQL
    
    Returns:
        List of DDL statements
    """
    ddl_statements = []
    
    for table_name, metadata in tables_metadata.items():
        if direction == "pg2ora":
            # PostgreSQL to Oracle DDL conversion
            table_name_upper = table_name.upper()
            ddl_statements.append(f"-- Table: {table_name_upper}")
            
            # Create sequence for auto-incrementing columns
            seq_name = f"{table_name_upper}_SEQ"
            ddl_statements.append(f"CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1;")
            ddl_statements.append("")
            
        elif direction == "ora2pg":
            # Oracle to PostgreSQL DDL conversion
            table_name_lower = table_name.lower()
            ddl_statements.append(f"-- Table: {table_name_lower}")
            
            # Create sequence for auto-incrementing columns
            seq_name = f"{table_name_lower}_id_seq"
            ddl_statements.append(f"CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1;")
            ddl_statements.append("")
    
    return ddl_statements


def transform_and_write(rows_by_table: Dict[str, List[Dict]], order: List[str], output_dir: str, direction: str = "pg2ora"):
    """
    Transform and write SQL files for bidirectional conversion.
    
    Args:
        rows_by_table: Dictionary of table rows
        order: List of table names in processing order
        output_dir: Output directory for generated files
        direction: Conversion direction ('pg2ora' or 'ora2pg')
    """
    os.makedirs(output_dir, exist_ok=True)
    
    source_type = "PostgreSQL" if direction == "pg2ora" else "Oracle"
    target_type = "Oracle" if direction == "pg2ora" else "PostgreSQL"
    
    for table in order:
        if table not in rows_by_table:
            continue
            
        rows = rows_by_table[table]
        
        # Determine file naming convention based on direction
        if direction == "pg2ora":
            filename = f"{table.upper()}.sql"
            table_display = table.upper()
        else:
            filename = f"{table.lower()}.sql"
            table_display = table.lower()
        
        lines: List[str] = [
            f"-- {target_type} SQL for table: {table_display}",
            f"-- Generated by SQL Cleanser on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Source: {source_type} INSERT statements",
            f"-- Direction: {direction.upper()}",
            "",
        ]
        
        # Add sequence creation for auto-incrementing columns
        if direction == "pg2ora":
            seq_name = f"{table.upper()}_SEQ"
            lines.extend([
                f"-- Create sequence for auto-incrementing primary key",
                f"CREATE SEQUENCE {seq_name} START WITH 1;",
                "",
            ])
        elif direction == "ora2pg":
            seq_name = f"{table.lower()}_id_seq"
            lines.extend([
                f"-- Create sequence for auto-incrementing primary key",
                f"CREATE SEQUENCE {seq_name} START WITH 1;",
                "",
            ])
        
        lines.append(f"-- Insert statements (converted from {source_type} syntax)")
        
        # Convert each row
        converted_statements = convert_insert_statements(rows, direction)
        lines.extend(converted_statements)
        
        lines.extend([
            "",
            "-- End of file",
            f"-- Total records inserted: {len(rows)}"
        ])
        
        # Write file
        output_path = os.path.join(output_dir, filename)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))


# Legacy function for backward compatibility
def transform_and_write_oracle(rows_by_table: Dict[str, List[Dict]], order: List[str], output_dir: str):
    """Legacy function for backward compatibility (PostgreSQL→Oracle only)"""
    transform_and_write(rows_by_table, order, output_dir, "pg2ora") 