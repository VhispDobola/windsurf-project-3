"""
LAN synchronization helpers.

Security note:
- This module now uses a bounded JSON + binary payload protocol.
- It intentionally avoids pickle for network packets.
"""

import json
import queue
import socket
import struct
import threading
import time
import zlib

PROTOCOL_VERSION = 2

MAX_JSON_BYTES = 64 * 1024
MAX_BLOB_BYTES = 16 * 1024 * 1024


def _send_message(sock, message, blob=b""):
    msg_bytes = json.dumps(message, separators=(",", ":")).encode("utf-8")
    header = struct.pack("!II", len(msg_bytes), len(blob))
    sock.sendall(header + msg_bytes + blob)
    return len(header) + len(msg_bytes) + len(blob)


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


def _recv_message(sock):
    header = _recv_exact(sock, 8)
    if not header:
        return None, None
    msg_len, blob_len = struct.unpack("!II", header)
    if msg_len <= 0 or msg_len > MAX_JSON_BYTES:
        raise ValueError("invalid message length")
    if blob_len < 0 or blob_len > MAX_BLOB_BYTES:
        raise ValueError("invalid blob length")
    msg_raw = _recv_exact(sock, msg_len)
    if msg_raw is None:
        return None, None
    blob = b""
    if blob_len > 0:
        blob = _recv_exact(sock, blob_len)
        if blob is None:
            return None, None
    message = json.loads(msg_raw.decode("utf-8"))
    if not isinstance(message, dict):
        raise ValueError("message must be a dict")
    return message, blob


class NetworkHost:
    def __init__(
        self,
        bind_host,
        port,
        max_remote_players=3,
        stream_fps=30,
        sync_mode="frame",
        zlib_level=1,
    ):
        self.bind_host = bind_host
        self.port = int(port)
        self.max_remote_players = max(1, int(max_remote_players))
        self.stream_fps = max(5, int(stream_fps))
        self.sync_mode = "state" if str(sync_mode).lower() == "state" else "frame"
        self.zlib_level = max(1, min(9, int(zlib_level)))

        self.server_sock = None
        self.clients = {}  # player_index -> info
        self.running = False
        self.input_states = {}
        self._lock = threading.Lock()
        self._accept_thread = None
        self._maintenance_thread = None
        self._recv_threads = []
        self._last_frame_sent_ts = 0.0

        self.heartbeat_interval = 1.0
        self.client_timeout_seconds = 8.0
        self.input_min_interval = 1.0 / 120.0

    def start(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind((self.bind_host, self.port))
        self.server_sock.listen(8)
        self.server_sock.settimeout(0.5)
        self.running = True
        self._accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self._accept_thread.start()
        self._maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._maintenance_thread.start()

    def stop(self):
        self.running = False
        with self._lock:
            sockets = [info["sock"] for info in self.clients.values()]
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

    def get_connected_player_indices(self):
        with self._lock:
            return sorted(self.clients.keys())

    def get_player_input(self, player_index):
        with self._lock:
            return dict(self.input_states.get(player_index, {}))

    def get_lobby_state(self):
        with self._lock:
            return {
                idx: {
                    "ready": bool(info.get("ready", False)),
                    "ping_ms": int(info.get("ping_ms", 0)),
                }
                for idx, info in self.clients.items()
            }

    def all_connected_ready(self):
        with self._lock:
            if not self.clients:
                return True
            return all(bool(info.get("ready", False)) for info in self.clients.values())

    def get_stats(self):
        with self._lock:
            return {
                idx: {
                    "ping_ms": int(info.get("ping_ms", 0)),
                    "bytes_in": int(info.get("bytes_in", 0)),
                    "bytes_out": int(info.get("bytes_out", 0)),
                    "ready": bool(info.get("ready", False)),
                }
                for idx, info in self.clients.items()
            }

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

    def _find_free_slot(self):
        for idx in range(1, self.max_remote_players + 1):
            if idx not in self.clients:
                return idx
        return None

    def _recv_loop(self, sock):
        player_index = None
        try:
            join_msg, _blob = _recv_message(sock)
            if not join_msg or join_msg.get("type") != "join":
                _send_message(sock, {"type": "join_ack", "ok": False, "reason": "invalid join packet", "version": PROTOCOL_VERSION})
                raise ValueError("invalid join packet")
            client_version = int(join_msg.get("version", 0))
            if client_version != PROTOCOL_VERSION:
                _send_message(
                    sock,
                    {
                        "type": "join_ack",
                        "ok": False,
                        "reason": "protocol version mismatch",
                        "version": PROTOCOL_VERSION,
                    },
                )
                raise ValueError("protocol version mismatch")

            requested_index = int(join_msg.get("player_index", 0))
            with self._lock:
                if requested_index <= 0:
                    requested_index = self._find_free_slot() or 0
                if requested_index < 1 or requested_index > self.max_remote_players:
                    _send_message(
                        sock,
                        {
                            "type": "join_ack",
                            "ok": False,
                            "reason": "no available player slots",
                            "version": PROTOCOL_VERSION,
                        },
                    )
                    raise ValueError("no available player slots")
                previous = self.clients.get(requested_index)
                if previous:
                    try:
                        previous["sock"].close()
                    except OSError:
                        pass
                now = time.time()
                self.clients[requested_index] = {
                    "sock": sock,
                    "ready": False,
                    "last_seen": now,
                    "last_input_ts": 0.0,
                    "ping_ms": 0,
                    "bytes_in": 0,
                    "bytes_out": 0,
                    "last_crc": None,
                }
                self.input_states[requested_index] = {}
                player_index = requested_index

            _send_message(
                sock,
                {
                    "type": "join_ack",
                    "ok": True,
                    "player_index": player_index,
                    "player_slot": player_index + 1,
                    "version": PROTOCOL_VERSION,
                    "sync_mode": self.sync_mode,
                },
            )
        except (OSError, EOFError, json.JSONDecodeError, ValueError, struct.error):
            pass

        try:
            while self.running and player_index is not None:
                try:
                    msg, blob = _recv_message(sock)
                    if msg is None:
                        break
                    now = time.time()
                    with self._lock:
                        info = self.clients.get(player_index)
                        if not info or info["sock"] is not sock:
                            break
                        info["last_seen"] = now
                        info["bytes_in"] += len(blob or b"")

                    msg_type = msg.get("type")
                    if msg_type == "input":
                        input_state = msg.get("input", {}) or {}
                        if not isinstance(input_state, dict):
                            continue
                        filtered = {
                            "left": bool(input_state.get("left", False)),
                            "right": bool(input_state.get("right", False)),
                            "up": bool(input_state.get("up", False)),
                            "down": bool(input_state.get("down", False)),
                            "dash": bool(input_state.get("dash", False)),
                            "shoot": bool(input_state.get("shoot", False)),
                        }
                        with self._lock:
                            info = self.clients.get(player_index)
                            if not info:
                                continue
                            if now - info["last_input_ts"] >= self.input_min_interval:
                                self.input_states[player_index] = filtered
                                info["last_input_ts"] = now
                    elif msg_type == "ready":
                        ready_flag = bool(msg.get("ready", False))
                        with self._lock:
                            info = self.clients.get(player_index)
                            if info:
                                info["ready"] = ready_flag
                    elif msg_type == "ping":
                        ts = float(msg.get("ts", now))
                        _send_message(sock, {"type": "pong", "ts": ts})
                    elif msg_type == "heartbeat_ack":
                        sent_ts = float(msg.get("sent_ts", now))
                        ping_ms = max(0, int((now - sent_ts) * 1000))
                        with self._lock:
                            info = self.clients.get(player_index)
                            if info:
                                info["ping_ms"] = ping_ms
                except socket.timeout:
                    continue
                except (OSError, EOFError, json.JSONDecodeError, ValueError, struct.error):
                    break
        finally:
            try:
                sock.close()
            except OSError:
                pass
            with self._lock:
                info = self.clients.get(player_index) if player_index is not None else None
                if info and info.get("sock") is sock:
                    self.clients.pop(player_index, None)
                    self.input_states[player_index] = {}

    def _maintenance_loop(self):
        while self.running:
            now = time.time()
            stale = []
            with self._lock:
                client_items = list(self.clients.items())
            for player_index, info in client_items:
                sock = info["sock"]
                last_seen = float(info.get("last_seen", now))
                if now - last_seen > self.client_timeout_seconds:
                    stale.append((player_index, sock))
                    continue
                try:
                    sent_ts = time.time()
                    sent_bytes = _send_message(
                        sock,
                        {
                            "type": "heartbeat",
                            "sent_ts": sent_ts,
                            "server_time": now,
                            "lobby": self.get_lobby_state(),
                        },
                    )
                    with self._lock:
                        live = self.clients.get(player_index)
                        if live and live["sock"] is sock:
                            live["bytes_out"] += int(sent_bytes)
                except OSError:
                    stale.append((player_index, sock))

<<<<<<< HEAD
            if stale:
                with self._lock:
                    for player_index, sock in stale:
                        info = self.clients.get(player_index)
                        if info and info["sock"] is sock:
                            self.clients.pop(player_index, None)
                            self.input_states[player_index] = {}
                        try:
                            sock.close()
                        except OSError:
                            pass
            time.sleep(self.heartbeat_interval)

    def _send_to_clients(self, message, blob=b""):
        disconnected = []
=======
        def get_connected_player_indices(self):
        with self._lock:
            return sorted(self.clients.keys())

    def send_frame(self, screen_surface, pygame_module):
>>>>>>> 1afbd43416aae4bc928e1581948626bf5e3fd3e7
        with self._lock:
            items = list(self.clients.items())
        for player_index, info in items:
            sock = info["sock"]
            try:
                sent_bytes = _send_message(sock, message, blob)
                with self._lock:
                    active = self.clients.get(player_index)
                    if active and active["sock"] is sock:
                        active["bytes_out"] += int(sent_bytes)
            except OSError:
                disconnected.append((player_index, sock))
        if disconnected:
            with self._lock:
                for player_index, sock in disconnected:
                    info = self.clients.get(player_index)
                    if info and info["sock"] is sock:
                        self.clients.pop(player_index, None)
                        self.input_states[player_index] = {}
                    try:
                        sock.close()
                    except OSError:
                        pass

    def send_frame(self, screen_surface, pygame_module, world_state=None):
        with self._lock:
            has_clients = bool(self.clients)
        if not has_clients:
            return

        now = time.time()
        min_interval = 1.0 / float(self.stream_fps)
        if now - self._last_frame_sent_ts < min_interval:
            return
        self._last_frame_sent_ts = now

        if self.sync_mode == "state":
            self._send_to_clients({"type": "state", "state": world_state or {}, "server_time": now})
            return

        w, h = screen_surface.get_size()
        raw = pygame_module.image.tobytes(screen_surface, "RGB")
        crc = int(zlib.crc32(raw) & 0xFFFFFFFF)
        packed = zlib.compress(raw, self.zlib_level)
        self._send_to_clients(
            {"type": "frame", "w": w, "h": h, "crc": crc, "encoding": "zlib-rgb", "server_time": now},
            packed,
        )


class NetworkClient:
    def __init__(self, host, port, player_index):
        self.host = host
        self.port = int(port)
        self.requested_player_index = int(player_index)
        self.assigned_player_index = None
        self.assigned_player_slot = None
        self.sync_mode = "frame"
        self.sock = None
        self.running = False
        self.updates = queue.Queue(maxsize=4)
        self._recv_thread = None
        self._maintenance_thread = None
        self.ping_ms = 0
        self.bytes_in = 0
        self.bytes_out = 0
        self.lobby = {}
        self._lock = threading.Lock()
        self._last_ping_sent = 0.0

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=5.0)
        self.sock.settimeout(1.0)
        join_msg = {
            "type": "join",
            "player_index": self.requested_player_index,
            "version": PROTOCOL_VERSION,
        }
        _send_message(self.sock, join_msg)
        msg, _blob = _recv_message(self.sock)
        if not msg or msg.get("type") != "join_ack":
            raise OSError("missing join acknowledgment from host")
        if not msg.get("ok", False):
            raise OSError(msg.get("reason", "host rejected connection"))
        self.assigned_player_index = int(msg.get("player_index", self.requested_player_index))
        self.assigned_player_slot = int(msg.get("player_slot", self.assigned_player_index + 1))
        self.sync_mode = str(msg.get("sync_mode", "frame")).lower()
        self.running = True
        self._recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self._recv_thread.start()
        self._maintenance_thread = threading.Thread(target=self._maintenance_loop, daemon=True)
        self._maintenance_thread.start()

    def close(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except OSError:
            pass

    def set_ready(self, ready):
        if not self.sock or not self.running:
            return
        try:
            sent_bytes = _send_message(self.sock, {"type": "ready", "ready": bool(ready)})
            with self._lock:
                self.bytes_out += int(sent_bytes)
        except OSError:
            self.running = False

    def _recv_loop(self):
        while self.running and self.sock:
            try:
                msg, blob = _recv_message(self.sock)
                if msg is None:
                    break
                msg_type = msg.get("type")
                if msg_type == "pong":
                    now = time.time()
                    sent = float(msg.get("ts", now))
                    with self._lock:
                        self.ping_ms = max(0, int((now - sent) * 1000))
                elif msg_type == "heartbeat":
                    sent_ts = float(msg.get("sent_ts", time.time()))
                    with self._lock:
                        self.lobby = msg.get("lobby", {}) or {}
                    try:
                        sent_bytes = _send_message(self.sock, {"type": "heartbeat_ack", "sent_ts": sent_ts})
                        with self._lock:
                            self.bytes_out += int(sent_bytes)
                    except OSError:
                        self.running = False
                elif msg_type in ("frame", "state"):
                    payload = dict(msg)
                    if blob:
                        payload["data"] = blob
                        with self._lock:
                            self.bytes_in += len(blob)
                    if self.updates.full():
                        try:
                            self.updates.get_nowait()
                        except queue.Empty:
                            pass
                    self.updates.put_nowait(payload)
            except socket.timeout:
                continue
            except (OSError, EOFError, json.JSONDecodeError, ValueError, struct.error, queue.Full):
                break
        self.running = False

    def _maintenance_loop(self):
        while self.running and self.sock:
            now = time.time()
            if now - self._last_ping_sent >= 1.0:
                self._last_ping_sent = now
                try:
                    sent_bytes = _send_message(self.sock, {"type": "ping", "ts": now})
                    with self._lock:
                        self.bytes_out += int(sent_bytes)
                except OSError:
                    self.running = False
                    break
            time.sleep(0.2)

    def send_input(self, input_state):
        if not self.sock or not self.running:
            return
        safe_input = {
            "left": bool(input_state.get("left", False)),
            "right": bool(input_state.get("right", False)),
            "up": bool(input_state.get("up", False)),
            "down": bool(input_state.get("down", False)),
            "dash": bool(input_state.get("dash", False)),
            "shoot": bool(input_state.get("shoot", False)),
        }
        try:
            sent_bytes = _send_message(self.sock, {"type": "input", "input": safe_input})
            with self._lock:
                self.bytes_out += int(sent_bytes)
        except OSError:
            self.running = False

    def get_latest_update(self):
        latest = None
        while not self.updates.empty():
            try:
                latest = self.updates.get_nowait()
            except queue.Empty:
                break
        return latest

    def get_status(self):
        with self._lock:
            return {
                "ping_ms": int(self.ping_ms),
                "bytes_in": int(self.bytes_in),
                "bytes_out": int(self.bytes_out),
                "lobby": dict(self.lobby),
                "assigned_player_slot": self.assigned_player_slot,
                "sync_mode": self.sync_mode,
            }
