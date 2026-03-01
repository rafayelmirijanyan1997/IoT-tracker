from __future__ import annotations

import itertools
import os
import time
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from haversine import haversine_m
from tb_api import ThingsBoardClient


def env(name: str, default: Optional[str] = None) -> str:
    v = os.getenv(name, default)
    if v is None or v == "":
        raise SystemExit(f"Missing environment variable: {name}")
    return v


def parse_ids(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def short_name(device_id: str) -> str:
    return device_id.split("-")[0]


def main() -> None:
    load_dotenv()

    tb_host = env("TB_HOST")
    tb_user = env("TB_USER")
    tb_pass = env("TB_PASS")

    phone_ids = parse_ids(env("PHONE_DEVICE_IDS"))
    out_token = env("PAIRWISE_DEVICE_TOKEN")
    poll_s = float(os.getenv("POLL_SECONDS", "10"))

    if len(phone_ids) < 3:
        raise SystemExit("PHONE_DEVICE_IDS must contain at least 3 device IDs")

    tb = ThingsBoardClient(host=tb_host, username=tb_user, password=tb_pass)

    print(f"[TeamTrack] Pairwise mode for {len(phone_ids)} phones")
    print(f"[TeamTrack] Writing telemetry to token: {out_token[:6]}...")

    while True:
        try:
            coords: Dict[str, Tuple[float, float]] = {}
            for did in phone_ids:
                coords[did] = tb.get_latest_latlon(did)

            distances: Dict[str, float] = {}
            closest_pair = None
            closest_d = None

            for a, b in itertools.combinations(phone_ids, 2):
                lat1, lon1 = coords[a]
                lat2, lon2 = coords[b]
                d = float(round(haversine_m(lat1, lon1, lat2, lon2), 2))
                key = f"d_{short_name(a)}_{short_name(b)}_m"
                distances[key] = d
                if closest_d is None or d < closest_d:
                    closest_d = d
                    closest_pair = f"{short_name(a)}-{short_name(b)}"

            payload = dict(distances)
            if closest_pair is not None:
                payload["closest_pair"] = closest_pair
                payload["closest_distance_m"] = closest_d

            ThingsBoardClient.post_telemetry_by_token(tb_host, out_token, payload)
            print(f"Closest: {payload.get('closest_pair')} = {payload.get('closest_distance_m')} m")
        except Exception as e:
            print(f"[WARN] {e}")

        time.sleep(poll_s)


if __name__ == "__main__":
    main()
