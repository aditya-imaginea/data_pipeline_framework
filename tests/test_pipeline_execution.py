
import json
from pipeline.engine import run_pipeline

def test_pipeline_end_to_end(tmp_path):
    
    output_path = tmp_path / "state_transitions.json"
    run_pipeline(
        pipeline_path="storage/pipeline_definitions/pipeline_definition.json",
        dataset_path="datasets/sample_dataset.json",
        state_table_path=str(output_path)
    )
    #print("outputpath :",output_path)
    with open(output_path, "r") as f:
        results = json.load(f)
       
    assert len(results) == 100
    #print(len(results))
    print("All results:", results)
    for r in results:
        print("final step",r)
        assert r.get("main_uppercase_step", {}).get("text", "").isupper()
        assert r.get("post_uppercase_step", {}).get("transformed") is True
