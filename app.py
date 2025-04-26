from flask import Flask, request, jsonify
import requests
import os
import json

app = Flask(__name__)

ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
PHONE_NUMBER_ID = "629828370214498"
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


def send_template_message(phone, customer_name, product_name, image_url):
    data = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "order_confirmation",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {"link": image_url},
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "parameter_name": "customer_name", "text": customer_name},

                        {"type": "text", "parameter_name": "product_name", "text": product_name}
                    ]
                },
                {
                    "type": "footer",  # Optional, if you want to include footer
                    "parameters": [
                        {"type": "text", "text": "Thank you for your Order"}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": "Yes-Button-Payload"
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": 1,
                    "parameters": [
                        {
                            "type": "payload",
                            "payload": "No-Button-Payload"
                        }
                    ]
                }

            ]
        }
    }
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    print(data)
    response = requests.post(WHATSAPP_API_URL, headers=headers, json=data)
    print("Template Message Response:", response.status_code, response.text)
    return response


@app.route('/webhook/whatsapp-reply', methods=['GET', 'POST'])
def handle_whatsapp_reply():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        challenge = request.args.get('hub.challenge')
        token = request.args.get('hub.verify_token')

        VERIFY_TOKEN = 'your-custom-verify-token'

        if mode and token:
            if mode == 'subscribe' and token == VERIFY_TOKEN:
                print('WEBHOOK_VERIFIED')
                return challenge, 200
            else:
                return "Verification token mismatch", 403

    if request.method == 'POST':
        data = request.json
        print("Received data:", data)

        if 'entry' in data:
            for entry in data['entry']:
                changes = entry.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    if 'messages' in value:
                        for message in value['messages']:
                            if 'button' in message:
                                button_payload = message['button'].get('payload')
                                print("Button Payload Received:", button_payload)

                                phone_number = message['from']
                                print("Phone number who clicked:", phone_number)

                                if button_payload == "Yes-Button-Payload":
                                    # Customer clicked Yes
                                    thank_you_message = "🎉 Thank you for confirming your order! Your order is now being processed. 🚚"
                                    send_text_message(phone_number, thank_you_message)
                                    return jsonify({"status": "Replied to YES"}), 200

                                elif button_payload == "No-Button-Payload":
                                    # Customer clicked No
                                    sorry_message = "😔 Thanks for letting us know! If you need help changing or cancelling your order, please contact our support team."
                                    send_text_message(phone_number, sorry_message)
                                    return jsonify({"status": "Replied to NO"}), 200

        return jsonify({"status": "No button interaction found"}), 200


@app.route('/')
def home():
    return "WhatsApp Shopify Flask App Running"


@app.route('/webhook/shopify-order', methods=['POST'])
def handle_order():
    data = request.json
    customer = data.get("customer", {})
    product = data.get("product", {})
    name = customer.get("name", "Customer")
    phone = customer.get("phone")
    product_name = product.get("title", "Product")
    image_url = product.get("image_url",
                            "https://mixwix.in/cdn/shop/files/Untitled_design_-_2025-03-13T082510.334.png?v=1741865378&width=360")

    if phone:
        send_template_message(
            phone=phone,  # Dynamic phone
            customer_name=name,  # Dynamic customer name
            product_name=product_name,  # Dynamic product name
            image_url=image_url  # Dynamic image if provided, else fallback
        )
    return jsonify({"status": "Order processed"}), 200


def send_abandoned_cart_template(phone, customer_name, item_name, checkout_url):
    data = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": "abandon_cart",
            "language": {"code": "en"},
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "text",
                            "text": item_name
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": customer_name
                        },
                        {
                            "type": "text",
                            "text": item_name
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": 0,
                    "parameters": [
                        {
                            "type": "text",
                            "text": checkout_url
                        }
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
    print("Abandoned Cart Template Response:", response.status_code, response.text)
    return response


@app.route('/webhook/shopify-abandoned-cart', methods=['POST'])
def abandoned_cart():
    data = request.json
    customer = data.get("customer", {})
    name = customer.get("name", "there")  # fallback if name missing
    phone = customer.get("phone")

    cart = data.get("cart", {})
    cart_item_name = cart.get("first_product_name", "items")  # fallback if missing
    checkout_url = data.get("landing_site", "https://mixwix.in/")  # fallback to your homepage if missing

    if phone:
        send_abandoned_cart_template(
            phone=phone,
            customer_name=name,
            item_name=cart_item_name,
            checkout_url=checkout_url
        )

    return jsonify({"status": "Abandoned cart reminder sent"}), 200


# ---------- Run Server ----------
if __name__ == '__main__':
    app.run(port=5000, debug=True)
