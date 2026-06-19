import socket
import threading


class LanTransport:

    def __init__(self, on_receive, host=False, ip=None, port=5555):
        self.on_receive = on_receive
        self.host = host
        self.ip = ip
        self.port = port

        self.sock = None
        self.conn = None
        self.running = False

    # -----------------------------
    # Start Transport (THREAD SAFE)
    # -----------------------------
    def start(self):
        self.running = True

        if self.host:
            threading.Thread(target=self._start_server, daemon=True).start()
        else:
            threading.Thread(target=self._start_client, daemon=True).start()

    # -----------------------------
    # SERVER
    # -----------------------------
    def _start_server(self):
        print("[MP] Server thread started")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", self.port))
        self.sock.listen(1)

        self.conn, addr = self.sock.accept()
        print("[MP] Client connected:", addr)

        self._receive_loop(self.conn)

    # -----------------------------
    # CLIENT
    # -----------------------------
    def _start_client(self):
        print("[MP] Client thread started")

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.ip, self.port))

        self._receive_loop(self.sock)

    # -----------------------------
    # RECEIVE LOOP
    # -----------------------------
    def _receive_loop(self, connection):
        while self.running:
            try:
                data = connection.recv(1024)
                if not data:
                    break

                decoded = data.decode()
                self.on_receive(decoded)

            except:
                break

        self.close()

    # -----------------------------
    # SEND
    # -----------------------------
    def send(self, data):
        try:
            message = str(data).encode()
            if self.conn:
                self.conn.sendall(message)
            elif self.sock:
                self.sock.sendall(message)
        except:
            pass

    # -----------------------------
    # CLOSE
    # -----------------------------
    def close(self):
        self.running = False
        try:
            if self.conn:
                self.conn.close()
            if self.sock:
                self.sock.close()
        except:
            pass
