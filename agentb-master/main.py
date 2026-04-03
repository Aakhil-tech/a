"""
Root ASGI entrypoint for deployment platforms that start from repo root.
Loads gw5_fixed/main.py while preserving its local import expectations.
"""
from pathlib import Path
import importlib.util
import sys


GW5_DIR = Path(__file__).resolve().parent / "gw5_fixed"
APP_FILE = GW5_DIR / "main.py"

# Ensure imports like `from gateway...` resolve exactly as they do locally.
sys.path.insert(0, str(GW5_DIR))

spec = importlib.util.spec_from_file_location("gw5_entrypoint", APP_FILE)
if spec is None or spec.loader is None:
    raise RuntimeError("Failed to load gw5_fixed/main.py")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
app = module.app
