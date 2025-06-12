import json
import os
import time
from typing import Optional
from config_loader import config

class ProgressTracker:
    """Thread-safe progress tracker that saves progress to files"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.results_dir = config.get('output.results_directory', 'results')
        self.progress_file = os.path.join(self.results_dir, f"{job_id}_progress.json")
        self.progress = 0
        self.step = "Initializing..."
        self.status = "processing"
        self.start_time = time.time()
        
        # Initialize progress file
        self._save_progress()
    
    def update(self, progress: int, step: str):
        """Update progress and step"""
        self.progress = min(100, max(0, progress))
        self.step = step
        self.status = "processing" if progress < 100 else "complete"
        self._save_progress()
    
    def complete(self, message: str = "✅ Processing complete!"):
        """Mark as complete"""
        self.progress = 100
        self.step = message
        self.status = "complete"
        self._save_progress()
    
    def error(self, message: str = "❌ Processing failed"):
        """Mark as error"""
        self.step = message
        self.status = "error"
        self._save_progress()
    
    def _save_progress(self):
        """Save current progress to file"""
        try:
            os.makedirs(os.path.dirname(self.progress_file), exist_ok=True)
            
            progress_data = {
                "job_id": self.job_id,
                "progress": self.progress,
                "step": self.step,
                "status": self.status,
                "timestamp": time.time(),
                "elapsed_time": time.time() - self.start_time
            }
            
            with open(self.progress_file, 'w') as f:
                json.dump(progress_data, f)
        except Exception as e:
            print(f"Failed to save progress: {e}")
    
    def cleanup(self):
        """Remove progress file when done"""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
        except Exception as e:
            print(f"Failed to cleanup progress file: {e}")

def get_progress(job_id: str) -> Optional[dict]:
    """Get current progress for a job"""
    try:
        results_dir = config.get('output.results_directory', 'results')
        progress_file = os.path.join(results_dir, f"{job_id}_progress.json")
        
        if not os.path.exists(progress_file):
            return None
            
        with open(progress_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to read progress: {e}")
        return None 