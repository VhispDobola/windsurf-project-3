# Boss Rush Game

Boss Rush is a local co-op bullet-hell boss game built with Python and Pygame. This repo is now set up so a new Windows player can download it from GitHub, run a launcher, have Python dependencies installed automatically, and start either solo play or host or join multiplayer.

## Windows Quick Start

1. Download this repo as a ZIP from GitHub, or clone it:
   ```powershell
   git clone <repo-url>
   cd windsurf-project-3
   ```
2. Double-click `RUN_GAME.bat`.
3. In the main menu:
   - `Space` starts normal play
   - `H` hosts a multiplayer lobby
   - `J` opens the join screen

The launcher will:
- detect Python 3.10+
- try to install Python 3.12 with `winget` if Python is missing
- install packages from `requirements.txt`
- start the game in the selected mode

## Multiplayer

The game supports 1 host and up to 3 remote players.

### Same Wi-Fi or LAN

1. One player opens the game and presses `H` to host a lobby.
2. The host shares the IP address and port.
3. Other players open the game, press `J`, and enter the host IP and port.
4. If Windows Firewall prompts for Python access, allow it on Private networks.

Default port: `50000`

### Over the internet

The networking code already supports direct socket connections. The simplest ways to use it outside the local network are:

- use a VPN mesh such as Tailscale, ZeroTier, or Radmin VPN, then connect to the host's VPN IP
- or port-forward TCP `50000` on the host router and connect to the host's public IP

Every player must be on the same game version.

## Manual Setup

If you do not want to use the launchers:

```powershell
python -m pip install -r requirements.txt --user
python main.py
```

Host mode:

```powershell
$env:BOSS_RUSH_NETWORK_MODE="host"
$env:BOSS_RUSH_HOST="0.0.0.0"
$env:BOSS_RUSH_PORT="50000"
python main.py
```

Client mode:

```powershell
$env:BOSS_RUSH_NETWORK_MODE="client"
$env:BOSS_RUSH_HOST="192.168.1.20"
$env:BOSS_RUSH_PORT="50000"
$env:BOSS_RUSH_PLAYER_SLOT="auto"
python main.py
```

## Requirements

- Windows 10 or 11
- internet access on first run to install Python packages
- Python 3.10+ if `winget` is unavailable

Python dependencies:
- `pygame==2.5.2`
- `pytest>=8.0,<9.0`

## Troubleshooting

- If Python install fails, install Python 3.12 manually from python.org and rerun the launcher.
- If clients cannot connect, verify the host IP, port, and Windows Firewall prompt.
- If internet play fails, use a VPN mesh or configure port forwarding. Most home networks will block unsolicited inbound traffic by default.

## Docs

- `docs/SETUP_GUIDE.md`
- `docs/LAN_QUICKSTART.md`
- `docs/ONLINE_PLAY.md`
- `docs/CODING_STANDARDS.md`
