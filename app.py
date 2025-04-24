# import requests
#

# RECIPIENT_PHONE = "whatsapp:+15874326564"  # Your test/customer number
#
#
# TEMPLATE_NAME = "order_confirmation"  # Ensure this is the correct template name
# API_VERSION = "v19.0"
#
# url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
#
# headers = {
#     "Authorization": f"Bearer {ACCESS_TOKEN}",
#     "Content-Type": "application/json"
# }
#
# data = {
#     "messaging_product": "whatsapp",
#     "to": RECIPIENT_PHONE,
#     "type": "template",
#     "template": {
#         "name": TEMPLATE_NAME,
#         "language": { "code": "en" },  # Language code for English
#         "components": [
#             {
#                 "type": "body",
#                 "parameters": []  # No parameters needed for this template
#             }
#         ]
#     }
# }
#
# response = requests.post(url, headers=headers, json=data)
#
# print(response.status_code)
# print(response.json())
#
# print(response.status_code)
# print(response.json())


from flask import Flask, request, jsonify
import requests
import json

app = Flask(__name__)

import os

ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")

WHATSAPP_API_URL = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"


# Utils to send messages
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
            "name": "order_confirm",
            "language": {"code": "en_US"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": name},
                        {"type": "text", "text": order_id},
                        {"type": "text", "text": str(price)}
                    ]
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


# Routes
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


if __name__ == '__main__':
    app.run(port=5000, debug=True)
