import importlib.util # Still needed if we want to directly load modules (though hooks.py does it now)
import os
import logging
from typing import Dict, List, Any, Optional

# Import the refined functions from hooks and state_tracker
from .hooks import load_script_module, execute_hook
from .state_tracker import record_state_transition

# Set up logging for this module
logger = logging.getLogger(__name__)

class PipelineExecutor:
    """
    Executes a defined pipeline on a dataset, applying pre-processing, main transformations,
    and post-processing scripts to each record.
    Optionally logs the state transitions of each record.
    """
    def __init__(self, pipeline_definition: Dict[str, Any], enable_state_log: bool = True):
        """
        Initializes the PipelineExecutor.

        Args:
            pipeline_definition (Dict[str, Any]): A dictionary defining the pipeline steps.
                                                  Expected format: {"steps": [{"name": "step_name", "main_script": "path/to/main.py", ...}]}
            enable_state_log (bool): If True, records the state of each record after each step
                                     to a log file.
        """
        if not isinstance(pipeline_definition, dict) or "steps" not in pipeline_definition:
            logger.error("Invalid pipeline definition: Missing 'steps' key or not a dictionary.")
            raise ValueError("Invalid pipeline definition provided.")

        self.pipeline_definition = pipeline_definition
        self.enable_state_log = enable_state_log
        logger.info("PipelineExecutor initialized.")

    def execute(self, dataset: List[Dict[str, Any]], script_dir: str) -> List[Dict[str, Any]]:
        """
        Executes the defined pipeline on a given dataset.

        Args:
            dataset (List[Dict[str, Any]]): A list of dictionaries, where each dictionary
                                            represents a record to be processed.
            script_dir (str): The base directory where all pipeline scripts (pre, main, post) are located.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents
                                  the final state transition log for a processed record.
                                  Returns only the 'raw' and final states if state logging is disabled.
        """
        if not isinstance(dataset, list):
            logger.error("Invalid dataset: Expected a list of dictionaries.")
            raise TypeError("Dataset must be a list of dictionaries.")
        if not os.path.isdir(script_dir):
            logger.error(f"Script directory not found or is not a directory: {script_dir}")
            raise FileNotFoundError(f"Script directory not found: {script_dir}")

        all_transitions: List[Dict[str, Any]] = []

        logger.info(f"Starting pipeline execution for {len(dataset)} records.")
        for i, record in enumerate(dataset):
            # Create a deep copy of the record for processing to avoid modifying original dataset
            current_record = dict(record) # Start with a copy of the raw record
            state_record: Dict[str, Any] = {"raw": dict(record)} # Store raw for logging

            logger.debug(f"Processing record {i+1}/{len(dataset)}")

            for step in self.pipeline_definition.get("steps", []):
                step_name = step.get("name", "unnamed_step")
                logger.debug(f"Executing step '{step_name}' for record {i+1}")

                # --- Handle Pre-script ---
                if step.get("pre_script"):
                    pre_script_path = os.path.join(script_dir, step["pre_script"])
                    # Generate a unique module name for this specific hook and step
                    pre_module_name = f"pre_{step_name}_module_{os.path.basename(pre_script_path).replace('.', '_')}"
                    pre_module = load_script_module(pre_script_path, pre_module_name)
                    if pre_module:
                        transformed_pre_record = execute_hook(pre_module, current_record)
                        # Only update current_record if transformation was successful and returned a dict
                        if transformed_pre_record is not current_record: # Check if a new dict was returned
                            current_record = transformed_pre_record
                        state_record[f"pre_{step_name}"] = dict(current_record)
                    else:
                        logger.warning(f"Failed to load or execute pre-script for step '{step_name}'. Record unchanged.")
                        state_record[f"pre_{step_name}"] = dict(current_record) # Log current state even if script failed

                # --- Handle Main Script ---
                if step.get("main_script"):
                    main_script_path = os.path.join(script_dir, step["main_script"])
                    main_module_name = f"main_{step_name}_module_{os.path.basename(main_script_path).replace('.', '_')}"
                    main_module = load_script_module(main_script_path, main_module_name)
                    if main_module:
                        transformed_main_record = execute_hook(main_module, current_record)
                        if transformed_main_record is not current_record:
                            current_record = transformed_main_record
                        state_record[f"main_{step_name}"] = dict(current_record)
                    else:
                        logger.error(f"Failed to load or execute main script for step '{step_name}'. This is critical. Record unchanged.")
                        state_record[f"main_{step_name}"] = dict(current_record) # Log current state

                # --- Handle Post-script ---
                if step.get("post_script"):
                    post_script_path = os.path.join(script_dir, step["post_script"])
                    # CORRECTED BUG: Used post_script_path here, not pre_script_path
                    post_module_name = f"post_{step_name}_module_{os.path.basename(post_script_path).replace('.', '_')}"
                    post_module = load_script_module(post_script_path, post_module_name)
                    if post_module:
                        transformed_post_record = execute_hook(post_module, current_record)
                        if transformed_post_record is not current_record:
                            current_record = transformed_post_record
                        state_record[f"post_{step_name}"] = dict(current_record)
                    else:
                        logger.warning(f"Failed to load or execute post-script for step '{step_name}'. Record unchanged.")
                        state_record[f"post_{step_name}"] = dict(current_record) # Log current state

                # Update the record for the next step, ensuring it's always a new dict
                # This ensures each step works on a fresh copy of the record after previous transformations
                # This line is redundant if current_record is updated in place, but good for clarity if changed
                # record = current_record # Not needed since current_record holds the state for the next step
            
            # Record the final state transition for the record if enabled
            if self.enable_state_log:
                record_state_transition(state_record)
            
            all_transitions.append(state_record) # Store the complete state history for this record

        logger.info("Pipeline execution completed.")
        return all_transitions

