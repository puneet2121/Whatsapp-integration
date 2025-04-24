from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"
VERIFY_TOKEN = "puneethook"  # You define this yourself (use the same when setting up webhook in Meta)


# ---------- Messaging Utils ----------

def send_text_message(phone, message):
    data = {
        "messaging_product": "whatsapp",
        "to": f"whatsapp:{phone}",
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    print("Text Message Response:", response.status_code, response.text)
    return response


def send_template_message(name, order_id, price, phone):
    data = {
        "messaging_product": "whatsapp",
        "to": f"whatsapp:{phone}",
        "type": "template",
        "template": {
            "name": "order_confirmation",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "body",
                    "parameters": []
                }
            ]
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    print("Template Message Response:", response.status_code, response.text)
    return response


def send_yes_no_buttons(name, order_id, price, phone):
    data = {
        "messaging_product": "whatsapp",
        "to": f"whatsapp:{phone}",
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": f"Hi {name}, please confirm your order #{order_id} of ₹{price}."
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": "yes_confirm",
                            "title": "Yes"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": "no_cancel",
                            "title": "No"
                        }
                    }
                ]
            }
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    print("Button Message Response:", response.status_code, response.text)
    return response


# ---------- Webhooks ----------

@app.route('/webhook/whatsapp-reply', methods=['GET', 'POST'])
def whatsapp_webhook():
    if request.method == 'GET':
        # Verify token for Meta Webhook setup
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')

        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        else:
            return 'Verification failed', 403

    if request.method == 'POST':
        data = request.get_json()
        print("WhatsApp message received:", json.dumps(data, indent=2))

        if data.get("entry"):
            for entry in data["entry"]:
                if entry.get("changes"):
                    for change in entry["changes"]:
                        value = change.get("value", {})
                        messages = value.get("messages", [])
                        for message in messages:
                            from_number = message.get("from")
                            name = value.get("contacts", [{}])[0].get("profile", {}).get("name", "Customer")

                            if message.get("type") == "button":
                                button_reply_id = message["button"]["payload"]

                                if button_reply_id == "yes_confirm":
                                    send_text_message(from_number, f"Thanks {name}, your order is confirmed! 📦 We will ship your item shortly.")
                                elif button_reply_id == "no_cancel":
                                    send_text_message(from_number, f"Hi {name}, your order has been canceled as requested. Let us know if you need help!")

        return "EVENT_RECEIVED", 200


@app.route('/')
def home():
    return "WhatsApp Shopify Flask App Running"


@app.route('/webhook/shopify-order', methods=['POST'])
def handle_order():
    data = request.json
    customer = data.get("customer", {})
    name = customer.get("first_name", "Customer")
    phone = customer.get("phone")
    order_id = data.get("id")
    price = data.get("total_price")
    print("Shopify order received.")

    if phone:
        send_template_message(name, order_id, price, phone)
        send_yes_no_buttons(name, order_id, price, phone)

    return jsonify({"status": "Order processed"}), 200


@app.route('/webhook/shopify-abandoned-cart', methods=['POST'])
def abandoned_cart():
    data = request.json
    customer = data.get("customer", {})
    name = customer.get("first_name", "there")
    phone = customer.get("phone")
    cart_url = data.get("landing_site", "https://yourstore.myshopify.com")

    if phone:
        message = f"Hi {name}, you left some items in your cart 🛒. Complete your purchase here: {cart_url}"
        send_text_message(phone, message)

    return jsonify({"status": "Cart reminder sent"}), 200


# ---------- Run Server ----------
if __name__ == '__main__':
    app.run(port=5000, debug=True)
