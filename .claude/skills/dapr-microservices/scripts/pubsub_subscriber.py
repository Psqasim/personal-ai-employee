"""
Dapr Pub/Sub Subscriber

Subscribes to messages from a topic using Dapr.

Run:
    dapr run --app-id subscriber --app-port 5001 --dapr-http-port 3501 -- python pubsub_subscriber.py

Dependencies: pip install flask cloudevents
"""

from flask import Flask, request, jsonify
from cloudevents.http import from_http
import json

app = Flask(__name__)

@app.route('/dapr/subscribe', methods=['GET'])
def subscribe():
    """
    Dapr calls this endpoint to get subscription configuration.
    Returns list of topics to subscribe to.
    """
    subscriptions = [{
        'pubsubname': 'orderpubsub',
        'topic': 'orders',
        'route': 'orders'
    }]
    print(f"📋 Subscribed to: {subscriptions}")
    return jsonify(subscriptions)

@app.route('/orders', methods=['POST'])
def handle_order():
    """
    Handler for order events.
    Dapr sends CloudEvents format messages to this endpoint.
    """
    try:
        # Parse CloudEvent
        event = from_http(request.headers, request.get_data())

        # Extract data
        data = json.loads(event.data)

        # Process order
        print(f"📦 Received order #{data['orderId']}: {data['item']} - ${data['amount']}")

        # Simulate processing
        # ... your business logic here ...

        # Return success
        return jsonify({'success': True}), 200

    except Exception as e:
        print(f"✗ Error processing order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = 5001
    print(f"🚀 Subscriber listening on port {port}")
    print(f"   Waiting for orders from topic 'orders'...\n")
    app.run(host='0.0.0.0', port=port)
