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


def find_free_port_auto():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


dev_mode = "--devMode" in sys.argv

port = 5000 if dev_mode else find_free_port_auto()
URL = f"http://127.0.0.1:{port}"
app = create_app()


def run_waitress():
    serve(app, host="0.0.0.0", port=port)


def open_browser():
    if "--noBrowser" not in sys.argv:
        webbrowser.open_new(URL)


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
