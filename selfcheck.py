"""Pre-flight check: run this before the real test (Step 11).

    python selfcheck.py

It looks at your config.ini and surroundings and prints a plain checklist of
what's ready (OK) and what still needs fixing (FIX), with a hint for each. It
does NOT contact SmartThings or play music -- it just catches typos and missing
pieces early.
"""

from __future__ import annotations

import configparser
from pathlib import Path

OK = "[ OK  ]"
FIX = "[ FIX ]"

PLACEHOLDERS = {
    "PASTE_CLIENT_ID_HERE",
    "PASTE_CLIENT_SECRET_HERE",
    "PASTE_DEVICE_ID_HERE",
    "",
}


def check(label: str, ok: bool, hint: str, results: list) -> bool:
    results.append((ok, label, hint))
    return ok


def main() -> None:
    results: list = []

    # 1. config.ini exists
    cfg_path = Path("config.ini")
    if not check("config.ini exists", cfg_path.exists(),
                 "Copy config.example.ini and rename the copy to config.ini (Step 7).",
                 results):
        _report(results)
        return

    cfg = configparser.ConfigParser()
    cfg.read("config.ini")

    def val(section: str, key: str) -> str:
        if cfg.has_section(section) and cfg.has_option(section, key):
            return cfg.get(section, key).strip()
        return ""

    # 2. Authentication: either OAuth client + tokens.json, or a static token.
    client_id = val("oauth", "client_id")
    using_oauth = client_id not in PLACEHOLDERS
    static_token = val("smartthings", "token")

    if using_oauth:
        check("OAuth Client Id filled in", True, "", results)
        check("OAuth Client Secret filled in",
              val("oauth", "client_secret") not in PLACEHOLDERS,
              "Paste the Client Secret from 'smartthings apps:create' (Step 6-7).",
              results)
        check("Logged in (tokens.json exists)",
              Path(val("oauth", "token_store") or "tokens.json").exists(),
              "Run: python authorize.py  (Step 8).",
              results)
    else:
        check("Authentication configured",
              static_token not in PLACEHOLDERS,
              "Fill in [oauth] client_id/secret (recommended) or a [smartthings] "
              "token. See Steps 6-8.",
              results)

    # 3. Device ID
    check("Door sensor device_id filled in",
          val("smartthings", "device_id") not in PLACEHOLDERS,
          "Run 'python list_devices.py' and paste your door sensor's ID (Step 9).",
          results)

    # 4. MediaMonkey executable
    mm = val("mediamonkey", "executable_path")
    check("MediaMonkey program found",
          bool(mm) and Path(mm).exists(),
          f"executable_path points to a file that doesn't exist: '{mm}'. "
          "Check it via the MediaMonkey shortcut's Properties > Target (Step 10).",
          results)

    # 5. Playlist file
    pl = val("mediamonkey", "playlist_path")
    check("Playlist (.m3u) found",
          bool(pl) and Path(pl).exists(),
          f"playlist_path points to a file that doesn't exist: '{pl}'. "
          "Export a playlist from MediaMonkey to .m3u and use that path (Step 10).",
          results)

    _report(results)


def _report(results: list) -> None:
    print("\n  Pre-flight check\n  " + "-" * 50)
    all_ok = True
    for ok, label, hint in results:
        print(f"  {OK if ok else FIX}  {label}")
        if not ok:
            all_ok = False
            print(f"          -> {hint}")
    print("  " + "-" * 50)
    if all_ok:
        print("  All good! Continue to Step 11:  python door_music_trigger.py --once\n")
    else:
        print("  Fix the [ FIX ] items above, then run  python selfcheck.py  again.\n")


if __name__ == "__main__":
    main()
