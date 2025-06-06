from datetime import datetime
import threading

log_lock = threading.Lock()

def log_with_time(message: str):
    with log_lock:
        now = datetime.now().strftime("[%H:%M:%S]")
        print(f"{now} {message}")
