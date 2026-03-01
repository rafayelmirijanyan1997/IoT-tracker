from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import requests


@dataclass
class ThingsBoardClient:
    """Minimal ThingsBoard REST client.

    - Auth via JWT (/api/auth/login)
    - Read last telemetry: /api/plugins/telemetry/DEVICE/{id}/values/timeseries?keys=lat,lon
    - Write telemetry by device token: /api/v1/{token}/telemetry
    """

    host: str
    username: str
    password: str
    timeout_s: int = 10

    _jwt: Optional[str] = None
    _jwt_expiry_epoch: float = 0.0

    def _url(self, path: str) -> str:
        return self.host.rstrip("/") + path

    def login(self) -> str:
        url = self._url("/api/auth/login")
        r = requests.post(
            url,
            json={"username": self.username, "password": self.password},
            timeout=self.timeout_s,
        )
        r.raise_for_status()
        data = r.json()
        token = data.get("token") or data.get("jwtToken")
        if not token:
            raise RuntimeError(f"Login response missing token: keys={list(data.keys())}")
        self._jwt = token
        # soft expiry (refresh early)
        self._jwt_expiry_epoch = time.time() + 25 * 60
        return token

    def _auth_headers(self) -> Dict[str, str]:
        if not self._jwt or time.time() > self._jwt_expiry_epoch:
            self.login()
        return {"X-Authorization": f"Bearer {self._jwt}"}

    def get_latest_latlon(self, device_id: str) -> Tuple[float, float]:
        url = self._url(
            f"/api/plugins/telemetry/DEVICE/{device_id}/values/timeseries?keys=lat,lon"
        )
        r = requests.get(url, headers=self._auth_headers(), timeout=self.timeout_s)
        if r.status_code == 401:
            self.login()
            r = requests.get(url, headers=self._auth_headers(), timeout=self.timeout_s)
        r.raise_for_status()

        data = r.json()
        try:
            lat_v = float(data["lat"][0]["value"])
            lon_v = float(data["lon"][0]["value"])
        except Exception as e:
            raise RuntimeError(f"Unexpected telemetry payload for {device_id}: {data}") from e
        return lat_v, lon_v

    @staticmethod
    def post_telemetry_by_token(host: str, device_token: str, payload: Dict) -> None:
        url = host.rstrip("/") + f"/api/v1/{device_token}/telemetry"
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
