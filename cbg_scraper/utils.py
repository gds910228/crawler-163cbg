import os
import time
from datetime import datetime

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def sleep_s(seconds: float):
    if seconds and seconds > 0:
        time.sleep(seconds)