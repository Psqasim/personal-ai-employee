"""
Dapr State Management Example

Demonstrates saving, retrieving, and deleting state using Dapr.

Run:
    dapr run --app-id stateapp --dapr-http-port 3500 -- python state_management.py

Component required: statestore (Redis by default with `dapr init`)

Dependencies: pip install dapr
"""

from dapr.clients import DaprClient
import json

def main():
    with DaprClient() as client:
        store_name = "statestore"

        print("=== Dapr State Management Demo ===\n")

        # 1. Save state
        print("1. Saving state...")
        order = {
            "orderId": 123,
            "item": "laptop",
            "amount": 1200,
            "status": "pending"
        }
        client.save_state(store_name=store_name, key="order-123", value=json.dumps(order))
        print(f"✓ Saved: {order}\n")

        # 2. Get state
        print("2. Retrieving state...")
        state = client.get_state(store_name=store_name, key="order-123")
        retrieved_order = json.loads(state.data) if state.data else None
        print(f"✓ Retrieved: {retrieved_order}")
        print(f"  ETag: {state.etag}\n")

        # 3. Save multiple states (bulk)
        print("3. Saving bulk state...")
        states = [
            ("order-124", json.dumps({"orderId": 124, "item": "mouse", "amount": 25})),
            ("order-125", json.dumps({"orderId": 125, "item": "keyboard", "amount": 75}))
        ]
        client.save_bulk_state(store_name=store_name, states=states)
        print(f"✓ Saved {len(states)} items\n")

        # 4. Get multiple states (bulk)
        print("4. Retrieving bulk state...")
        keys = ["order-123", "order-124", "order-125"]
        bulk_states = client.get_bulk_state(store_name=store_name, keys=keys)
        for item in bulk_states.items:
            if item.data:
                order_data = json.loads(item.data)
                print(f"✓ Retrieved {item.key}: Order #{order_data['orderId']}")
        print()

        # 5. Update with ETag (optimistic concurrency)
        print("5. Updating with ETag...")
        state = client.get_state(store_name=store_name, key="order-123")
        if state.data:
            order = json.loads(state.data)
            order["status"] = "completed"

            try:
                client.save_state(
                    store_name=store_name,
                    key="order-123",
                    value=json.dumps(order),
                    etag=state.etag
                )
                print(f"✓ Updated order status to: {order['status']}\n")
            except Exception as e:
                print(f"✗ Update failed (ETag mismatch): {e}\n")

        # 6. Delete state
        print("6. Deleting state...")
        client.delete_state(store_name=store_name, key="order-124")
        print("✓ Deleted order-124\n")

        # 7. Verify deletion
        print("7. Verifying deletion...")
        state = client.get_state(store_name=store_name, key="order-124")
        if not state.data:
            print("✓ Confirmed: order-124 does not exist\n")

        # 8. Query state (if supported by state store)
        print("8. State operations complete!")
        print("\nNote: For advanced queries, use state stores that support querying")
        print("(e.g., MongoDB, CosmosDB) and the Query State API")

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print("1. Dapr is initialized: dapr init")
        print("2. Redis is running (comes with dapr init)")
        print("3. You're running with: dapr run --app-id stateapp -- python state_management.py")
