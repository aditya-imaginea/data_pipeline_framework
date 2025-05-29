import uuid
import shutil
import os
import json
import subprocess
from typing import List
from fastapi import FastAPI, Form, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

app = FastAPI(title="FSM-Based Scalable Pipeline API")

# Allow frontend requests (adjust origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend UI
ui_path = Path(__file__).parent / "ui"
app.mount("/static", StaticFiles(directory=ui_path / "static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_index():
    return (ui_path / "index.html").read_text()


async def save_scripts_from_pipeline(
    pipeline_file: UploadFile, form_data, script_dir: str
) -> list:
    print("Invoking save scripts to save files in script directory:", script_dir)

    pipeline_file.file.seek(0)
    pipeline_content = json.load(pipeline_file.file)
    steps = pipeline_content.get("steps", [])

    os.makedirs(script_dir, exist_ok=True)

    for index, step in enumerate(steps):
        for script_type in ["main_script", "pre_script", "post_script"]:
            script_filename = step.get(script_type)
            if not script_filename:
                continue

            # Form field names follow this pattern: main_0, pre_0, post_0
            field_name = f"{script_type.split('_')[0]}_{index}"
            if field_name in form_data:
                script_file: UploadFile = form_data[field_name]
                save_path = os.path.join(script_dir, script_filename)
                print(f"Saving {field_name} to {save_path}")
                with open(save_path, "wb") as f:
                    shutil.copyfileobj(script_file.file, f)
            else:
                print(f"WARNING: Expected form field '{field_name}' not found in form data.")

    return steps


@app.post("/submit_pipeline")
async def submit_pipeline(
    request: Request,
    pipeline: UploadFile = File(...),
    dataset: UploadFile = File(...),
    batch_size: int = Form(...),
):
    try:
        
        print("Invoked submit pipeline")
        # DEBUG: Dump form keys to inspect what was sent
        form = await request.form()
        print("Incoming form keys:", list(form.keys()))
        print("Files attached:", pipeline.filename, dataset.filename)
        print("Batch size received:", batch_size)

        # Create unique request ID and directories
        request_id = str(uuid.uuid4())
        base_path = f"requests/{request_id}"
        os.makedirs(base_path, exist_ok=True)

        # Save uploaded files
        pipeline_path = os.path.join(base_path, "pipeline.json")
        dataset_path = os.path.join(base_path, "dataset.json")

        with open(pipeline_path, "wb") as f:
            shutil.copyfileobj(pipeline.file, f)
        with open(dataset_path, "wb") as f:
            shutil.copyfileobj(dataset.file, f)

        # Save script files
        form = await request.form()
        script_dir = os.path.join(base_path, "scripts")
        await save_scripts_from_pipeline(pipeline, form, script_dir)

        # Create batch directory
        batch_dir = os.path.join(base_path, "batches")
        os.makedirs(batch_dir, exist_ok=True)

        # Kick off batch processing (non-blocking)
        subprocess.Popen(["python", "batch_runner.py", request_id, str(batch_size)])

        return {"request_id": request_id, "status": "processing_started"}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit pipeline: {str(e)}"
        )


@app.get("/get_result/{request_id}")
async def get_result(request_id: str):
    response_dir = f"requests/{request_id}/state_logs"

    if not os.path.exists(response_dir) or not os.path.isdir(response_dir):
        raise HTTPException(
            status_code=404, detail="Invalid request ID or results not ready."
        )

    result = []
    for fname in os.listdir(response_dir):
        if fname.endswith(".json"):
            file_path = os.path.join(response_dir, fname)
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        result.extend(data)
                    else:
                        result.append(data)
            except json.JSONDecodeError:
                continue  # skip malformed files silently, or log if needed

    return {"request_id": request_id, "results": result}
