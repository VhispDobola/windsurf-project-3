import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.network_sync import NetworkClient, NetworkHost


def main():
    port = 50123
    host = NetworkHost("127.0.0.1", port, max_remote_players=3, stream_fps=20, sync_mode="state")
    host.start()

    clients = []
    try:
        for idx in range(3):
            client = NetworkClient(
                "127.0.0.1",
                port,
                player_index=0,
                profile={
                    "username": f"Client{idx + 1}",
                    "color": [40 + idx * 20, 120, 200],
                    "hat": "Cap",
                },
            )  # auto slot
            client.connect()
            client.set_ready(True)
            clients.append(client)

        time.sleep(0.5)

        slots = host.get_connected_player_indices()
        assert len(slots) == 3, f"Expected 3 clients, got {slots}"
        assert host.all_connected_ready(), "Expected all connected clients to be ready"
        lobby = host.get_lobby_state()
        first_slot = min(slots)
        assert lobby[first_slot].get("profile", {}).get("username") == "Client1", lobby

        clients[0].send_input(
            {
                "left": True,
                "right": False,
                "up": False,
                "down": False,
                "dash": False,
                "shoot": True,
            }
        )
        time.sleep(0.1)

        input_state = host.get_player_input(first_slot)
        assert input_state.get("left") is True, f"Input not propagated for slot {first_slot}: {input_state}"
        assert input_state.get("shoot") is True, f"Shoot not propagated for slot {first_slot}: {input_state}"
        print("LAN smoke test passed")
    finally:
        for client in clients:
            client.close()
        host.stop()


if __name__ == "__main__":
    main()
