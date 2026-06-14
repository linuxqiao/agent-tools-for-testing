
import re

PATTERN_DB = [
    {
        "pattern": r"Operation not permitted",
        "category": "Permissions / Configuration",
        "confidence": 90,
        "suggestion": "Check perf_event_paranoid, capability status. Try: setcap 'cap_net_admin,cap_net_bind_service=+ep', etc to fix."
    },
    {
        "pattern": r"Command not found",
        "category": "Script / Environment",
        "confidence": 90,
        "suggestion": "Check the tools dependency and path if it is right."
    },
    {
        "pattern": r"Killed",
        "category": "resource / OOM",
        "confidence": 70,
        "suggestion": "check the memory usage, and consider to increase buffer."
    }
]

def quick_classify(log_exit):
    for item in PATTERN_DB:
        if re.search(item["pattern"], log_exit, re.IGNORECASE):
            return item

    return None       # Unknown issues
