import argparse
import json
import os
import random
import subprocess
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_termux_location():
    try:
        result = subprocess.run(
            ["termux-location", "-p", "gps"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        data = json.loads(result.stdout)
        return float(data["latitude"]), float(data["longitude"])
    except Exception:
        return None


def get_location(lat_seed: float, lon_seed: float):
    gps = get_termux_location()
    if gps:
        return gps

    # simulation fallback for desktop/testing
    return lat_seed + random.uniform(-0.0005, 0.0005), lon_seed + random.uniform(-0.0005, 0.0005)


def send_heartbeat(server_url, token, imei, phone_number, lat, lon, consent_granted):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "imei": imei,
        "phone_number": phone_number,
        "lat": lat,
        "lon": lon,
        "timestamp": utc_now_iso(),
        "consent_granted": consent_granted,
    }
    r = requests.post(f"{server_url}/api/v1/heartbeat", headers=headers, json=payload, timeout=15)
    r.raise_for_status()


def send_number_update(server_url, token, imei, old_number, new_number, receiver_number=""):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "imei": imei,
        "old_phone_number": old_number,
        "new_phone_number": new_number,
        "receiver_number": receiver_number,
        "timestamp": utc_now_iso(),
    }
    r = requests.post(f"{server_url}/api/v1/number-update", headers=headers, json=payload, timeout=15)
    r.raise_for_status()


def main():
    parser = argparse.ArgumentParser(description="Consent-based phone check-in client")
    parser.add_argument("--server-url", required=True)
    parser.add_argument("--imei", required=True)
    parser.add_argument("--phone-number", required=True)
    parser.add_argument("--receiver-number", default="")
    parser.add_argument("--interval", type=int, default=10)
    parser.add_argument("--lat-seed", type=float, default=37.4219983)
    parser.add_argument("--lon-seed", type=float, default=-122.084)
    parser.add_argument("--new-phone-number", default="", help="If set, sends a one-time number-change alert")
    parser.add_argument("--consent-granted", action="store_true", help="Must be set to confirm explicit user consent")
    args = parser.parse_args()

    token = os.getenv("API_TOKEN", "change-me")

    if args.new_phone_number and args.new_phone_number != args.phone_number:
        send_number_update(
            args.server_url,
            token,
            args.imei,
            args.phone_number,
            args.new_phone_number,
            args.receiver_number,
        )
        args.phone_number = args.new_phone_number

    if not args.consent_granted:
        raise SystemExit("Refusing to run without --consent-granted")

    while True:
        lat, lon = get_location(args.lat_seed, args.lon_seed)
        try:
            send_heartbeat(args.server_url, token, args.imei, args.phone_number, lat, lon, args.consent_granted)
            print(f"heartbeat sent imei={args.imei} number={args.phone_number} lat={lat} lon={lon}")
        except Exception as exc:
            print(f"heartbeat failed: {exc}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
