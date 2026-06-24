"""Helper: list your SmartThings devices so you can find the door sensor's ID.

Usage:
    python list_devices.py YOUR_TOKEN

Prints each device's name and deviceId. Copy the deviceId of your door sensor
into config.ini.
"""

import sys

import requests

DEVICES_URL = "https://api.smartthings.com/v1/devices"


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python list_devices.py YOUR_TOKEN")
    token = sys.argv[1].strip()

    resp = requests.get(
        DEVICES_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    for d in resp.json().get("items", []):
        label = d.get("label") or d.get("name") or "(unnamed)"
        print(f"{label:40s}  {d['deviceId']}")


if __name__ == "__main__":
    main()
