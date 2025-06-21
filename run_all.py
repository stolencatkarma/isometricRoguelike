import subprocess
import sys
import threading

def run_process(name, cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
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
    server_proc = run_process("SERVER", server_cmd)
    print("Starting client...")
    client_proc = run_process("CLIENT", client_cmd)
    try:
        server_proc.wait()
        client_proc.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        server_proc.terminate()
        client_proc.terminate()

if __name__ == "__main__":
    main()
