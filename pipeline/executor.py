import importlib.util
import os
from .hooks import execute_hook
from .state_tracker import record_state_transition

class PipelineExecutor:
    def __init__(self, pipeline_definition, enable_state_log=True):
        self.pipeline_definition = pipeline_definition
        self.enable_state_log = enable_state_log

    def _load_script(self, path):
        spec = importlib.util.spec_from_file_location("module.name", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def execute(self, dataset, script_dir):
        all_transitions = []

        for record in dataset:
            state_record = {"raw": dict(record)}

            for step in self.pipeline_definition["steps"]:
                if step.get("pre_script"):
                    pre_script_path = os.path.join(script_dir, step["pre_script"])
                    pre = self._load_script(pre_script_path)
                    record = execute_hook(pre, record)
                    state_record[f"pre_{step['name']}"] = dict(record)
                
                script_path = os.path.join(script_dir, step["main_script"])
                main = self._load_script(script_path)
                record = main.transform(record)
                state_record[f"main_{step['name']}"] = dict(record)

                if step.get("post_script"):
                    post_script_path = os.path.join(script_dir, step["post_script"])
                    post = self._load_script(pre_script_path)
                    record = execute_hook(post, record)
                    state_record[f"post_{step['name']}"] = dict(record)

            if self.enable_state_log:
                record_state_transition(state_record)

            all_transitions.append(state_record)

        return all_transitions
