import json
import os
import math
import subprocess
from pathlib import Path

BATCH_SIZE = 25

def split_dataset(dataset_path, output_dir):
    with open(dataset_path) as f:
        data = json.load(f)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    total_batches = math.ceil(len(data) / BATCH_SIZE)
    batch_files = []

    for i in range(total_batches):
        batch_data = data[i * BATCH_SIZE:(i + 1) * BATCH_SIZE]
        batch_file = os.path.join(output_dir, f"batch_{i}.json")
        with open(batch_file, "w") as bf:
            json.dump(batch_data, bf, indent=2)
        batch_files.append(batch_file)

    return batch_files

def run_batches(batch_files, pipeline_path):
    processes = []
    for i, batch_file in enumerate(batch_files):
        print(batch_file)
        output_file = f"state_logs/batch_{i}_transitions.json"
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}:/app",
            "--env-file", ".env",
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
    dataset_path = "datasets/sample_dataset_capitals.json"
    pipeline_path = "storage/pipeline_definitions/pipeline_definition.json"
    batch_dir = "batches"

    batch_files = split_dataset(dataset_path, batch_dir)
    run_batches(batch_files, pipeline_path)
