# Online Play

Boss Rush supports direct online play using the same built-in multiplayer flow as LAN play.

## Fastest setup

1. Host opens the game and presses `H`.
2. Host shares the address shown in the lobby.
3. Other players open the game, press `J`, enter that address, and connect.

## Best internet options

### VPN mesh

This is the easiest option for most players.

- Tailscale
- ZeroTier
- Radmin VPN

All players join the same VPN network, then clients connect to the host's VPN IP.

### Port forwarding

If the host controls their router:

1. Forward TCP port `50000` to the host PC.
2. Share the host's public IP with other players.
3. Clients connect with that public IP and port `50000`.

## Notes

- Everyone should use the same repository version.
- Windows Firewall must allow Python on the host machine.
- Wired or stable Wi-Fi improves latency.
