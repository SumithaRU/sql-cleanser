import os, uuid, zipfile
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from ingest import parse_all
from fuzz import detect_duplicates_and_order, reorder_tables
from transform import transform_and_write
from ollama_utils import infer_primary_keys, explain_anomalies

app = FastAPI()
jobs_status = {}

@app.post('/upload')
async def upload(files: list[UploadFile] = File(...), background_tasks: BackgroundTasks):
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
        return FileResponse(zip_path, media_type='application/zip', filename='cleaned_sql.zip')
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
    transform_and_write(rows_by_table, order, output_dir)

    jobs_status[job_id].update({'status': 'reporting', 'progress': 90})
    report_path = os.path.join(output_dir, 'report.md')
    with open(report_path, 'w') as f:
        f.write('# SQL Cleanser Report\n\n')
        for table, rows in rows_by_table.items():
            f.write(f'## {table}\n')
            f.write(f'- Total Rows: {len(rows)}\n')
            dups = anomalies[table]['duplicates']
            orders = anomalies[table]['order_issues']
            f.write(f'- Duplicates: {len(dups)}\n')
            f.write(f'- Order Issues: {len(orders)}\n\n')
            md = remediation.get(table, {}).get('markdown', '')
            f.write(md + '\n\n')

    zip_path = os.path.join(job_dir, 'output.zip')
    with zipfile.ZipFile(zip_path, 'w') as z:
        for root, _, files in os.walk(output_dir):
            for file in files:
                z.write(os.path.join(root, file), arcname=file)
    jobs_status[job_id].update({'status': 'complete', 'progress': 100}) 