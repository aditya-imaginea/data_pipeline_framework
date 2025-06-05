import json
import os
from datetime import datetime
import logging
from typing import Dict, Any

# Set up logging for this module
logger = logging.getLogger(__name__)

# The log file path, defaults to './state_transitions.jsonl'
# Can be overridden by the STATE_LOG_PATH environment variable
LOG_PATH = os.environ.get("STATE_LOG_PATH", "./state_transitions.jsonl")

def record_state_transition(state: Dict[str, Any]):
    """
    Appends a JSON record of the state transition to a log file.
    Each call appends a new line, making it a JSON Lines (JSONL) file.

    Args:
        state (Dict[str, Any]): A dictionary representing the state of a record
                                 at a particular point in the pipeline.
    """
    # Ensure the directory for the log file exists
    log_directory = os.path.dirname(LOG_PATH)
    if log_directory and not os.path.exists(log_directory):
        try:
            os.makedirs(log_directory, exist_ok=True)
            logger.info(f"Created log directory: {log_directory}")
        except OSError as e:
            logger.error(f"Failed to create log directory '{log_directory}': {e}")
            # Depending on severity, you might want to raise here or continue without logging
            return

    state_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **state  # Unpack the provided state dictionary into the log entry
    }

    try:
        # Open in append mode ('a') with UTF-8 encoding
        # Using a context manager (with open(...)) ensures the file is properly closed
        with open(LOG_PATH, "a", encoding='utf-8') as f:
            f.write(json.dumps(state_entry) + "\n")
        logger.debug(f"Recorded state transition for record: {list(state.keys())[0] if state else 'empty state'}")
    except IOError as e:
        logger.error(f"Failed to write state transition to log file '{LOG_PATH}': {e}")
    except TypeError as e:
        logger.error(f"Failed to serialize state to JSON. Check state content for non-serializable types: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while recording state transition: {e}")

