# TeamTrack: Real-Time Multi-Phone Mapping + Proximity Analytics (ThingsBoard)

TeamTrack turns phones into IoT location devices and builds a live **team awareness** dashboard in ThingsBoard.

## What it does
- **Live team map (OpenStreetMap widget):** shows each teammate’s phone as a real-time marker.
- **Proximity analytics:** computes distance between two teammates (Haversine) and publishes it back as telemetry.
- **Dashboard widgets:** map + live distance value card (meters), ready for demos and future alarms.

## Architecture
1. Teammates share iPhone location using **OwnTracks** (HTTP mode) into ThingsBoard devices (`lat`, `lon` telemetry).
2. A Python service periodically:
   - pulls latest `lat/lon` for two phones via ThingsBoard REST API
   - calculates distance (meters)
   - publishes `distance_m` to a virtual “distance device” using its access token
3. ThingsBoard dashboard visualizes the results.

## Repo structure
```
iot-team-tracker/
  README.md
  requirements.txt
  .env.example
  src/
    distance_pair.py
    distance_all_pairs.py
    tb_api.py
    haversine.py
  systemd/
    distance-pair.service
```

## Quick start

### 1) Install
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment
Copy `.env.example` → `.env` and fill values:
- `TB_HOST` (e.g. `http://localhost:8080` or `http://<server-ip>:8080`)
- `TB_USER` / `TB_PASS` (tenant credentials) — **for reading phone telemetry**
- `PHONE_A_DEVICE_ID` and `PHONE_B_DEVICE_ID` (UUIDs of the phone devices)
- `DIST_DEVICE_TOKEN` (access token for the distance device — **for writing telemetry**)

### 3) Run
```bash
python3 src/distance_pair.py
```

Expected output:
```
Distance: 907.32 meters
```

## Optional: compute all pair distances (3+ phones)
Publish all pair distances into a single device:
```bash
python3 src/distance_all_pairs.py
```
Configure `PHONE_DEVICE_IDS` and `PAIRWISE_DEVICE_TOKEN` in `.env`.

## Troubleshooting
### 401 when reading telemetry
JWT is missing/expired or credentials are wrong.
- Verify `TB_USER` / `TB_PASS`
- Verify `TB_HOST` is correct/reachable
- Re-run (the script refreshes JWT automatically)

### 400 from curl
Don’t wrap the token in `< >`:
✅ `.../api/v1/qXekfQ.../telemetry`
❌ `.../api/v1/<qXekfQ...>/telemetry`
