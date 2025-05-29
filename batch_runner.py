import os
import json
import subprocess
import sys
import time

def split_dataset(dataset_path, batch_dir, batch_size):
    """
    Splits the dataset JSON file into smaller files of given batch_size.
    Returns list of paths to batch files.
    """
    with open(dataset_path, "r") as f:
        data = json.load(f)

    os.makedirs(batch_dir, exist_ok=True)
    batch_files = []

    for i in range(0, len(data), batch_size):
        batch = data[i:i + batch_size]
        batch_file = os.path.join(batch_dir, f"batch_{i // batch_size}.json")
        with open(batch_file, "w") as bf:
            json.dump(batch, bf, indent=2)
        batch_files.append(batch_file)

    return batch_files

def run_batches(batch_files, pipeline_path, script_dir, request_id):
    """
    Runs a Docker container for each batch, executing pipeline/engine.py.
    """
    state_log_dir = f"requests/{request_id}/state_logs"
    os.makedirs(state_log_dir, exist_ok=True)

    processes = []
    start_time = time.time()

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
            output_file,
            script_dir
        ]

        print("Docker command:", " ".join(cmd))
        processes.append((i, batch_file, subprocess.Popen(cmd)))

    for i, batch_file, process in processes:
        retcode = process.wait()
        if retcode != 0:
            print(f"Batch {i} ({batch_file}) failed with return code {retcode}")
        else:
            print(f"Batch {i} completed successfully.")

    elapsed = time.time() - start_time
    print(f"All batches completed in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python batch_runner.py <request_id> <batch_size>")
        sys.exit(1)

    request_id = sys.argv[1]
    batch_size = int(sys.argv[2])

    base_path = f"requests/{request_id}"
    pipeline_path = os.path.join(base_path, "pipeline.json")
    dataset_path = os.path.join(base_path, "dataset.json")
    batch_dir = os.path.join(base_path, "batches")
    script_dir = os.path.join(base_path, "scripts")

    os.makedirs(batch_dir, exist_ok=True)

    batch_files = split_dataset(dataset_path, batch_dir, batch_size)
    run_batches(batch_files, pipeline_path, script_dir, request_id)
