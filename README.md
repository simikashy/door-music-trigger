# Door Sensor → Music 🎵

**What this does:** when you close your door, your SmartThings door sensor tells
this program, and the program makes **MediaMonkey** on your Windows laptop start
playing a playlist. That's it — close the door, music plays.

It runs quietly in the background on the laptop. Your phone and Alexa are not
involved, and nothing from the internet can reach into your laptop — the laptop
only ever reaches *out* to ask SmartThings "is the door open or closed?"

> **Note for whoever is setting this up:** the steps below assume no coding
> experience. Just follow them in order, top to bottom. It takes about 20–30
> minutes the first time. Anything in a `grey box` is something you type or run.

---

## ✅ Before you start, make sure you have

- A **Windows laptop** (this runs on the laptop, not your phone).
- Your **door sensor already added** and working in the SmartThings phone app.
- **MediaMonkey installed** on the laptop, with some music/playlist in it.
- Your **SmartThings / Samsung account** email + password (you'll log in once).
- About 20–30 minutes.

---

## Step 1 — Download this project onto the laptop

1. At the top of this GitHub page, click the green **`< > Code`** button.
2. Click **Download ZIP**.
3. Find the downloaded ZIP (usually in your **Downloads** folder), right-click it
   → **Extract All…** → extract it to somewhere easy like your **Desktop**.
4. You now have a folder named **`door-music-trigger`**. Remember where it is.

---

## Step 2 — Install Python (the engine this runs on)

1. Go to **https://www.python.org/downloads/** and click the big
   **Download Python** button.
2. Open the downloaded installer.
3. **VERY IMPORTANT:** at the bottom of the first screen, tick the box that says
   **“Add python.exe to PATH”** before continuing. (If you miss this, later steps
   won't work.)
4. Click **Install Now**, let it finish, then **Close**.

---

## Step 3 — Open a command window inside the folder

This is the black text window you'll type the next commands into.

1. Open the **`door-music-trigger`** folder in File Explorer.
2. Click the **address bar** at the top (where the folder path is shown).
3. Type **`cmd`** and press **Enter**.
4. A black window opens — it's already pointed at the right folder. Keep it open;
   we use it for the next steps.

> Tip: to paste something into this black window, **right-click** inside it.

---

## Step 4 — Install the building blocks

In the black window, type this and press Enter:

```
pip install -r requirements.txt
```

Wait until it finishes (a few lines of text, then it returns to a normal prompt).

---

## Step 5 — Get the SmartThings tool

1. Go to **https://github.com/SmartThingsCommunity/smartthings-cli/releases**.
2. Under the newest release, download the **Windows** file (its name contains
   `win32-x64` and ends in `.zip` or `.msi`).
3. If it's a ZIP: extract it, and copy the **`smartthings.exe`** inside into your
   **`door-music-trigger`** folder. If it's an MSI: just run it to install.

---

## Step 6 — Create your SmartThings connection

In the black window, run:

```
smartthings apps:create
```

(If that says “not recognized”, run `.\smartthings.exe apps:create` instead.)

It will ask a series of questions. Answer them like this (use the **arrow keys**
to move, **Spacebar** to tick a choice, **Enter** to confirm):

| It asks… | What to do |
|----------|------------|
| What kind of app? | Choose **OAuth-In Only** |
| Display Name | Type `Door Music` |
| Description | Type `Plays music when door closes` |
| Icon Image URL | Leave blank, press Enter |
| Target URL | Leave blank, press Enter |
| Scopes | Tick **`r:devices:*`** (Spacebar), then Enter |
| Redirect URI | Type `http://localhost:8910/callback`, press Enter |

When it finishes it prints an **OAuth Client Id** and an **OAuth Client Secret**.
**Copy both** into a temporary note — you'll paste them in the next step. (The
secret is shown only once.)

---

## Step 7 — Fill in your settings file

1. In the folder, find **`config.example.ini`**. Copy it, and rename the copy to
   exactly **`config.ini`**.
2. Open **`config.ini`** with **Notepad** (right-click → Open with → Notepad).
3. Paste your **Client Id** and **Client Secret** into the matching lines under
   `[oauth]`.
4. **Save** the file (Ctrl+S). Leave it open — you'll add two more things soon.

---

## Step 8 — Log in once

In the black window, run:

```
python authorize.py
```

Your web browser opens to SmartThings. **Log in and approve.** The page will say
**“Authorization complete.”** You can close that browser tab.

This quietly creates a file called `tokens.json` — that's what keeps you logged in
from now on. You won't have to do this again.

---

## Step 9 — Find your door sensor's ID

In the black window, run:

```
python list_devices.py
```

It prints a list of your devices and a long ID next to each. Find the row for your
**door sensor** and copy its long ID. In `config.ini`, paste it into the
`device_id =` line. **Save.**

---

## Step 10 — Point it at MediaMonkey and your playlist

1. **MediaMonkey location:** right-click your MediaMonkey desktop shortcut →
   **Properties** → the **Target** box shows the full path (something like
   `C:\Program Files (x86)\MediaMonkey 5\MediaMonkey.exe`). Paste that into the
   `executable_path =` line in `config.ini`.
2. **Playlist:** in MediaMonkey, build the playlist you want to hear. Right-click
   it → **Send to / Export → Playlist file (.m3u)** and save it somewhere easy
   like your Music folder (e.g. `C:\Users\YourName\Music\door.m3u`). Paste that
   path into the `playlist_path =` line in `config.ini`.
3. **Save** `config.ini` and close it.

---

## Step 11 — Test it

First, a quick self-check that catches typos before the real test. In the black
window, run:

```
python selfcheck.py
```

It prints a checklist. Every line should say **`[ OK ]`**. If any line says
**`[ FIX ]`**, it tells you exactly what to fix — do that, then run
`python selfcheck.py` again until everything is OK.

Once it's all OK, run the real connection test:

```
python door_music_trigger.py --once
```

You should see a line like **“Initial door state: closed”** (or open). That means
it's talking to SmartThings correctly. If you see an error, see **Troubleshooting**
below.

Now run it for real:

```
python door_music_trigger.py
```

**Close your door.** Within a few seconds, music should start in MediaMonkey. 🎉
To stop the program in this window, press **Ctrl+C**.

---

## Step 12 — Make it start automatically (so you never touch it again)

In the folder, **double-click `install_startup.bat`**.
(If it shows a permission error, right-click it → **Run as administrator**.)

That's it. From now on, every time the laptop is turned on and logged in, this
starts itself silently in the background. Just close the door and music plays.

---

## 🎶 Everyday use

- **Close the door → music plays.** Nothing else to do.
- **To stop the music:** pause/stop it in MediaMonkey like normal.
- **To change the songs:** edit the playlist in MediaMonkey and export it again
  over the same `.m3u` file. No settings to change.

---

## 🔧 Troubleshooting

Open the file **`door_music_trigger.log`** in the folder and read the last few
lines — it says what happened.

| Problem | Fix |
|---------|-----|
| Not sure what's wrong before testing | Run `python selfcheck.py` — it lists exactly what's missing or mistyped. |
| `python is not recognized` | Python wasn't added to PATH. Reinstall Python (Step 2) and **tick the “Add to PATH” box**. |
| Auth / token error in the log | Run `python authorize.py` again to log back in. |
| `unexpected API response shape` | Your sensor reports a slightly different format. Tell the person who set this up — one line in the code needs a small tweak. |
| Music didn't start, but the log says it triggered | Check `executable_path` and `playlist_path` in `config.ini` are exactly correct. |
| `smartthings is not recognized` | Use `.\smartthings.exe apps:create` (Step 6), and make sure `smartthings.exe` is in this folder. |

---

## 🔒 Your privacy

`config.ini` (your login secrets) and `tokens.json` (your saved login) stay **only
on the laptop**. They are deliberately **not** uploaded to GitHub. Don't share
those two files with anyone.

---

## For the technically curious

- Full design write-up:
  `docs/superpowers/specs/2026-06-23-door-sensor-music-trigger-design.md`
- How it works: a small Python script polls the SmartThings REST API every few
  seconds and launches MediaMonkey on each open→closed transition. OAuth tokens
  refresh themselves automatically.
- Run the logic tests: `python test_logic.py`
