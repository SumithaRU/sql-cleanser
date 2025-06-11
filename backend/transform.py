import os
from typing import Dict, List

def transform_and_write(rows_by_table: Dict[str, List[Dict]], order: List[str], output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    for table in order:
        seq_name = f"{table.upper()}_SEQ"
        lines: List[str] = [f"CREATE SEQUENCE {seq_name} START WITH 1;"]
        for row in rows_by_table[table]:
            cols = [c.upper() for c in row['columns']]
            vals: List[str] = []
            for c, v in zip(row['columns'], row['values']):
                if c.upper().endswith('_ID') and (not v or v.lower() == 'null'):
                    vals.append(f"{seq_name}.NEXTVAL")
                else:
                    vv = v.upper().replace('"', '')
                    if vv.lower() in ('now()', 'current_timestamp'):
                        vals.append('SYSDATE')
                    else:
                        vals.append(f"'{vv}'")
            lines.append(f"INSERT INTO {table.upper()} ({', '.join(cols)}) VALUES ({', '.join(vals)});")
        with open(os.path.join(output_dir, f"{table.upper()}.sql"), 'w') as f:
            f.write("\n".join(lines)) 