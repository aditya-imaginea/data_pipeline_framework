import os
import shutil
import uuid
import json
import subprocess

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for development/testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
STATE_LOG_DIR = "state_logs"

@app.post("/submit_pipeline")
async def submit_pipeline(
    pipeline_file: UploadFile = File(...),
    dataset_file: UploadFile = File(...)
):
    try:
        request_id = str(uuid.uuid4())
        request_dir = os.path.join(UPLOAD_DIR, request_id)
        os.makedirs(request_dir, exist_ok=True)

        pipeline_path = os.path.join(request_dir, "pipeline_definition.json")
        dataset_path = os.path.join(request_dir, "dataset.json")

        # Save uploaded files
        with open(pipeline_path, "wb") as f:
            f.write(await pipeline_file.read())
        with open(dataset_path, "wb") as f:
            f.write(await dataset_file.read())

        # Run the pipeline via Docker and batch_runner.py
        subprocess.Popen([
            "python", "batch_runner.py", request_id
        ])

        return {"request_id": request_id, "status": "processing_started"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit pipeline: {str(e)}")


@app.get("/get_result/{request_id}")
def get_result(request_id: str):
    log_dir = os.path.join(STATE_LOG_DIR, request_id)
    if not os.path.exists(log_dir):
        raise HTTPException(status_code=404, detail="Result not found. Try again later.")

    aggregated = []
    for filename in sorted(os.listdir(log_dir)):
        if filename.endswith(".json"):
            with open(os.path.join(log_dir, filename)) as f:
                try:
                    content = json.load(f)
                    if isinstance(content, list):
                        aggregated.extend(content)
                    else:
                        aggregated.append(content)
                except Exception as e:
                    aggregated.append({"error": f"Failed to load {filename}: {str(e)}"})

    return JSONResponse(content={"request_id": request_id, "results": aggregated})
