# Door Sensor → MediaMonkey Music Trigger

When your SmartThings door sensor closes, your Windows PC starts playing music in
MediaMonkey. The PC polls SmartThings' public API and launches MediaMonkey on each
open → closed transition. Nothing is pushed to the PC; it's never exposed to the
internet; Alexa is not involved.

See the full design in
`docs/superpowers/specs/2026-06-23-door-sensor-music-trigger-design.md`.

## Setup (on the Windows PC)

1. **Install Python 3.10+** (python.org) and the dependency:
   ```
   pip install -r requirements.txt
   ```

2. **Get a SmartThings token.**
   - Quick/testing: create a Personal Access Token at
     https://account.smartthings.com/tokens with the *Devices: read* scope.
     ⚠️ Newly-created personal tokens may expire after ~24h — fine for testing,
     not for daily use.
   - Durable (recommended for everyday use): set up a small OAuth SmartApp so the
     token auto-refreshes. This is the one piece that takes extra time; ask and
     I'll walk you through it (or we add a refresh step to the script).

3. **Find your door sensor's device ID:**
   ```
   python list_devices.py YOUR_TOKEN
   ```
   Copy the deviceId next to your door sensor.

4. **Create your config:** copy `config.example.ini` to `config.ini` and fill in
   the token, device_id, the MediaMonkey path, and your playlist path.

5. **Test connectivity** (single poll, prints current door state, then exits):
   ```
   python door_music_trigger.py --once
   ```
   The log should show "Initial door state: open" or "closed".

6. **Run it:**
   ```
   python door_music_trigger.py
   ```
   Close the door — music should start. Activity is written to
   `door_music_trigger.log`.

## Run automatically at startup (optional)

Create a shortcut to `pythonw door_music_trigger.py` in your Startup folder
(`Win+R` → `shell:startup`), or set up a Task Scheduler task that runs at logon.
`pythonw` runs it without a console window.

## Tests

Pure logic (no network/PC needed):
```
python test_logic.py
```

## Notes / limits

- **Start-only:** music starts on close; stop it manually.
- **What plays** is whatever's in the configured `.m3u` playlist — edit it in
  MediaMonkey, no code changes.
- **Delay:** up to `poll_interval` seconds (default 3) between close and playback.
