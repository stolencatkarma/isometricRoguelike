import subprocess
import sys
import threading
import signal
import os

def run_process(name, cmd, env=None):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env)
    def stream():
        for line in proc.stdout:
            print(f"[{name}] {line}", end="")
    t = threading.Thread(target=stream, daemon=True)
    t.start()
    return proc

def main():
    server_cmd = [sys.executable, "server/main.py"]
    client_cmd = [sys.executable, "client/main.py"]
    print("Starting server...")
    server_env = os.environ.copy()
    server_env["PYTHONUNBUFFERED"] = "1"
    server_proc = run_process("SERVER", server_cmd, env=server_env)
    print("Starting client...")
    client_proc = run_process("CLIENT", client_cmd)
    def handle_sigint(sig, frame):
        print("\nShutting down...")
        server_proc.terminate()
        client_proc.terminate()
        sys.exit(0)
    signal.signal(signal.SIGINT, handle_sigint)
    try:
        server_proc.wait()
        client_proc.wait()
    except KeyboardInterrupt:
        handle_sigint(None, None)

if __name__ == "__main__":
    main()
