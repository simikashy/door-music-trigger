"""One-time OAuth authorization for the SmartThings SmartApp.

Run this ONCE on the PC after registering your OAuth SmartApp (see README):

    python authorize.py

It opens your browser to SmartThings, you log in and approve, and it saves the
resulting tokens to the token_store file in config.ini. After that, the main
script refreshes tokens automatically -- you never run this again unless the
PC is offline long enough for the refresh token to expire (~30 days).
"""

from __future__ import annotations

import json
import os
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests

from door_music_trigger import load_config
from smartthings_auth import AUTHORIZE_URL, TOKEN_URL

_received: dict = {}


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server API)
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        _received.update({k: v[0] for k, v in params.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        if "code" in _received:
            msg = "Authorization complete. You can close this tab."
        else:
            msg = f"Authorization failed: {_received.get('error', 'unknown error')}"
        self.wfile.write(f"<html><body><h2>{msg}</h2></body></html>".encode())

    def log_message(self, *args):  # silence the default console logging
        pass


def _wait_for_code(redirect_uri: str) -> str:
    parsed = urllib.parse.urlparse(redirect_uri)
    server = HTTPServer((parsed.hostname, parsed.port or 80), _CallbackHandler)
    server.timeout = 300
    print(f"Listening for the redirect on {redirect_uri} ...")
    while "code" not in _received and "error" not in _received:
        server.handle_request()
    if "code" not in _received:
        raise SystemExit(f"Authorization failed: {_received.get('error')}")
    return _received["code"]


def main() -> None:
    cfg = load_config("config.ini")
    if not cfg.get("client_id"):
        raise SystemExit("config.ini has no [oauth] client_id. See README.")

    auth_url = AUTHORIZE_URL + "?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": cfg["client_id"],
            "scope": cfg["scope"],
            "redirect_uri": cfg["redirect_uri"],
        }
    )
    print("Opening browser to authorize...")
    webbrowser.open(auth_url)
    print("If the browser did not open, visit this URL manually:\n", auth_url)

    code = _wait_for_code(cfg["redirect_uri"])

    print("Exchanging code for tokens...")
    resp = requests.post(
        TOKEN_URL,
        auth=(cfg["client_id"], cfg["client_secret"]),
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": cfg["redirect_uri"],
            "client_id": cfg["client_id"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    state = {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": time.time() + float(data.get("expires_in", 86400)),
    }
    store = cfg["token_store"]
    tmp = store + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, store)
    print(f"Saved tokens to {store}. You're done -- run door_music_trigger.py.")


if __name__ == "__main__":
    main()
