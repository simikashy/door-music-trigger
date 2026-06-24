"""List your SmartThings devices so you can find the door sensor's ID.

Normal use (after you've run authorize.py):
    python list_devices.py

It reads your saved login from config.ini / tokens.json automatically and prints
each device's name and its long ID. Copy the ID next to your door sensor into
config.ini.

Advanced: pass a token directly to bypass config:
    python list_devices.py YOUR_TOKEN
"""

import sys

from door_music_trigger import load_config
from smartthings_auth import StaticAuth, build_auth

DEVICES_URL = "https://api.smartthings.com/v1/devices"


def main() -> None:
    if len(sys.argv) == 2:
        auth = StaticAuth(sys.argv[1].strip())
    else:
        auth = build_auth(load_config("config.ini"))

    resp = auth.get(DEVICES_URL)
    items = resp.json().get("items", [])
    if not items:
        print("No devices found for this account.")
        return
    print(f"{'DEVICE NAME':40s}  DEVICE ID")
    print("-" * 80)
    for d in items:
        label = d.get("label") or d.get("name") or "(unnamed)"
        print(f"{label:40s}  {d['deviceId']}")


if __name__ == "__main__":
    main()
