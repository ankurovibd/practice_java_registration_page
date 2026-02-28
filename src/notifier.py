import os
import requests


def send_sms(receiver_number: str, message: str) -> bool:
    """Send SMS via Twilio if configured; otherwise log to console."""
    sid = os.getenv("TWILIO_ACCOUNT_SID", "").strip()
    token = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
    from_number = os.getenv("TWILIO_FROM_NUMBER", "").strip()

    if not (sid and token and from_number):
        print(f"[NOTIFY:FALLBACK] to={receiver_number} msg={message}")
        return True

    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    payload = {"From": from_number, "To": receiver_number, "Body": message}

    response = requests.post(url, data=payload, auth=(sid, token), timeout=15)
    if response.status_code >= 400:
        print(f"[NOTIFY:ERROR] Twilio returned {response.status_code}: {response.text}")
        return False

    return True
