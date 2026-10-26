import json
import socket
import threading

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


class WeatherServer:
    def __init__(self, host="0.0.0.0", port=8888, command_handler=None):
        self.host = host
        self.port = port
        self.command_handler = command_handler
        self.server_socket = None
        self.running = False
        self.clients = []

    def start(self):
        self.running = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)

        thread = threading.Thread(target=self._accept_loop, daemon=True)
        thread.start()

    def _accept_loop(self):
        while self.running:
            try:
                client_sock, client_addr = self.server_socket.accept()
                self.clients.append(client_sock)
                t = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, client_addr),
                    daemon=True,
                )
                t.start()
            except Exception:
                break

    def _handle_client(self, client_sock, client_addr):
        buffer = ""
        while self.running:
            try:
                data = client_sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        req = json.loads(line)
                        if self.command_handler:
                            resp = self.command_handler(req, client_addr)
                        else:
                            resp = {"status": "ok", "message": "Команда принята"}
                    except Exception as err:
                        resp = {"status": "error", "message": str(err)}

                    response_bytes = (json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8")
                    client_sock.sendall(response_bytes)
            except Exception:
                break

        try:
            client_sock.close()
        except Exception:
            pass
        if client_sock in self.clients:
            self.clients.remove(client_sock)

    def stop(self):
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass


class WeatherClient:
    def __init__(self, host="127.0.0.1", port=8888, timeout=5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.timeout)
        self.sock.connect((self.host, self.port))

    def send_command(self, cmd_dict):
        if not self.sock:
            self.connect()
        msg = json.dumps(cmd_dict, ensure_ascii=False) + "\n"
        self.sock.sendall(msg.encode("utf-8"))

        data = b""
        while b"\n" not in data:
            chunk = self.sock.recv(4096)
            if not chunk:
                break
            data += chunk

        line = data.decode("utf-8").strip()
        return json.loads(line)

    def close(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None
