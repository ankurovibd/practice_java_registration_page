import argparse
import os
import threading
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import Flask, jsonify, request

from notifier import send_sms

load_dotenv()

app = Flask(__name__)

API_TOKEN = os.getenv("API_TOKEN", "change-me")
DEFAULT_RECEIVER = os.getenv("DEVELOPER_RECEIVER_NUMBER", "")

# in-memory device state
DEVICES = {}
LOCK = threading.Lock()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def is_authorized(req) -> bool:
    auth = req.headers.get("Authorization", "")
    return auth == f"Bearer {API_TOKEN}"


def require_fields(payload, required):
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify({"error": f"missing fields: {', '.join(missing)}"}), 400
    return None


@app.get("/")
def health():
    return {
        "status": "ok",
        "timestamp": utc_now_iso(),
        "devices": len(DEVICES),
        "mode": "consent-based",
    }


@app.get("/api/v1/devices")
def list_devices():
    if not is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401

    with LOCK:
        return jsonify({"devices": list(DEVICES.values()), "count": len(DEVICES)})


@app.post("/api/v1/heartbeat")
def heartbeat():
    if not is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    required = ["imei", "phone_number", "lat", "lon", "timestamp", "consent_granted"]
    err = require_fields(payload, required)
    if err:
        return err

    if payload.get("consent_granted") is not True:
        return jsonify({"error": "consent_required"}), 403

    imei = str(payload["imei"])

    with LOCK:
        existing = DEVICES.get(imei, {})
        old_number = existing.get("phone_number")
        DEVICES[imei] = {
            "imei": imei,
            "phone_number": payload["phone_number"],
            "lat": payload["lat"],
            "lon": payload["lon"],
            "timestamp": payload["timestamp"],
            "consent_granted": True,
            "last_seen_server": utc_now_iso(),
        }

    new_number = payload["phone_number"]
    if old_number and old_number != new_number:
        receiver = DEFAULT_RECEIVER
        if receiver:
            send_sms(
                receiver,
                f"[ALERT] IMEI {imei} phone number changed from {old_number} to {new_number}",
            )

    return jsonify({"status": "ok"})


@app.post("/api/v1/number-update")
def number_update():
    if not is_authorized(request):
        return jsonify({"error": "unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    required = ["imei", "old_phone_number", "new_phone_number", "timestamp"]
    err = require_fields(payload, required)
    if err:
        return err

    receiver = payload.get("receiver_number") or DEFAULT_RECEIVER
    if not receiver:
        return jsonify({"error": "receiver_number missing and default not configured"}), 400

    imei = str(payload["imei"])
    old_number = payload["old_phone_number"]
    new_number = payload["new_phone_number"]

    ok = send_sms(
        receiver,
        f"[ALERT] IMEI {imei} phone number changed from {old_number} to {new_number} at {payload['timestamp']}",
    )

    return jsonify({"status": "ok" if ok else "failed"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consent-based smartphone check-in server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    app.run(host=args.host, port=args.port)
