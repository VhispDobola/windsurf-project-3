# Boss Difficulty Profile

This table documents the manual phase/stage tuning currently applied to spike-prone bosses.
Values are in frames (60 FPS) unless noted.
Source of truth: `config/boss_difficulty_profiles.json` (with in-code fallback defaults).

| Boss | Phase/Stage | Attack Timing Profile | Damage Profile |
|---|---|---|---|
| Ice Tyrant | Phase 1 | `blizzard=180`, `spire=220`, `wall=240`, `shatter=260` | `damage_scale=0.90`, `aura=6` |
| Ice Tyrant | Phase 2 | `blizzard=150`, `spire=190`, `wall=200`, `shatter=250` | `damage_scale=0.93`, `aura=7` |
| Ice Tyrant | Phase 3 | `blizzard=120`, `spire=160`, `wall=165`, `shatter=210` | `damage_scale=0.96`, `aura=8` |
| Magma Sovereign | Phase 1 | `bomb=115`, `geyser=155`, `rain=190`, `heat_wave=235` | `damage_scale=0.90` |
| Magma Sovereign | Phase 2 | `tracking=82`, `wall=130`, `chain=102` | `damage_scale=0.94` |
| Magma Sovereign | Phase 3 | `vortex=170`, `cascade=195`, `tsunami=215`, `inferno=320` | `damage_scale=0.97` |
| Nexus Core | Phase 1 | `spiral=60`, `aimed=120` | `burst: count=4, dmg=8, speed=5.6` |
| Nexus Core | Phase 2 | `spiral=50`, `aimed=98`, `pulse=138` | `burst: count=6, dmg=9`; `pulse: dmg=10` |
| Nexus Core | Phase 3 | `spiral=34`, `aimed=78`, `pulse=112` | `burst: count=8, dmg=10`; `pulse: dmg=11` |
| Cyber Overlord | Stage 1 | `drone_cd=130` | unchanged per-projectile damage |
| Cyber Overlord | Stage 2 | `laser_cd=112`, `predict_strike_delay=34` | unchanged per-projectile damage |
| Cyber Overlord | Stage 3 | `glitch_cd=205`, `glitch_count=24` | unchanged per-projectile damage |

## Notes

- These profiles are intentionally conservative so they stack safely with auto-balance.
- Auto-balance and log-driven tuning still apply on top of these values.
- If fights become too easy after enough logged sessions, reduce cooldowns before raising raw damage.
