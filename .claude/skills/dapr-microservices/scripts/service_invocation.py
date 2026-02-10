"""
Dapr Service Invocation Example

Demonstrates service-to-service communication using Dapr.

Components:
- Client: Sends requests to another service
- Server: Receives and processes requests

Run server:
    dapr run --app-id order-processor --app-port 6001 --dapr-http-port 3501 -- python service_invocation.py server

Run client:
    dapr run --app-id checkout --dapr-http-port 3500 -- python service_invocation.py client

Dependencies: pip install flask requests dapr
"""

import requests
import json
import time
import sys
from flask import Flask, request, jsonify

# ============ CLIENT ============
def run_client():
    """Client that invokes another service via Dapr"""
    dapr_port = "3500"
    dapr_url = f"http://localhost:{dapr_port}/v1.0/invoke/order-processor/method/orders"

    orders = [
        {"orderId": 1, "item": "laptop", "amount": 1200},
        {"orderId": 2, "item": "mouse", "amount": 25},
        {"orderId": 3, "item": "keyboard", "amount": 75}
    ]

    for order in orders:
        try:
            response = requests.post(
                dapr_url,
                json=order,
                headers={'Content-Type': 'application/json'}
            )
            print(f"✓ Order {order['orderId']} processed: {response.json()}")
        except Exception as e:
            print(f"✗ Error processing order {order['orderId']}: {e}")

        time.sleep(1)

# ============ SERVER ============
app = Flask(__name__)

@app.route('/orders', methods=['POST'])
def process_order():
    """Server endpoint that processes orders"""
    order = request.json
    print(f"📦 Processing order {order['orderId']}: {order['item']} - ${order['amount']}")

    # Simulate processing
    result = {
        "success": True,
        "orderId": order["orderId"],
        "status": "processed",
        "timestamp": time.time()
    }

    return jsonify(result), 200

def run_server():
    """Run the order processor server"""
    port = 6001
    print(f"🚀 Order processor listening on port {port}")
    app.run(host='0.0.0.0', port=port)

# ============ MAIN ============
if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        run_server()
    else:
        run_client()
