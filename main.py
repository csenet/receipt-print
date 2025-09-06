import os
import uuid
import time
import random
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException, Path as FastAPIPath
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
from PIL import Image
import io


app = FastAPI(
    title="Receipt Print Client Service",
    description="Client service for uploading images to receipt printer API",
    version="1.0.0"
)

# CORS対応を追加
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_HOST = os.getenv("API_HOST", "http://printer-api:8080")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

jobs_db: Dict[str, Dict[str, Any]] = {}


def validate_image(file_content: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(file_content))
        return image.format.lower() in ['jpeg', 'jpg', 'png', 'gif']
    except Exception:
        return False


@app.post("/api/upload")
async def upload_image(image: UploadFile = File(...)):
    try:
        print(f"Received file: {image.filename}, content_type: {image.content_type}, size: {image.size}")
        
        # Content-type チェックを緩く
        if image.content_type and not image.content_type.startswith('image/'):
            print(f"Invalid content type: {image.content_type}")
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
        
        file_content = await image.read()
        print(f"File content size: {len(file_content)}")
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file received.")
        
        if not validate_image(file_content):
            raise HTTPException(status_code=400, detail="Invalid image format. Only JPG, PNG, GIF are supported.")
        
        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")
        
        job_id = str(uuid.uuid4())
        safe_filename = image.filename or f"image_{job_id}"
        filename = f"{job_id}_{safe_filename}"
        file_path = UPLOAD_DIR / filename
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        jobs_db[job_id] = {
            "filename": safe_filename,
            "file_path": str(file_path),
            "size": len(file_content),
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        print(f"Successfully uploaded: {job_id}")
        
        return {
            "success": True,
            "jobId": job_id,
            "filename": safe_filename,
            "size": len(file_content)
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@app.post("/api/print/{job_id}")
async def print_image(job_id: str = FastAPIPath(...)):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    
    try:
        with open(job["file_path"], "rb") as f:
            files = {"imgf": (job["filename"], f, "image/*")}
            
            # ランダムに /0 または /1 エンドポイントを選択
            endpoint = random.choice([0, 1])
            response = requests.post(f"{API_HOST}/{endpoint}", files=files, timeout=30)
            
            if response.status_code == 200:
                jobs_db[job_id]["status"] = "completed"
                jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "message": "Print job completed successfully",
                    "jobId": job_id
                }
            else:
                jobs_db[job_id]["status"] = "failed"
                jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
                
                raise HTTPException(
                    status_code=500, 
                    detail=f"Print service returned error: {response.status_code}"
                )
                
    except requests.exceptions.RequestException as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to connect to print service: {str(e)}"
        )
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["updated_at"] = datetime.now().isoformat()
        
        raise HTTPException(
            status_code=500, 
            detail=f"Print job failed: {str(e)}"
        )


@app.get("/api/status/{job_id}")
async def get_job_status(job_id: str = FastAPIPath(...)):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs_db[job_id]
    return {
        "jobId": job_id,
        "status": job["status"],
        "message": f"Job is {job['status']}",
        "createdAt": job["created_at"],
        "updatedAt": job["updated_at"]
    }


app.mount("/", StaticFiles(directory="static", html=True), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
