import uuid
import shutil
import os
import json
import subprocess
import sys # Added for sys.executable
from typing import List, Dict, Any
from fastapi import FastAPI, Form, Request, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from dotenv import load_dotenv # Import load_dotenv

# Load environment variables from .env file at application startup
# This ensures GOOGLE_API_KEY is available in os.environ for batch_runner.py
load_dotenv() 

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
    # Serve the main index.html file from the ui directory
    index_file_path = ui_path / "index.html"
    if not index_file_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found.")
    return index_file_path.read_text()


async def save_scripts_from_pipeline_definition(
    pipeline_def_content: Dict[str, Any], form_data: Dict[str, Any], script_dir: str
) -> None:
    """
    Saves uploaded script files from the form data into the specified script directory,
    based on the parsed pipeline definition content.

    Args:
        pipeline_def_content (Dict[str, Any]): The parsed JSON content of the
                                                dynamically generated pipeline definition
                                                from the frontend.
        form_data (Dict[str, Any]): The complete form data from the client request,
                                    containing the uploaded script files.
        script_dir (str): The directory where the script files should be saved.
    """
    print("Invoking save_scripts_from_pipeline_definition to save files in script directory:", script_dir)

    steps = pipeline_def_content.get("steps", [])
    os.makedirs(script_dir, exist_ok=True)

    for index, step in enumerate(steps):
        # The script filenames are in the step metadata (e.g., "capital_transform.py")
        # The form data keys for the actual files are like "main_0", "pre_0", "post_0"
        
        for script_type_key, script_filename_key in [
            ("main", "main_script"),
            ("pre", "pre_script"),
            ("post", "post_script")
        ]:
            # Get the expected filename from the pipeline definition metadata
            script_filename = step.get(script_filename_key)
            if not script_filename:
                continue # Skip if no script defined for this type in the step

            # Construct the form field name used by the frontend (e.g., "main_0", "pre_1")
            form_field_name = f"{script_type_key}_{index}"
            
            if form_field_name in form_data:
                script_file: UploadFile = form_data[form_field_name]
                save_path = os.path.join(script_dir, script_filename)
                print(f"Saving uploaded file for '{form_field_name}' as '{script_filename}' to '{save_path}'")
                
                # Ensure the file pointer is at the beginning before copying
                script_file.file.seek(0)
                with open(save_path, "wb") as f:
                    shutil.copyfileobj(script_file.file, f)
            else:
                # This warning indicates a mismatch between frontend and backend file naming
                print(f"WARNING: Expected form field '{form_field_name}' for script '{script_filename}' not found in form data.")
                # This could be acceptable for optional pre/post scripts if the user didn't upload them
                # But it's critical for 'main' scripts. Frontend validation helps here.


@app.post("/submit_pipeline")
async def submit_pipeline(
    request: Request,
    pipeline: UploadFile = File(...), # The original pipeline.json file uploaded by user
    dataset: UploadFile = File(...),   # The dataset.json file
    batch_size: int = Form(...),
    # NEW PARAMETER: This is the dynamically generated JSON blob from the frontend
    pipeline_definition_json: UploadFile = File(..., description="Dynamically generated pipeline definition as JSON blob"),
):
    try:
        print("Invoked submit pipeline")
        
        form_data = await request.form() # Get all form data once for easier access
        print("Incoming form keys:", list(form_data.keys()))
        print("Files attached:", pipeline.filename, dataset.filename, pipeline_definition_json.filename)
        print("Batch size received:", batch_size)

        # Create unique request ID and directories
        request_id = str(uuid.uuid4())
        base_path = f"requests/{request_id}"
        os.makedirs(base_path, exist_ok=True)

        # Save the original pipeline.json and dataset.json (as before)
        # Note: The 'pipeline' file is now the original static file, not the one
        # containing dynamic steps which is now 'pipeline_definition_json'
        pipeline_path = os.path.join(base_path, "pipeline.json")
        dataset_path = os.path.join(base_path, "dataset.json")

        pipeline.file.seek(0) # Reset file pointer
        with open(pipeline_path, "wb") as f:
            shutil.copyfileobj(pipeline.file, f)
        
        dataset.file.seek(0) # Reset file pointer
        with open(dataset_path, "wb") as f:
            shutil.copyfileobj(dataset.file, f)

        # Parse the dynamically generated pipeline definition from the frontend
        pipeline_definition_json_content = json.loads(await pipeline_definition_json.read())
        print(f"Parsed dynamic pipeline definition: {pipeline_definition_json_content}")

        # Save script files using the new function and the parsed content
        script_dir = os.path.join(base_path, "scripts")
        await save_scripts_from_pipeline_definition(pipeline_definition_json_content, form_data, script_dir)

        # Create batch directory
        batch_dir = os.path.join(base_path, "batches")
        os.makedirs(batch_dir, exist_ok=True)

        # If your batch_runner.py (or your pipeline engine) expects the pipeline definition
        # to be the *dynamically generated one*, you must save it to disk as well.
        # Let's assume you save it as `dynamic_pipeline_definition.json`
        dynamic_pipeline_def_path = os.path.join(base_path, "dynamic_pipeline_definition.json")
        with open(dynamic_pipeline_def_path, "w", encoding='utf-8') as f:
            json.dump(pipeline_definition_json_content, f, indent=2)
        print(f"Saved dynamic pipeline definition to: {dynamic_pipeline_def_path}")
        
        # Kick off batch processing (non-blocking)
        # We are now passing the dynamic_pipeline_def_path directly
        subprocess.Popen([
            sys.executable, # Use the current python interpreter
            "batch_runner.py", # Assuming batch_runner.py is in the same directory as main.py
            request_id,
            str(batch_size),
            dynamic_pipeline_def_path, # Path to the dynamic pipeline definition
            dataset_path,              # Path to the dataset
            script_dir                 # Path to the scripts directory
        ])

        return {"request_id": request_id, "status": "processing_started", "message": "Pipeline files saved and batch processing initiated."}

    except Exception as e:
        # Clean up the created directory in case of an error
        if 'base_path' in locals() and os.path.exists(base_path):
            shutil.rmtree(base_path)
        print(f"Error during pipeline submission: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to submit pipeline: {str(e)}"
        )


@app.get("/get_result/{request_id}")
async def get_result(request_id: str):
    response_dir = f"requests/{request_id}/results" # Assuming state_logs is where results are stored

    if not os.path.exists(response_dir) or not os.path.isdir(response_dir):
        # Also check for a top-level results.json if run_pipeline outputs directly there
        top_level_result_path = f"requests/{request_id}/results.json"
        if os.path.exists(top_level_result_path):
            try:
                with open(top_level_result_path, "r", encoding='utf-8') as f:
                    return {"request_id": request_id, "results": json.load(f)}
            except json.JSONDecodeError as e:
                raise HTTPException(status_code=500, detail=f"Error reading result file: {e}")
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
        
        raise HTTPException(
            status_code=404, detail="Invalid request ID or results not ready."
        )

    result = []
    for fname in os.listdir(response_dir):
        if fname.endswith(".json") or fname.endswith(".jsonl"): # Allow .jsonl if using state_tracker.py
            file_path = os.path.join(response_dir, fname)
            try:
                # If it's a JSONL file (multiple JSON objects per line)
                if fname.endswith(".jsonl"):
                    with open(file_path, "r", encoding='utf-8') as f:
                        for line in f:
                            if line.strip(): # Avoid empty lines
                                try:
                                    result.append(json.loads(line))
                                except json.JSONDecodeError as e:
                                    print(f"WARNING: Malformed JSON line in {file_path}: {line.strip()} - {e}")
                                    continue # Skip malformed lines
                else: # Assume it's a single JSON object or array
                    with open(file_path, "r", encoding='utf-8') as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            result.extend(data)
                        else:
                            result.append(data)
            except json.JSONDecodeError as e:
                print(f"WARNING: Malformed JSON file {file_path}: {e}")
                continue  # skip malformed files silently, or log if needed
            except Exception as e:
                print(f"ERROR: Could not read file {file_path}: {e}")
                continue

    return {"request_id": request_id, "results": result}

