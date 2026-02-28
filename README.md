# Consent-Based Smartphone Check-in Tracker (Python)

This repository provides a **legal, consent-based** Python project for smartphone check-ins.

It does **not** implement spyware, stealth monitoring, or remote phone takeover (camera/gallery/file-manager control), because that would be unsafe and illegal in many places.

## What this project does

1. **Real-time GPS check-ins** (from a phone-side script you run yourself, e.g., in Termux on Android).
2. **Phone number change alert**: if the registered phone number changes, the server notifies a configured receiver number.
3. **Cross-platform server/CLI**: runs on Linux, Windows, or macOS.

## Structure

- `src/server.py` – Flask API + terminal dashboard.
- `src/phone_client.py` – phone-side client that sends location + number updates.
- `src/notifier.py` – pluggable notifier (console fallback + optional Twilio SMS).
- `requirements.txt` – Python dependencies.
- `.env.example` – environment variable template.

## Quick start

### 1) Create environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2) Configure env

```bash
cp .env.example .env
```

Edit `.env`:
- `API_TOKEN`: shared token between server and phone client.
- `DEVELOPER_RECEIVER_NUMBER`: destination number for change alerts.
- Optional Twilio vars (`TWILIO_*`) for SMS delivery.

### 3) Run server

```bash
python src/server.py --host 0.0.0.0 --port 8080
```

### 4) Run phone client

On the phone (or any device that can provide GPS), run:

```bash
python src/phone_client.py \
  --server-url http://YOUR_SERVER_IP:8080 \
  --imei "123456789012345" \
  --phone-number "+15555550100" \
  --interval 10 \
  --consent-granted
```

#### Android + Termux GPS integration
If `termux-location` exists, the client uses it automatically for live GPS.
Otherwise, it falls back to manual or simulated coordinates.

## API protocol


### `GET /api/v1/devices`
Returns latest known check-in data for all registered devices.


### `POST /api/v1/heartbeat`
Body:
```json
{
  "imei": "123456789012345",
  "phone_number": "+15555550100",
  "lat": 37.4219983,
  "lon": -122.084,
  "timestamp": "2026-01-01T12:34:56Z",
  "consent_granted": true
}
```

### `POST /api/v1/number-update`
Body:
```json
{
  "imei": "123456789012345",
  "old_phone_number": "+15555550100",
  "new_phone_number": "+15555550123",
  "receiver_number": "+15555550999",
  "timestamp": "2026-01-01T12:35:00Z"
}
```

Both endpoints require header:
- `Authorization: Bearer <API_TOKEN>`

## Notes

- Use only with explicit owner consent.
- Client execution requires `--consent-granted`, and the server rejects heartbeats without `consent_granted: true`.
- This is for device management and anti-loss workflows, not surveillance.
