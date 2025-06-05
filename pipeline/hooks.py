import importlib.util
import logging
import sys
import os
from types import ModuleType
from typing import Dict, Any, Optional

# Set up logging for this module
logger = logging.getLogger(__name__)

# A cache for loaded modules to avoid re-loading the same script multiple times
_module_cache: Dict[str, ModuleType] = {}

def load_script_module(script_path: str, module_name: str) -> Optional[ModuleType]:
    """
    Dynamically loads a Python script as a module.
    Caches loaded modules to prevent redundant loading.

    Args:
        script_path (str): The full path to the Python script file.
        module_name (str): A unique name for the module. Important for importlib.

    Returns:
        Optional[ModuleType]: The loaded module object, or None if loading fails.
    """
    if script_path in _module_cache:
        logger.debug(f"Returning cached module for {script_path}")
        return _module_cache[script_path]

    if not os.path.exists(script_path):
        logger.error(f"Script file not found: {script_path}")
        return None

    try:
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        if spec is None:
            logger.error(f"Could not create module spec for script: {script_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        # Add the module to sys.modules to prevent it from being re-loaded with the same name
        # This is useful if different scripts might have the same file name but different paths
        sys.modules[module_name] = module 
        
        if spec.loader:
            spec.loader.exec_module(module)
            _module_cache[script_path] = module
            logger.info(f"Successfully loaded script as module: {script_path} as {module_name}")
            return module
        else:
            logger.error(f"Module loader not found for spec: {script_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading script '{script_path}' as module '{module_name}': {e}", exc_info=True)
        return None

def execute_hook(module: Optional[ModuleType], record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes the 'transform' function within a loaded module, if it exists.
    If the module is None or 'transform' function is not found, returns the record unchanged.

    Args:
        module (Optional[ModuleType]): The loaded Python module object.
        record (Dict[str, Any]): The data record to be transformed.

    Returns:
        Dict[str, Any]: The transformed record, or the original record if transformation fails or is not applicable.
    """
    if module is None:
        logger.debug("No module provided for hook execution. Returning record unchanged.")
        return record

    if hasattr(module, 'transform'):
        try:
            # Ensure the transform function accepts and returns a dictionary
            transformed_record = module.transform(record)
            if not isinstance(transformed_record, dict):
                logger.warning(f"Hook '{module.__name__}' 'transform' function did not return a dictionary. Returning original record.")
                return record
            logger.debug(f"Successfully applied transform from hook: {module.__name__}")
            return transformed_record
        except Exception as e:
            logger.error(f"Error executing 'transform' function in hook '{module.__name__}': {e}", exc_info=True)
            # Return original record on transformation error
            return record
    else:
        logger.warning(f"No 'transform' function found in module '{module.__name__}'. Returning record unchanged.")
        return record

