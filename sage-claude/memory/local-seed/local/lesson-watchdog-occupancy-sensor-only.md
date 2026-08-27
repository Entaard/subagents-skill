---
id: lesson-watchdog-occupancy-sensor-only
kind: lesson
class: local
count: 1
first: 2026-08-18
last: 2026-08-18
contradicts: —
promoted: —
status: watching
---

The watchdog is an occupancy sensor and sends nothing. Its six per-unit rungs were measured and cut: **0 true positives** across 193 subagent transcripts and 37 units in 4 real runs. What survives is `--status` arithmetic plus the **one** parent-occupancy rung — `occ-30pct`, the handover alarm — notify-only. One, deliberately: there is nothing above it, because a supervising parent has no action left to take on its own occupancy.
