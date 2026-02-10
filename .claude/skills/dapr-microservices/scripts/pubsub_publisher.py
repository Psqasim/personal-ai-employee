"""
Dapr Pub/Sub Publisher

Publishes messages to a topic using Dapr.

Run:
    dapr run --app-id publisher --dapr-http-port 3500 -- python pubsub_publisher.py

Dependencies: pip install dapr
"""

from dapr.clients import DaprClient
import json
import time

def main():
    pubsub_name = 'orderpubsub'  # Name of pub/sub component
    topic_name = 'orders'         # Topic to publish to

    orders = [
        {"orderId": 1, "item": "laptop", "amount": 1200},
        {"orderId": 2, "item": "mouse", "amount": 25},
        {"orderId": 3, "item": "keyboard", "amount": 75},
        {"orderId": 4, "item": "monitor", "amount": 350},
        {"orderId": 5, "item": "webcam", "amount": 80}
    ]

    with DaprClient() as client:
        print(f"📤 Publishing to topic '{topic_name}'...")
        print(f"   Using pub/sub: {pubsub_name}\n")

        for order in orders:
            try:
                # Publish event
                client.publish_event(
                    pubsub_name=pubsub_name,
                    topic_name=topic_name,
                    data=json.dumps(order),
                    data_content_type='application/json'
                )
                print(f"✓ Published order #{order['orderId']}: {order['item']} - ${order['amount']}")

                time.sleep(1)  # Delay between messages

            except Exception as e:
                print(f"✗ Failed to publish order #{order['orderId']}: {e}")

        print(f"\n✓ Published {len(orders)} orders")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. Dapr is initialized: dapr init")
        print("2. Pub/sub component 'orderpubsub' is configured")
        print("3. Subscriber is running to receive messages")
