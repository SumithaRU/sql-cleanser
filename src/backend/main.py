import os, uuid, zipfile
import datetime
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from typing import List
from compare_utils import run_compare
import traceback
from fastapi.middleware.cors import CORSMiddleware
from config_loader import config
from progress_tracker import ProgressTracker, get_progress

# Configuration constants from YAML
MAX_BATCH_FILES = config.get('processing.max_batch_files', 50)
RESULTS_DIRECTORY = config.get('output.results_directory', 'results')

app = FastAPI(
    title=config.get('application.name', 'SQL Cleanser'),
    version=config.get('application.version', '2.0.0'),
    description=config.get('application.description', 'AI-Powered SQL Migration Tool')
)

# Enable CORS based on configuration
if config.get('server.cors_enabled', True):
    allowed_origins = config.get('server.allowed_origins', ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get('/progress/{job_id}')
def get_job_progress(job_id: str):
    """Get real-time progress for a comparison job"""
    progress_data = get_progress(job_id)
    if progress_data:
        return progress_data
    return JSONResponse({'detail': 'Job progress not found'}, status_code=404)

@app.post('/compare')
async def compare(
    background_tasks: BackgroundTasks,
    base_files: List[UploadFile] = File(..., alias="base_files"),
    oracle_files: List[UploadFile] = File(..., alias="oracle_files")
):
    try:
        # Validate input files
        if not base_files or not oracle_files:
            raise HTTPException(status_code=400, detail="Both base and oracle files are required")
            
        # Slice file lists to MAX_BATCH_FILES
        base_files = base_files[:MAX_BATCH_FILES]
        oracle_files = oracle_files[:MAX_BATCH_FILES]
        
        job_id = str(uuid.uuid4())
        job_dir = os.path.join(RESULTS_DIRECTORY, job_id)
        base_dir = os.path.join(job_dir, 'base')
        oracle_dir = os.path.join(job_dir, 'oracle')
        
        # Ensure directories exist
        os.makedirs(base_dir, exist_ok=True)
        os.makedirs(oracle_dir, exist_ok=True)
        
        # Save uploaded files
        try:
            for f in base_files:
                path = os.path.join(base_dir, f.filename)
                with open(path, 'wb') as out:
                    out.write(await f.read())
            for f in oracle_files:
                path = os.path.join(oracle_dir, f.filename)
                with open(path, 'wb') as out:
                    out.write(await f.read())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded files: {str(e)}")

        # Create progress tracker
        tracker = ProgressTracker(job_id)
        tracker.update(5, "📤 Files uploaded, starting analysis...")
        
        # Start background processing
        background_tasks.add_task(process_comparison, job_id, base_dir, oracle_dir, job_dir, tracker)
        
        # Return job ID immediately for progress tracking
        return JSONResponse({"job_id": job_id, "status": "started"}, status_code=202)
    
    except HTTPException:
        raise
    except Exception as e:
        tb = traceback.format_exc()
        return JSONResponse(
            {'detail': 'Unexpected error occurred', 'error': str(e), 'traceback': tb},
            status_code=500
        )

@app.get('/download/{job_id}')
def download_comparison(job_id: str):
    """Download completed comparison results"""
    job_dir = os.path.join(RESULTS_DIRECTORY, job_id)
    
    # Check if job directory exists
    if not os.path.exists(job_dir):
        return JSONResponse({'detail': 'Job not found'}, status_code=404)
    
    # Find the ZIP file
    try:
        zip_files = [f for f in os.listdir(job_dir) if f.endswith('.zip')]
        if not zip_files:
            return JSONResponse({'detail': 'Results not ready yet'}, status_code=404)
        
        zip_filename = zip_files[0]
        zip_path = os.path.join(job_dir, zip_filename)
    except Exception as e:
        return JSONResponse({'detail': 'Error accessing results'}, status_code=500)
    
    def iterfile():
        with open(zip_path, 'rb') as f:
            for chunk in iter(lambda: f.read(16384), b''):
                yield chunk

    headers = {
        'Content-Disposition': f'attachment; filename="{zip_filename}"',
        'X-Status': 'ok',
        'X-Zip-Filename': zip_filename,
        'X-Job-Id': job_id
    }
    
    return StreamingResponse(iterfile(), media_type='application/zip', headers=headers)

def process_comparison(job_id: str, base_dir: str, oracle_dir: str, job_dir: str, tracker: ProgressTracker):
    """Background task to process comparison with real progress tracking"""
    try:
        # Create progress callback
        def progress_callback(progress: int, step: str):
            tracker.update(progress, step)
        
        zip_path, zip_filename, _ = run_compare(base_dir, oracle_dir, job_dir, progress_callback)
        tracker.complete("✅ Comparison complete! Ready for download.")
        
    except RuntimeError as e:
        tracker.error("❌ LLM service error")
        print(f"LLM error in job {job_id}: {e}")
    except Exception as e:
        tracker.error("❌ Comparison failed")
        print(f"Error in job {job_id}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 