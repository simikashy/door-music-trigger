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

2. **Register an OAuth SmartApp** (one time — gives durable, auto-refreshing
   tokens). Install the SmartThings CLI (https://github.com/SmartThingsCommunity/smartthings-cli),
   then:
   ```
   smartthings apps:create
   ```
   - Choose **OAuth-In Only**.
   - Display name: anything (e.g. "Door Music Trigger").
   - Scopes: `r:devices:*`.
   - Redirect URI: `http://localhost:8910/callback`.

   It prints a **Client ID** and **Client Secret** — copy both. (You can also do
   this in the SmartThings Developer Workspace if you prefer a web UI.)

   > Quick test alternative: instead of OAuth you can paste a Personal Access
   > Token into `[smartthings] token` in config.ini. ⚠️ New PATs expire after
   > ~24h — fine to verify things work, not for daily use.

3. **Create your config:** copy `config.example.ini` to `config.ini` and fill in
   the `[oauth]` client_id and client_secret, the MediaMonkey path, and your
   playlist path. Leave device_id for the next step.

4. **Authorize once** (opens your browser; log in and approve):
   ```
   python authorize.py
   ```
   This saves auto-refreshing tokens to `tokens.json`. You won't run it again
   unless the PC stays offline for ~30 days (refresh-token lifetime).

5. **Find your door sensor's device ID** and put it in config.ini:
   ```
   python list_devices.py "$(python -c "import json;print(json.load(open('tokens.json'))['access_token'])")"
   ```
   (Or just run `python list_devices.py YOUR_PAT` if you used a static token.)
   Copy the deviceId next to your door sensor into `[smartthings] device_id`.

6. **Test connectivity** (single poll, prints current door state, then exits):
   ```
   python door_music_trigger.py --once
   ```
   The log should show "Initial door state: open" or "closed".

7. **Run it:**
   ```
   python door_music_trigger.py
   ```
   Close the door — music should start. Activity is written to
   `door_music_trigger.log`. Tokens refresh silently in the background.

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
