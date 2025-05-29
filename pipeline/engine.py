import sys
import json
import os

from pipeline.loader import load_pipeline_definition, load_dataset
from pipeline.executor import PipelineExecutor

def run_pipeline(pipeline_path: str, dataset_path: str, state_table_path: str, script_dir: str):
    print(f"Running pipeline:\n - Pipeline: {pipeline_path}\n - Dataset: {dataset_path}\n - Output: {state_table_path}", flush=True)
    pipeline_definition = load_pipeline_definition(pipeline_path)
    dataset = load_dataset(dataset_path)
    executor = PipelineExecutor(pipeline_definition)
    print(script_dir)
    results = executor.execute(dataset,script_dir)

# Ensure the output directory exists
    os.makedirs(os.path.dirname(state_table_path), exist_ok=True)

    with open(state_table_path, 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    pipeline_path = sys.argv[1]
    dataset_path = sys.argv[2]
    output_path = sys.argv[3]
    script_dir = sys.argv[4]
    run_pipeline(pipeline_path, dataset_path, output_path,script_dir)
