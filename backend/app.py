import subprocess
import sys
import threading
import time
import webbrowser
import shutil
from waitress import serve
from app import create_app
import socket
import os


dev_mode = "--devMode" in sys.argv

port = 5000 if dev_mode else 52586
URL = f"http://127.0.0.1:{port}"
app = create_app()

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def get_kill_instructions(port: int) -> str:
    base_message = f"Unable to start the application. Port {port} is already in use.\n\n"

    warning = (
        "WARNING: Be very careful before killing a process. "
        "The PID you choose might belong to another important application, "
        "and terminating it could cause unwanted side effects.\n\n"
    )

    if sys.platform.startswith("win"):
        instructions = (
            "To identify the process:\n"
            f"    netstat -ano | findstr :{port}\n\n"
            "The correct PID is in the last column of the line where LISTENING is written.\n\n"
            "To kill the process (replace X with the PID):\n"
            "    taskkill /PID X /F\n"
        )
    elif sys.platform.startswith("linux"):
        instructions = (
            "To identify the process (look for the PID column associated with the port):\n"
            f"    sudo lsof -i :{port}\n\n"
            "To kill the process (replace X with the PID):\n"
            "    sudo kill -9 X\n"
        )
    elif sys.platform.startswith("darwin"):
        instructions = (
            "To identify the process (look for the PID column associated with the port):\n"
            f"    lsof -i :{port}\n\n"
            "To kill the process (replace X with the PID):\n"
            "    kill -9 X\n"
        )
    else:
        return f"Unable to start the application. Port {port} is in use. Unknown operating system."

    return base_message + warning + instructions

def run_waitress():
    serve(app, host="0.0.0.0", port=port)


def open_browser():
    if "--noBrowser" not in sys.argv:
        webbrowser.open(URL, new=2)


def get_script_path():
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(__file__)


def open_console_and_wait():
    script_path = get_script_path()

    if sys.platform.startswith("win"):
        cmd = [
            "cmd",
            "/c",
            "start",
            "cmd",
            "/k",
            f'"{sys.executable}" "{script_path}"',
        ]
        proc = subprocess.Popen(cmd)
        proc.wait()

    elif sys.platform.startswith("linux"):
        terminals = [
            "gnome-terminal",
            "konsole",
            "xfce4-terminal",
            "lxterminal",
            "xterm",
        ]
        terminal_cmd = None
        for term in terminals:
            if shutil.which(term):
                terminal_cmd = term
                break

        if terminal_cmd is None:
            print("No supported terminal emulator found.")
            input("Press Enter to exit...")
            return

        cmd = []
        bash_command = f'"{sys.executable}" "{script_path}"; exec bash'

        if terminal_cmd == "gnome-terminal":
            cmd = [terminal_cmd, "--", "bash", "-c", bash_command]
        elif terminal_cmd == "konsole":
            cmd = [terminal_cmd, "-e", f"bash -c '{bash_command}'"]
        elif terminal_cmd == "xfce4-terminal":
            cmd = [terminal_cmd, "--hold", "-e", f"bash -c '{bash_command}'"]
        elif terminal_cmd == "lxterminal":
            cmd = [terminal_cmd, "-e", f"bash -c '{bash_command}'"]
        else:  # xterm or other fallback
            cmd = [terminal_cmd, "-hold", "-e", f"bash -c '{bash_command}'"]

        proc = subprocess.Popen(cmd)
        proc.wait()

    elif sys.platform == "darwin":
        script = f"""
            tell application "Terminal"
                do script "{sys.executable} '{script_path}'"
                activate
            end tell
        """
        proc = subprocess.Popen(["osascript", "-e", script])
        proc.wait()
    else:
        print("Unsupported OS for external console.")
        input("Press Enter to exit...")


def main():
    if is_port_in_use(port):
        print(get_kill_instructions(port))
        sys.exit(1)
    
    if not sys.stdin.isatty():
        open_console_and_wait()
        return

    print("Application started successfully.")
    print(f"Please open your browser and go to {URL}")
    print("(Close this window to stop the server.)")

    if sys.platform.startswith("win"):
        print("\n====== IMPORTANT NOTICE ======")
        print(
            "On Windows terminals, selecting text with the mouse will temporarily pause the application."
        )
        print(
            "To resume, simply press Enter or right-click to copy, then press Enter again."
        )
        print("==============================\n")

    print("\n--- Server logs will appear below ---\n")

    server_thread = threading.Thread(target=run_waitress, daemon=True)
    server_thread.start()

    open_browser()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server.")

    sys.exit(0)


if __name__ == "__main__":
    main()
