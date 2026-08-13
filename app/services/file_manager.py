import os
import shutil
from pathlib import Path

def create_job_dir(job_id: str) -> Path:
    job_dir = Path(f"temp/{job_id}")
    job_dir.mkdir(parents=True, exist_ok=True)
    return job_dir

def cleanup_job_dir(job_id: str):
    job_dir = Path(f"temp/{job_id}")
    if job_dir.exists():
        shutil.rmtree(job_dir, ignore_errors=True)
      
