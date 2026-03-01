from __future__ import annotations

import os
import time
from typing import Optional

from dotenv import load_dotenv

from haversine import haversine_m
from tb_api import ThingsBoardClient


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise SystemExit(f"Missing environment variable: {name}")
    return v


def main() -> None:
    load_dotenv()

    tb_host = env("TB_HOST")
    tb_user = env("TB_USER")
    tb_pass = env("TB_PASS")

    phone_a = env("PHONE_A_DEVICE_ID")
    phone_b = env("PHONE_B_DEVICE_ID")
    dist_token = env("DIST_DEVICE_TOKEN")

    poll_s = float(os.getenv("POLL_SECONDS", "10"))

    tb = ThingsBoardClient(host=tb_host, username=tb_user, password=tb_pass)

    print(f"[TeamTrack] Reading phones: A={phone_a} B={phone_b}")
    print(f"[TeamTrack] Writing distance telemetry to token: {dist_token[:6]}...")

    while True:
        try:
            lat1, lon1 = tb.get_latest_latlon(phone_a)
            lat2, lon2 = tb.get_latest_latlon(phone_b)

            d_m = haversine_m(lat1, lon1, lat2, lon2)
            payload = {
                "distance_m": round(d_m, 2),
                "a_lat": lat1, "a_lon": lon1,
                "b_lat": lat2, "b_lon": lon2,
            }

            ThingsBoardClient.post_telemetry_by_token(tb_host, dist_token, payload)
            print(f"Distance: {payload['distance_m']} meters")
        except Exception as e:
            print(f"[WARN] {e}")

        time.sleep(poll_s)


if __name__ == "__main__":
    main()
