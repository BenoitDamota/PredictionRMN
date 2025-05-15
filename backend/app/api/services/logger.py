from datetime import datetime


def log_with_time(message: str):
    now = datetime.now().strftime("[%H:%M:%S]")
    print(f"{now} {message}")
