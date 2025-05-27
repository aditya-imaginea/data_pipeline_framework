import os
import json
import uuid
import subprocess
import sys

# Configurable batch size
BATCH_SIZE = 100

def split_dataset(dataset_path, batch_dir):
    """
    Splits the dataset JSON file into smaller files of BATCH_SIZE.
    Returns list of paths to batch files.
    """
    with open(dataset_path, "r") as f:
        data = json.load(f)

    os.makedirs(batch_dir, exist_ok=True)
    batch_files = []

    for i in range(0, len(data), BATCH_SIZE):
        batch = data[i:i + BATCH_SIZE]
        batch_file = os.path.join(batch_dir, f"batch_{i // BATCH_SIZE}.json")
        with open(batch_file, "w") as bf:
            json.dump(batch, bf, indent=2)
        batch_files.append(batch_file)

    return batch_files


def run_batches(batch_files, pipeline_path, request_id):
    """
    Runs a Docker container for each batch, executing pipeline/engine.py
    """
    processes = []

    state_log_dir = f"state_logs/{request_id}"
    os.makedirs(state_log_dir, exist_ok=True)

    for i, batch_file in enumerate(batch_files):
        output_file = f"{state_log_dir}/batch_{i}_transitions.json"
        print(f"Running batch {i}: {batch_file} -> {output_file}")

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}:/app",
            "-e", f"OPENAI_API_KEY={os.environ.get('OPENAI_API_KEY')}",
            "data-pipeline:latest",
            "python", "pipeline/engine.py",
            pipeline_path,
            batch_file,
            output_file
        ]
        processes.append(subprocess.Popen(cmd))

    for p in processes:
        p.wait()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python batch_runner.py <request_id>")
        sys.exit(1)

    request_id = sys.argv[1]
    base_path = f"uploads/{request_id}"
    pipeline_path = f"{base_path}/pipeline_definition.json"
    dataset_path = f"{base_path}/dataset.json"
    batch_dir = f"{base_path}/batches"

    os.makedirs(batch_dir, exist_ok=True)

    batch_files = split_dataset(dataset_path, batch_dir)
    run_batches(batch_files, pipeline_path, request_id)
