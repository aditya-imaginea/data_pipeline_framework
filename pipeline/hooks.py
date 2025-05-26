import importlib.util
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run_hook(script_path: str, record: Dict[str, Any], step_name: str, hook_type: str) -> Dict[str, Any]:
    
    """
    Dynamically loads and executes a script that transforms the data record.
    Expects the script to define a `transform(record: dict) -> dict` function.
    """
    try:
        spec = importlib.util.spec_from_file_location(f"{step_name}_{hook_type}_module", script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        if hasattr(module, "transform"):
            return module.transform(record)
        else:
            logger.warning(f"No `transform` function found in {script_path}. Returning record unchanged.")
            return record
    except Exception as e:
        logger.error(f"Error running {hook_type} hook for step '{step_name}': {e}")
        return record
    

def execute_hook(module, record):
    #print (record,module)
    if hasattr(module, 'transform'):
        return module.transform(record)
    return record
