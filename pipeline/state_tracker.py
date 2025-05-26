import json
import os
from datetime import datetime
from typing import Dict

LOG_PATH = os.environ.get("STATE_LOG_PATH", "./state_transitions.jsonl")

def record_state_transition(state: Dict):
    #print(state)
    """
    Appends a JSON record of the state transition to a log file.
    """
    state_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        **state
    }
    #print(state_entry)
    #print(LOG_PATH)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(state_entry) + "\n")
