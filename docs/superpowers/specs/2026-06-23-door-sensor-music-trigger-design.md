# Door Sensor → PC Music Trigger — Design

**Date:** 2026-06-23
**Status:** Approved design, ready for implementation planning

## Summary

When a SmartThings multipurpose contact sensor on a door registers a **close**
event, a Windows PC on the local network starts playing music in **MediaMonkey**.

The PC reaches *out* to the SmartThings public REST API and **polls** the door
sensor's state. On an open → closed transition, it launches MediaMonkey with a
configured playlist. Nothing is pushed to the PC; the PC is never exposed to the
internet; Alexa is not in the loop at all.

## Goals

- Door closes → music starts playing in MediaMonkey on the Windows PC.
- No inbound network exposure (no port forwarding, no tunnels).
- No reliance on SmartThings/Alexa push integrations or local-device discovery.
- Easy to reconfigure (token, device, playlist) without code changes.

## Non-Goals (YAGNI)

- No stop/pause/timer logic. The trigger is **start-only**; the user stops music
  manually.
- No control of music selection from the sensor — *what* plays is governed by the
  configured playlist file, not the code.
- No multi-device, multi-sensor, or multi-action support.
- No GUI.

## Why This Avoids the Previous EventGhost Failure

A prior attempt with EventGhost failed because it depended on a **push/plugin
model** — SmartThings or Alexa had to recognize EventGhost and send events to it
via plugins, IFTTT bridges, or local discovery. Those integrations are brittle and
frequently deprecated.

This design inverts the direction: the PC is an ordinary authenticated **API
client** that pulls state from `api.smartthings.com`, the same documented endpoint
the SmartThings app uses. Nothing has to discover or integrate with the PC, and
Alexa is removed from the chain entirely. The previous failure mode does not apply.

## Architecture / Data Flow

```
SmartThings Cloud  ──(REST API: device status)──►  Polling script on PC
   (door sensor)         every ~3 seconds              (Python, runs at startup)
                                                              │
                                          detects open ➜ closed transition
                                                              │
                                                              ▼
                                          launches MediaMonkey with playlist
```

A single small Python script runs in the background on the Windows PC. On a loop it
queries the SmartThings API for the door sensor's `contactSensor` state, remembers
the previous state, and fires **only on an open → closed edge** — once per close,
never repeatedly while the door stays shut.

## Components

### 1. Polling Loop
- Calls the SmartThings device-status API every `poll_interval` seconds (default 3).
- Parses the `contactSensor.contact.value` field (`"open"` / `"closed"`).
- Maintains `previous_state` in memory to detect transitions.

### 2. Edge Detector / State Machine
- Fires the trigger **only** when `previous_state == "open"` and
  `current_state == "closed"`.
- `closed → closed` does nothing (prevents re-launching every poll).
- `closed → open` and `open → open` do nothing.
- On startup, the first observed state seeds `previous_state` without firing.

### 3. MediaMonkey Launcher
- On a qualifying edge, runs:
  ```
  "C:\Program Files (x86)\MediaMonkey 5\MediaMonkey.exe" "C:\path\to\playlist.m3u"
  ```
- Executable path and playlist path come from config (not hard-coded).
- A playlist (`.m3u`) is passed so the user changes what plays by editing the
  playlist in MediaMonkey — no code changes.
- If MediaMonkey is already running, passing a playlist loads and plays it via its
  normal single-instance behavior.

### 4. Configuration File
A single local config file (`config.ini` or `config.json`) beside the script holds:
- SmartThings token (or OAuth credentials)
- Door sensor device ID
- Poll interval (default 3s)
- MediaMonkey executable path
- Playlist path

No secrets or paths are hard-coded. Normal changes require zero code edits.

## Authentication / Token

The script authenticates to the SmartThings API with a bearer token. Two options,
finalized during implementation:

- **Static Personal Access Token (PAT)** — simplest; one token in the config file.
  Caveat: SmartThings now expires newly-issued PATs after ~24h, so this likely
  suits testing only.
- **OAuth SmartApp token (expected final choice)** — a one-time setup registers a
  small SmartApp, yielding a refresh token the script uses to silently mint fresh
  access tokens indefinitely. ~20 min more setup, then untouched.

The polling logic is identical regardless of token type; only the token-acquisition
and refresh code differs.

## Error Handling

- **No internet / API down:** log, wait, retry on the next loop. Never crash; a
  transient blip is one skipped poll.
- **Auth failure (expired token):** with OAuth, auto-refresh and retry; with a
  static PAT, log a clear "token expired — regenerate" message.
- **Edge-detection guard:** fire only on open→closed; ignore repeats while closed,
  so music never re-launches every few seconds.
- **MediaMonkey launch failure (e.g. wrong path):** catch and log a clear message
  rather than crashing.
- **Logging:** a small rolling log file records each state change and trigger, so
  if music doesn't play the user can see exactly what the script observed.

## Testing Strategy

- **State-machine logic:** unit tests with mocked sensor states — open→closed fires
  once; closed→closed doesn't; startup seeds without firing; etc. No real door
  needed.
- **API parsing:** tested against a saved sample SmartThings API response.
- **MediaMonkey launch:** point config at a test playlist; confirm it plays.
- **End-to-end:** run the script, physically open and close the door, confirm music
  starts exactly once.

## Open Items for Implementation

- Decide PAT vs OAuth SmartApp for the token (expected: OAuth for durability).
- Confirm the exact MediaMonkey executable path on the target PC.
- Confirm the door sensor's SmartThings device ID and the `contactSensor`
  attribute path in the API response.
