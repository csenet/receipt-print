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
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    print("HEIC/HEIF support enabled")
except ImportError:
    print("HEIC/HEIF support not available - pillow_heif not installed")


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
        # まずPILで開いてみる
        image = Image.open(io.BytesIO(file_content))
        supported_formats = ['jpeg', 'jpg', 'png', 'gif', 'webp', 'heic', 'heif']
        format_name = image.format.lower() if image.format else ''
        print(f"PIL detected format: {format_name}")
        return format_name in supported_formats
    except Exception as e:
        print(f"PIL validation error: {str(e)}")
        
        # HEICファイルの場合、magicバイトで判定
        magic_bytes = file_content[:32] if len(file_content) >= 32 else file_content
        print(f"File magic bytes: {magic_bytes[:16].hex()}")
        
        # HEIC/HEIF のマジックバイトパターン
        heic_patterns = [
            b'ftypheic',  # HEIC
            b'ftypheif',  # HEIF  
            b'ftypmif1',  # HEIF variant
            b'ftypmsf1',  # HEIF variant
        ]
        
        for pattern in heic_patterns:
            if pattern in magic_bytes:
                print(f"Detected HEIC/HEIF format by magic bytes: {pattern}")
                return True
        
        # 通常の画像形式のマジックバイト
        if file_content.startswith(b'\xFF\xD8\xFF'):  # JPEG
            print("Detected JPEG by magic bytes")
            return True
        elif file_content.startswith(b'\x89PNG'):  # PNG
            print("Detected PNG by magic bytes")
            return True
        elif file_content.startswith(b'GIF8'):  # GIF
            print("Detected GIF by magic bytes")
            return True
        elif file_content.startswith(b'RIFF') and b'WEBP' in file_content[:12]:  # WEBP
            print("Detected WEBP by magic bytes")
            return True
            
        print("Unknown file format")
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
            raise HTTPException(status_code=400, detail="Invalid image format. Only JPG, PNG, GIF, HEIC, HEIF are supported.")
        
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
