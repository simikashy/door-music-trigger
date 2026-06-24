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

## Run automatically at startup

Once `python door_music_trigger.py` works manually, make it start on its own at
every logon — no console window, nothing to launch by hand:

1. Double-click **`install_startup.bat`** in this folder. (If it reports a
   permission error, right-click → *Run as administrator*.)
2. That's it. It registers a Task Scheduler task named **DoorMusicTrigger** that
   runs `start_hidden.vbs` at logon, which launches the trigger with `pythonw`
   (invisible — no black console window).

Useful commands afterward (run in a terminal):
- Start it now without rebooting: `schtasks /Run /TN DoorMusicTrigger`
- Stop the running instance: `schtasks /End /TN DoorMusicTrigger`
- Remove auto-start entirely: `schtasks /Delete /TN DoorMusicTrigger /F`

To confirm it's running, close the door and check the tail of
`door_music_trigger.log`, or open Task Manager → Details and look for `pythonw.exe`.

## What YOU must supply (the placeholders)

The code is complete; these are the real-world values only you have. All of them
live in `config.ini` (except where noted) — nothing else needs editing:

| Value | Where it goes | How to get it |
|-------|---------------|---------------|
| **Client ID / Secret** | `[oauth]` in config.ini | From `smartthings apps:create` (step 2) |
| **tokens.json** | created for you | Produced by running `authorize.py` (step 4) |
| **device_id** | `[smartthings]` in config.ini | From `list_devices.py` — the row for your door sensor (step 5) |
| **MediaMonkey path** | `[mediamonkey] executable_path` | The real path to `MediaMonkey.exe` on your PC |
| **Playlist path** | `[mediamonkey] playlist_path` | A `.m3u` you save from MediaMonkey (see below) |

**Making the playlist:** in MediaMonkey, build the playlist you want, right-click
it → *Send to* → *Playlist file (.m3u)* (or *Export*), and save it somewhere
stable like `C:\Users\you\Music\Playlists\door.m3u`. Put that exact path in
config.ini. To change what plays later, just re-export over that file — no code
or config changes.

**If your sensor isn't a contact sensor** (e.g. a different SmartThings device),
the only code assumption is the attribute path
`components.main.contactSensor.contact.value` in `door_music_trigger.py`. Run
`python door_music_trigger.py --once` — if it logs an "unexpected API response
shape" error, the device reports a different attribute and that one line needs
adjusting. For a standard multipurpose/contact sensor, it works as-is.

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
