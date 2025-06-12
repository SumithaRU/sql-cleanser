import os, uuid, zipfile
import datetime
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from ingest import parse_all
from fuzz import detect_duplicates_and_order, reorder_tables
from transform import transform_and_write
from ollama_utils import infer_primary_keys, explain_anomalies

app = FastAPI()
jobs_status = {}

@app.post('/upload')
async def upload(background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join('jobs', job_id)
    input_dir = os.path.join(job_dir, 'input')
    os.makedirs(input_dir, exist_ok=True)
    for f in files:
        path = os.path.join(input_dir, f.filename)
        with open(path, 'wb') as out:
            out.write(await f.read())
    jobs_status[job_id] = {'status': 'queued', 'progress': 0}
    background_tasks.add_task(process_job, job_id)
    return {'job_id': job_id}

@app.get('/status/{job_id}')
def status(job_id: str):
    if job_id in jobs_status:
        return jobs_status[job_id]
    return JSONResponse({'detail': 'Job not found'}, status_code=404)

@app.get('/download/{job_id}')
def download(job_id: str):
    job_dir = os.path.join('jobs', job_id)
    zip_path = os.path.join(job_dir, 'output.zip')
    if os.path.exists(zip_path):
        return FileResponse(zip_path, media_type='application/zip', filename='SQL Cleanser - Results.zip')
    return JSONResponse({'detail': 'Output not ready'}, status_code=404)

def process_job(job_id: str):
    job_dir = os.path.join('jobs', job_id)
    input_dir = os.path.join(job_dir, 'input')
    output_dir = os.path.join(job_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    jobs_status[job_id] = {'status': 'parsing', 'progress': 10}
    rows_by_table = parse_all(input_dir)

    jobs_status[job_id].update({'status': 'inferring_keys', 'progress': 30})
    primary_keys = {}
    for table, rows in rows_by_table.items():
        sample = rows[:10]
        cols = rows[0]['columns'] if rows else []
        primary_keys[table] = infer_primary_keys(sample, cols)

    jobs_status[job_id].update({'status': 'detecting_anomalies', 'progress': 50})
    anomalies = {}
    for table, rows in rows_by_table.items():
        dups, orders = detect_duplicates_and_order(rows, primary_keys.get(table, []))
        anomalies[table] = {'duplicates': dups, 'order_issues': orders}

    jobs_status[job_id].update({'status': 'explaining_anomalies', 'progress': 60})
    remediation = {}
    for table, anoms in anomalies.items():
        remediation[table] = explain_anomalies(anoms)

    jobs_status[job_id].update({'status': 'transforming', 'progress': 70})
    order = reorder_tables(rows_by_table)
    
    # Create organized folder structure
    oracle_sql_dir = os.path.join(output_dir, 'oracle_sql')
    reports_dir = os.path.join(output_dir, 'reports')
    metadata_dir = os.path.join(output_dir, 'metadata')
    os.makedirs(oracle_sql_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)
    
    # Transform and write Oracle SQL files
    transform_and_write(rows_by_table, order, oracle_sql_dir)

    jobs_status[job_id].update({'status': 'reporting', 'progress': 90})
    
    # Generate main analysis report with LLM insights
    report_path = os.path.join(reports_dir, 'analysis_report.md')
    with open(report_path, 'w') as f:
        f.write('# SQL Cleanser - AI-Powered Analysis Report\n\n')
        f.write(f'**Processing Summary:**\n')
        f.write(f'- Total Tables Processed: {len(rows_by_table)}\n')
        f.write(f'- Total Records: {sum(len(rows) for rows in rows_by_table.values())}\n')
        f.write(f'- Table Execution Order: {" → ".join(order)}\n\n')
        
        for table, rows in rows_by_table.items():
            f.write(f'## Table: {table.upper()}\n')
            f.write(f'- Total Rows: {len(rows)}\n')
            f.write(f'- Primary Key(s): {", ".join(primary_keys.get(table, ["Unknown"]))}\n')
            dups = anomalies[table]['duplicates']
            orders = anomalies[table]['order_issues']
            f.write(f'- Duplicates: {len(dups)}\n')
            f.write(f'- Order Issues: {len(orders)}\n\n')
            f.write(f'**AI Analysis:**\n')
            md = remediation.get(table, {}).get('markdown', '')
            f.write(md + '\n\n')
    
    # Generate table summary
    summary_path = os.path.join(reports_dir, 'table_summary.md')
    with open(summary_path, 'w') as f:
        f.write('# Table Summary\n\n')
        f.write('| Table | Rows | Duplicates | Primary Key | Source Files |\n')
        f.write('|-------|------|------------|-------------|-------------|\n')
        for table in order:
            rows = rows_by_table[table]
            dups = len(anomalies[table]['duplicates'])
            pk = ', '.join(primary_keys.get(table, ['Unknown']))
            sources = list(set(row['source_file'] for row in rows))
            source_names = [os.path.basename(s) for s in sources]
            f.write(f'| {table.upper()} | {len(rows)} | {dups} | {pk} | {", ".join(source_names)} |\n')
    
    # Generate transformation log with AI insights
    transform_log_path = os.path.join(metadata_dir, 'transformation_log.txt')
    with open(transform_log_path, 'w') as f:
        f.write('SQL Cleanser - AI-Enhanced Transformation Log\n')
        f.write('=' * 50 + '\n\n')
        f.write(f'Processing Date: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Job ID: {job_id}\n')
        f.write(f'Tables Processed: {len(rows_by_table)}\n')
        f.write(f'Execution Order: {" → ".join(order)}\n\n')
        
        f.write('AI-Detected Primary Keys:\n')
        for table, pk in primary_keys.items():
            f.write(f'  {table}: {pk}\n')
        
        f.write('\nAI Analysis Summary:\n')
        for table, remedy in remediation.items():
            plan = remedy.get('plan', 'No analysis available')
            f.write(f'  {table}: {plan}\n')
        
        f.write('\nTransformation Rules Applied:\n')
        f.write('  - PostgreSQL → Oracle syntax conversion\n')
        f.write('  - NOW()/CURRENT_TIMESTAMP → SYSDATE\n')
        f.write('  - NULL IDs → SEQUENCE.NEXTVAL\n')
        f.write('  - Column/table names → UPPERCASE\n')
        f.write('  - Added CREATE SEQUENCE statements\n')
    
    # Create README for the output
    readme_path = os.path.join(output_dir, 'README.md')
    with open(readme_path, 'w') as f:
        f.write('# SQL Cleanser Output - AI-Enhanced Results\n\n')
        f.write('This package contains PostgreSQL-to-Oracle transformed SQL with AI-powered analysis.\n\n')
        f.write('## 🔬 AI Features Used:\n')
        f.write('- **Smart Primary Key Detection**: LLM analyzed data patterns\n')
        f.write('- **Intelligent Anomaly Analysis**: AI-generated remediation plans\n')
        f.write('- **Quality Assessment**: Data integrity recommendations\n\n')
        f.write('## 📁 Folder Structure:\n\n')
        f.write('```\n')
        f.write('📁 oracle_sql/          # Oracle-compatible SQL files\n')
        f.write('   ├── TABLE1.sql       # Individual table scripts with sequences\n')
        f.write('   └── TABLE2.sql       # Proper Oracle syntax and formatting\n')
        f.write('📁 reports/             # AI-powered analysis reports\n')
        f.write('   ├── analysis_report.md  # Detailed AI insights and recommendations\n')
        f.write('   └── table_summary.md    # Quick reference with AI-detected keys\n')
        f.write('📁 metadata/            # Processing and transformation details\n')
        f.write('   └── transformation_log.txt  # Complete processing log\n')
        f.write('📄 README.md            # This file\n')
        f.write('```\n\n')
        f.write('## 🚀 Usage:\n\n')
        f.write('1. **Execute Oracle SQL**: Run scripts in `oracle_sql/` in order shown in analysis report\n')
        f.write('2. **Review AI Analysis**: Check `reports/analysis_report.md` for intelligent insights\n')
        f.write('3. **Quick Reference**: Use `reports/table_summary.md` for overview\n')
        f.write('4. **Technical Details**: Review `metadata/transformation_log.txt` for processing info\n')

    zip_path = os.path.join(job_dir, 'output.zip')
    with zipfile.ZipFile(zip_path, 'w') as z:
        for root, _, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Create relative path with parent folder structure
                relative_path = os.path.relpath(file_path, output_dir)
                # Add parent folder for clean extraction
                archive_path = os.path.join('sql-cleanser', relative_path)
                z.write(file_path, arcname=archive_path)
    jobs_status[job_id].update({'status': 'complete', 'progress': 100}) 