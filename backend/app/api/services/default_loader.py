import os
import sys
import json


def get_resource_path(relative_path):
    if getattr(sys, "_MEIPASS", False):
        # Prod
        base_path = sys._MEIPASS
        return os.path.join(base_path, "defaults", relative_path)
    else:
        # Dev
        current_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(current_dir, "..", "defaults", relative_path)


def load_default_json(filename):
    path = get_resource_path(filename)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading default json '{filename}': {e}")
        return None
