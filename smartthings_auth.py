"""SmartThings authentication providers.

Two ways to authenticate API calls:

- StaticAuth: a single bearer token (e.g. a Personal Access Token). Simplest,
  but SmartThings expires new PATs quickly -- good for a quick test only.

- OAuthAuth: a registered OAuth SmartApp. Uses a long-lived refresh token to
  silently mint fresh access tokens, so it keeps working indefinitely. This is
  the durable, set-and-forget path.

Both expose the same interface: .get(url) -> requests.Response (raises on error).
Use build_auth(config) to pick the right one from config.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import requests

TOKEN_URL = "https://api.smartthings.com/oauth/token"
AUTHORIZE_URL = "https://api.smartthings.com/oauth/authorize"
# Refresh this many seconds before the access token actually expires.
REFRESH_SKEW = 120.0


class AuthError(RuntimeError):
    pass


class StaticAuth:
    """Single static bearer token. No refresh."""

    def __init__(self, token: str):
        self.token = token

    def get(self, url: str, timeout: float = 10.0) -> requests.Response:
        resp = requests.get(
            url, headers={"Authorization": f"Bearer {self.token}"}, timeout=timeout
        )
        resp.raise_for_status()
        return resp


class OAuthAuth:
    """OAuth SmartApp token with automatic refresh.

    Token state lives in a JSON file (token_store) holding access_token,
    refresh_token, and expires_at (epoch seconds). The initial file is created
    by running authorize.py once.
    """

    def __init__(self, client_id: str, client_secret: str, token_store: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_store = Path(token_store)
        self._state = self._load()

    def _load(self) -> dict:
        if not self.token_store.exists():
            raise AuthError(
                f"No token file at {self.token_store}. Run authorize.py once to "
                "create it."
            )
        return json.loads(self.token_store.read_text(encoding="utf-8"))

    def _save(self) -> None:
        # Atomic write so a crash mid-write can't corrupt the token store.
        tmp = self.token_store.with_suffix(self.token_store.suffix + ".tmp")
        tmp.write_text(json.dumps(self._state, indent=2), encoding="utf-8")
        os.replace(tmp, self.token_store)

    def _expired(self) -> bool:
        return time.time() >= self._state.get("expires_at", 0) - REFRESH_SKEW

    def refresh(self) -> None:
        resp = requests.post(
            TOKEN_URL,
            auth=(self.client_id, self.client_secret),
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._state["refresh_token"],
                "client_id": self.client_id,
            },
            timeout=15,
        )
        if resp.status_code in (400, 401):
            raise AuthError(
                "Refresh token rejected (expired or revoked). Re-run authorize.py "
                "to re-link your account."
            )
        resp.raise_for_status()
        self._apply_token_response(resp.json())

    def _apply_token_response(self, data: dict) -> None:
        self._state["access_token"] = data["access_token"]
        # SmartThings rotates the refresh token on each use; keep the newest.
        if data.get("refresh_token"):
            self._state["refresh_token"] = data["refresh_token"]
        self._state["expires_at"] = time.time() + float(data.get("expires_in", 86400))
        self._save()

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._state['access_token']}"}

    def get(self, url: str, timeout: float = 10.0) -> requests.Response:
        if self._expired():
            self.refresh()
        resp = requests.get(url, headers=self._headers(), timeout=timeout)
        if resp.status_code == 401:
            # Token died early; refresh once and retry.
            self.refresh()
            resp = requests.get(url, headers=self._headers(), timeout=timeout)
        resp.raise_for_status()
        return resp


def build_auth(config: dict):
    """Pick an auth provider from parsed config."""
    if config.get("client_id"):
        return OAuthAuth(
            client_id=config["client_id"],
            client_secret=config["client_secret"],
            token_store=config["token_store"],
        )
    if config.get("token"):
        return StaticAuth(config["token"])
    raise AuthError(
        "No auth configured. Set an [oauth] client_id/client_secret (recommended) "
        "or a [smartthings] token in config.ini."
    )
