import socket
import threading
import webbrowser

from app import app


def find_available_port():
    for port in range(8000, 8100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            try:
                server.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No available local port found for Scan2scanner.")


if __name__ == "__main__":
    port = find_available_port()
    url = f"http://127.0.0.1:{port}"
    threading.Timer(1, lambda: webbrowser.open(url)).start()
    app.run(host="127.0.0.1", port=port, debug=False)