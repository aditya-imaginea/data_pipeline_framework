import os
import json
import subprocess
import sys
import time
from typing import List, Dict, Any

def split_dataset(dataset_path: str, batch_dir: str, batch_size: int) -> List[str]:
    """
    Splits the dataset JSON file into smaller files of given batch_size.
    Returns list of paths to batch files.

    Args:
        dataset_path (str): Path to the input dataset JSON file.
        batch_dir (str): Directory where the batch files will be saved.
        batch_size (int): Maximum number of records per batch file.

    Returns:
        List[str]: A list of paths to the created batch files.
    """
    try:
        with open(dataset_path, "r", encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Dataset file not found: {dataset_path}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON format in dataset file: {dataset_path}", file=sys.stderr)
        return []

    if not isinstance(data, list):
        print(f"WARNING: Dataset file '{dataset_path}' did not contain a JSON array. Treating as single record.", file=sys.stderr)
        data = [data] # Wrap single dict in a list for consistent processing

    os.makedirs(batch_dir, exist_ok=True)
    batch_files = []

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_file = os.path.join(batch_dir, f"batch_{i // batch_size}.json")
        try:
            with open(batch_file, "w", encoding='utf-8') as bf:
                json.dump(batch, bf, indent=2)
            batch_files.append(batch_file)
        except IOError as e:
            print(f"ERROR: Could not write batch file {batch_file}: {e}", file=sys.stderr)
            # Decide if you want to stop or continue on file write errors

    return batch_files

def run_batches(batch_files: List[str], dynamic_pipeline_path: str, script_dir: str, request_id: str, results_output_base_path: str):
    """
    Runs a Docker container for each batch, executing pipeline/engine.py.

    Args:
        batch_files (List[str]): List of paths to individual batch JSON files.
        dynamic_pipeline_path (str): Path to the dynamically generated pipeline definition.
        script_dir (str): Directory containing all transformation scripts.
        request_id (str): Unique ID for the current request.
        results_output_base_path (str): Base directory where results will be written (e.g., 'requests/{request_id}/state_logs').
    """
    os.makedirs(results_output_base_path, exist_ok=True)
    print(f"Batch results will be written to: {results_output_base_path}")

    processes = []
    start_time = time.time()

    # Get GOOGLE_API_KEY from the environment
    # IMPORTANT: Ensure GOOGLE_API_KEY is available in the environment where batch_runner.py runs.
    # If running batch_runner.py directly via subprocess from FastAPI, FastAPI's environment
    # variables (e.g., from .env) should be propagated.
    google_api_key = os.environ.get('GOOGLE_API_KEY', '')
    if not google_api_key:
        print("WARNING: GOOGLE_API_KEY not found in environment. Docker containers might fail if LLM access is needed.", file=sys.stderr)

    for i, batch_file in enumerate(batch_files):
        # Each batch will output its results to a unique file within the state_logs directory
        output_file = os.path.join(results_output_base_path, f"batch_{i}_transitions.jsonl") # Using .jsonl as per state_tracker
        print(f"Running batch {i} for {batch_file} -> output: {output_file}")

        # The Docker command to run pipeline/engine.py for each batch
        # IMPORTANT: /app/pipeline/engine.py is the path *inside* the Docker container
        # The host paths need to be mapped using -v
        cmd = [
            "docker", "run", "--rm", # --rm removes the container after it exits
            "-v", f"{os.getcwd()}:/app", # Mount current working directory to /app inside container
            "-e", f"GOOGLE_API_KEY={google_api_key}", # Pass the GOOGLE_API_KEY to the container
            "-e", f"STATE_LOG_PATH=/app/{output_file}", # Pass the specific output file path for state_tracker
            "data-pipeline:latest", # The name of your Docker image
            "python", "pipeline/engine.py", # Command to run inside container
            f"/app/{dynamic_pipeline_path}", # Path to pipeline definition inside container
            f"/app/{batch_file}",            # Path to batch dataset inside container
            f"/app/{output_file}",           # Path for output file inside container (should match STATE_LOG_PATH usage)
            f"/app/{script_dir}"             # Path to scripts directory inside container
        ]

        print("Docker command:", " ".join(cmd))
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        processes.append((i, batch_file, process))

    for i, batch_file, process in processes:
        stdout, stderr = process.communicate() # Wait for process to complete and get output
        retcode = process.returncode
        if retcode != 0:
            print(f"Batch {i} ({batch_file}) failed with return code {retcode}", file=sys.stderr)
            print("--- STDOUT ---", file=sys.stderr)
            print(stdout, file=sys.stderr)
            print("--- STDERR ---", file=sys.stderr)
            print(stderr, file=sys.stderr)
        else:
            print(f"Batch {i} ({batch_file}) completed successfully.")
            # Optionally print stdout/stderr for successful runs if needed for debug
            # print("--- STDOUT ---")
            # print(stdout)

    elapsed = time.time() - start_time
    print(f"All batches completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    # Expected arguments:
    # 1: request_id
    # 2: batch_size
    # 3: dynamic_pipeline_def_path (e.g., requests/UUID/dynamic_pipeline_definition.json)
    # 4: dataset_path (e.g., requests/UUID/dataset.json)
    # 5: script_dir (e.g., requests/UUID/scripts)
    if len(sys.argv) < 6:
        print("Usage: python batch_runner.py <request_id> <batch_size> <dynamic_pipeline_path> <dataset_path> <script_dir>", file=sys.stderr)
        sys.exit(1)

    request_id = sys.argv[1]
    batch_size = int(sys.argv[2])
    dynamic_pipeline_path = sys.argv[3]
    dataset_path = sys.argv[4]
    script_dir = sys.argv[5]

    # Derived paths (relative to where batch_runner.py is run)
    base_path = f"requests/{request_id}" # This is derived for context, not explicitly used for input paths here
    batch_dir = os.path.join(base_path, "batches")
    results_output_base_path = os.path.join(base_path, "results") # Where engine.py will write its state_transitions.jsonl

    # Ensure batch directory exists before splitting
    os.makedirs(batch_dir, exist_ok=True)

    batch_files = split_dataset(dataset_path, batch_dir, batch_size)
    
    if not batch_files: # If dataset splitting failed, exit
        sys.exit(1)

    run_batches(batch_files, dynamic_pipeline_path, script_dir, request_id, results_output_base_path)

