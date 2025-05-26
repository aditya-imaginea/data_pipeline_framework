
import json

def load_pipeline_definition(pipeline_path):
    with open(pipeline_path, 'r') as f:
        return json.load(f)

def load_dataset(dataset_path):
    with open(dataset_path, 'r') as f:
        return json.load(f)
