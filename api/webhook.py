import os
from flask import Flask, request, abort
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env in dev; in Vercel you’ll set real ENV vars in the Dashboard

VERIFY_TOKEN    = os.getenv("WH_VERIFY_TOKEN")
ACCESS_TOKEN    = os.getenv("WH_ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("WH_PHONE_NUMBER_ID")

app = Flask(__name__)

@app.route("/api/webhook", methods=["GET"])
def verify():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/api/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if data.get("object") != "whatsapp_business_account":
        return "Ignored", 200

    for entry in data["entry"]:
        for change in entry.get("changes", []):
            if change["field"] != "messages":
                continue
            metadata = change["value"]["metadata"]
            for msg in change["value"]["messages"]:
                sender = msg["from"]
                if "text" in msg:
                    text = msg["text"]["body"]
                    reply = f"🤖 You said: {text}"
                    send_message(metadata["phone_number_id"], sender, reply)
    return "OK", 200

def send_message(phone_number_id, to, text):
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text}
    }
    resp = requests.post(url, json=payload, headers=headers)
    resp.raise_for_status()

# Vercel will detect `app` and use it as the WSGI entrypoint.
