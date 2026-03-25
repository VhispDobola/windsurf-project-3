# Boss Rush Game - Setup and Development Guide

## Quick Start

### Recommended for Windows players

1. Clone or download the repository.
2. Run `RUN_GAME.bat`.
3. Use the in-game menu:
   - `Space` for normal play
   - `H` to host a lobby
   - `J` to join a lobby

The Windows launcher calls `launch_windows.ps1`, which:
- detects Python 3.10+
- installs Python with `winget` if possible
- installs packages from `requirements.txt`
- starts the correct game mode

### Manual prerequisites
- Windows 10 or 11
- Python 3.10 or higher
- Git if you want to clone instead of downloading a ZIP

### Manual installation
1. Clone the repository:
```bash
git clone <repository-url>
cd BossFight
```

2. Install dependencies:
```bash
python -m pip install -r requirements.txt --user
```

3. Run the game:
```bash
python main.py
```

## Development Setup

### Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### IDE Configuration
- Use VS Code with the Python extension.
- Point the interpreter at your virtual environment.
- Use the batch launchers for quick Windows smoke tests.

## Project Structure

```text
BossFight/
|-- main.py
|-- requirements.txt
|-- README.md
|-- docs/
|-- launch_windows.ps1
|-- RUN_GAME.bat
|-- config/
|-- core/
|-- bosses/
|-- ui/
|-- utils/
|-- assets/
`-- data/
```

## Testing

```bash
python tests/lan_smoke_test.py
python -c "from config.constants import *; print('Config OK')"
python -c "from core import *; from bosses import *; print('Imports OK')"
```

## Multiplayer Notes

- Host mode listens on TCP port `50000` by default.
- Players on the same LAN should connect to the host's IPv4 address.
- Players across the internet should use a VPN mesh or port forwarding.
- All players should use the same repository revision.
- The regular main menu now includes both host and join flows.

## Troubleshooting

**Game will not start**
- Confirm Python 3.10+ is installed.
- Rerun the launcher with internet access so dependencies can install.
- Check that the repository was fully extracted and assets are present.

**Another player cannot join**
- Confirm the host shared the correct IP address.
- Allow Python through Windows Firewall on the host machine.
- Make sure all players use the same port, default `50000`.
- For internet play, use a VPN mesh or configure port forwarding.

**Audio problems**
- Check that the machine has a working audio device.
- The game will continue running if optional sounds are missing.
