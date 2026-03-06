"""
Simple LAN synchronization helpers.

Host mode:
- Receives remote input states.
- Streams rendered frames to connected clients.

Client mode:
- Sends local input state.
- Receives rendered frames and displays them.
"""

import pickle
import queue
import socket
import struct
import threading
import zlib


def _send_packet(sock, payload):
    data = pickle.dumps(payload, protocol=pickle.HIGHEST_PROTOCOL)
    header = struct.pack("!I", len(data))
    sock.sendall(header + data)


def _recv_exact(sock, size):
    chunks = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _recv_packet(sock):
    header = _recv_exact(sock, 4)
    if not header:
        return None
    length = struct.unpack("!I", header)[0]
    if length <= 0:
        return None
    body = _recv_exact(sock, length)
    if body is None:
        return None
    return pickle.loads(body)


class NetworkHost:
    def __init__(self, bind_host, port, max_remote_players=3):
        self.bind_host = bind_host
        self.port = int(port)
        self.max_remote_players = max(1, int(max_remote_players))
        self.server_sock = None
        self.clients = {}  # player_index -> socket
        self.running = False
        self.input_states = {}
        self._lock = threading.Lock()
        self._accept_thread = None
        self._recv_threads = []

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.bind_host, self.port))
        self.server_sock.listen(8)
        self.server_sock.settimeout(0.5)
        self.running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()

    def stop(self):
        self.running = False
        with self._lock:
            sockets = list(self.clients.values())
            self.clients.clear()
            self.input_states.clear()
        for sock in sockets + [self.server_sock]:
            try:
                if sock:
                    sock.close()
            except OSError:
                pass

    def has_client(self, player_index):
        with self._lock:
            return int(player_index) in self.clients

    def _accept_loop(self):
        while self.running:
            try:
                client, _addr = self.server_sock.accept()
                client.settimeout(1.0)
                recv_thread = threading.Thread(target=self._recv_loop, args=(client,), daemon=True)
                self._recv_threads.append(recv_thread)
                recv_thread.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _recv_loop(self, sock):
        player_index = None
        try:
            join_msg = _recv_packet(sock)
            if not join_msg or join_msg.get("type") != "join":
                return
            requested_index = int(join_msg.get("player_index", 1))
            if requested_index < 1 or requested_index > self.max_remote_players:
                return
            player_index = requested_index
            with self._lock:
                previous = self.clients.get(player_index)
                if previous:
                    try:
                        previous.close()
                    except OSError:
                        pass
                self.clients[player_index] = sock
                self.input_states[player_index] = {}
        except (OSError, EOFError, pickle.UnpicklingError, ValueError):
            return

        while self.running:
            try:
                msg = _recv_packet(sock)
                if msg is None:
                    break
                if msg.get("type") == "input":
                    input_state = msg.get("input", {}) or {}
                    with self._lock:
                        if self.clients.get(player_index) is sock:
                            self.input_states[player_index] = input_state
            except socket.timeout:
                continue
            except (OSError, EOFError, pickle.UnpicklingError):
                break

        with self._lock:
            try:
                sock.close()
            except OSError:
                pass
            if player_index is not None and self.clients.get(player_index) is sock:
                self.clients.pop(player_index, None)
                self.input_states[player_index] = {}

    def get_player_input(self, player_index):
        with self._lock:
            return dict(self.input_states.get(player_index, {}))

    def send_frame(self, screen_surface, pygame_module):
        with self._lock:
            client_items = list(self.clients.items())
        if not client_items:
            return

        w, h = screen_surface.get_size()
        raw = pygame_module.image.tobytes(screen_surface, "RGB")
        packed = zlib.compress(raw, 1)
        payload = {"type": "frame", "w": w, "h": h, "data": packed}
        disconnected = []

        for player_index, sock in client_items:
            try:
                _send_packet(sock, payload)
            except OSError:
                disconnected.append((player_index, sock))

        if not disconnected:
            return

        with self._lock:
            for player_index, sock in disconnected:
                if self.clients.get(player_index) is sock:
                    self.clients.pop(player_index, None)
                    self.input_states[player_index] = {}
                try:
                    sock.close()
                except OSError:
                    pass


class NetworkClient:
    def __init__(self, host, port, player_index):
        self.host = host
        self.port = int(port)
        self.player_index = int(player_index)
        self.sock = None
        self.running = False
        self.frames = queue.Queue(maxsize=2)
        self._recv_thread = None

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
        self.sock.settimeout(1.0)
        _send_packet(self.sock, {"type": "join", "player_index": self.player_index})
        self.running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()

    def close(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                msg = _recv_packet(self.sock)
                if msg is None:
                    break
                if msg.get("type") == "frame":
                    if self.frames.full():
                        try:
                            self.frames.get_nowait()
                        except queue.Empty:
                            pass
                    self.frames.put_nowait(msg)
            except socket.timeout:
                continue
            except (OSError, EOFError, pickle.UnpicklingError, queue.Full):
                break
        self.running = False

    def send_input(self, input_state):
        if not self.sock or not self.running:
            return
        try:
            _send_packet(
                self.sock,
                {"type": "input", "input": dict(input_state)},
            )
        except OSError:
            self.running = False

    def get_latest_frame(self):
        latest = None
        while not self.frames.empty():
            try:
                latest = self.frames.get_nowait()
            except queue.Empty:
                break
        return latest
