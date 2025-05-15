import subprocess
import sys
import threading
import time
import webbrowser
import shutil
from waitress import serve
from app import create_app
import socket


def find_free_port_auto():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


port = find_free_port_auto()

URL = f"http://127.0.0.1:{port}"

app = create_app()


def run_waitress():
    serve(app, host="0.0.0.0", port=port)


def open_browser():
    webbrowser.open_new(URL)


def open_console_and_wait():
    # If running inside a terminal, just print messages and wait for user input
    if sys.stdin.isatty():
        print("Application started successfully.")
        print(f"Please open your browser and go to {URL}")
        print("(Press Ctrl+C or close this terminal to stop the server.)")
        print("\n--- Server logs will appear below ---\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        return

    if sys.platform.startswith("win"):
        cmd = [
            "cmd",
            "/c",
            "start",
            "cmd",
            "/k",
            f"echo Application started successfully. && "
            f"echo Please open your browser and go to {URL} && "
            f"echo (Close this window to stop the server.) && "
            f"echo. && "
            f"echo --- Server logs will appear below ---",
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

        message = (
            'echo "Application started successfully."; '
            f'echo "Please open your browser and go to {URL}"; '
            'echo "(Close this window to stop the server.)"; '
            'echo ""; '
            'echo "--- Server logs will appear below ---"; '
        )

        if terminal_cmd == "gnome-terminal":
            cmd = [
                terminal_cmd,
                "--",
                "bash",
                "-c",
                message + "exec bash",
            ]
        elif terminal_cmd == "konsole":
            cmd = [
                terminal_cmd,
                "-e",
                f"bash -c '{message} exec bash'",
            ]
        elif terminal_cmd == "xfce4-terminal":
            cmd = [
                terminal_cmd,
                "--hold",
                "-e",
                f"bash -c '{message}'",
            ]
        elif terminal_cmd == "lxterminal":
            cmd = [
                terminal_cmd,
                "-e",
                f"bash -c '{message} exec bash'",
            ]
        else:
            cmd = [
                terminal_cmd,
                "-hold",
                "-e",
                message + "bash",
            ]

        proc = subprocess.Popen(cmd)
        proc.wait()

    elif sys.platform == "darwin":
        script = f"""
            tell application "Terminal"
                do script "echo Application started successfully.; echo Please open your browser and go to {URL}; echo Close this window to stop the server.; echo; echo --- Server logs will appear below ---; bash"
                activate
            end tell
        """
        proc = subprocess.Popen(["osascript", "-e", script])
        proc.wait()

    else:
        print("Unsupported OS for external console.")
        input("Press Enter to exit...")


def main():
    # Start Waitress server in a daemon thread
    server_thread = threading.Thread(target=run_waitress, daemon=True)
    server_thread.start()

    # Open the default web browser to the app URL
    open_browser()

    # Launch a console window with a startup message and wait for it to close
    open_console_and_wait()

    print("Console closed, shutting down server...")

    # Waitress lacks a stop() method, so exit the process to stop the server
    sys.exit(0)


if __name__ == "__main__":
    main()
