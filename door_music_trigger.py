"""Door sensor -> MediaMonkey music trigger.

Polls a SmartThings contact sensor's state via the public REST API and launches
MediaMonkey with a configured playlist on every open -> closed transition.

Runs on the Windows PC. The PC reaches OUT to api.smartthings.com; nothing is
pushed to it and it is never exposed to the internet. Alexa is not involved.

Usage:
    python door_music_trigger.py [--config config.ini] [--once]

    --once   Run a single poll and exit (useful for testing connectivity).
"""

from __future__ import annotations

import argparse
import configparser
import logging
import logging.handlers
import subprocess
import sys
import time
from pathlib import Path

import requests

STATUS_URL = "https://api.smartthings.com/v1/devices/{device_id}/status"
DEFAULT_CONFIG = "config.ini"
LOG_FILE = "door_music_trigger.log"


def load_config(path: str) -> dict:
    cfg = configparser.ConfigParser()
    if not cfg.read(path):
        raise SystemExit(
            f"Config file not found: {path}\n"
            "Copy config.example.ini to config.ini and fill it in."
        )
    try:
        st = cfg["smartthings"]
        mm = cfg["mediamonkey"]
        return {
            "token": st["token"].strip(),
            "device_id": st["device_id"].strip(),
            "poll_interval": cfg.getfloat("smartthings", "poll_interval", fallback=3.0),
            "mm_path": mm["executable_path"].strip(),
            "playlist": mm["playlist_path"].strip(),
        }
    except KeyError as e:
        raise SystemExit(f"Missing required config key/section: {e}")


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("door_music_trigger")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=512_000, backupCount=2, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    logger.addHandler(stream)
    return logger


def fetch_contact_state(token: str, device_id: str, timeout: float = 10.0) -> str:
    """Return 'open' or 'closed'. Raises on network/auth/parse failure."""
    resp = requests.get(
        STATUS_URL.format(device_id=device_id),
        headers={"Authorization": f"Bearer {token}"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["components"]["main"]["contactSensor"]["contact"]["value"]


def is_close_edge(previous: str | None, current: str) -> bool:
    """Fire only on a true open -> closed transition."""
    return previous == "open" and current == "closed"


def launch_music(mm_path: str, playlist: str, logger: logging.Logger) -> None:
    if not Path(mm_path).exists():
        logger.error("MediaMonkey executable not found: %s", mm_path)
        return
    try:
        subprocess.Popen([mm_path, playlist])
        logger.info("Launched MediaMonkey with playlist: %s", playlist)
    except OSError as e:
        logger.error("Failed to launch MediaMonkey: %s", e)


def poll_loop(config: dict, logger: logging.Logger, run_once: bool = False) -> None:
    previous: str | None = None
    logger.info("Started. Polling device %s every %ss.",
                config["device_id"], config["poll_interval"])

    while True:
        try:
            current = fetch_contact_state(config["token"], config["device_id"])
        except requests.HTTPError as e:
            code = e.response.status_code if e.response is not None else "?"
            if code in (401, 403):
                logger.error("Auth failed (%s). Token expired or invalid -- "
                             "regenerate it. Retrying after interval.", code)
            else:
                logger.warning("API error %s; retrying after interval.", code)
            current = None
        except requests.RequestException as e:
            logger.warning("Network error (%s); retrying after interval.", e)
            current = None
        except (KeyError, ValueError) as e:
            logger.error("Unexpected API response shape (%s); retrying.", e)
            current = None

        if current is not None:
            if previous is None:
                logger.info("Initial door state: %s", current)
            elif is_close_edge(previous, current):
                logger.info("Door closed (was %s) -> triggering music.", previous)
                launch_music(config["mm_path"], config["playlist"], logger)
            elif current != previous:
                logger.info("Door state: %s -> %s", previous, current)
            previous = current

        if run_once:
            return
        time.sleep(config["poll_interval"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--once", action="store_true",
                        help="Single poll then exit (connectivity test).")
    args = parser.parse_args()

    logger = setup_logging()
    config = load_config(args.config)
    try:
        poll_loop(config, logger, run_once=args.once)
    except KeyboardInterrupt:
        logger.info("Stopped by user.")


if __name__ == "__main__":
    main()
