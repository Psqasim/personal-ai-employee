"""
Dapr Hello World

Simple Flask application demonstrating Dapr sidecar integration.

Setup:
1. Install dependencies: pip install flask
2. Run with Dapr: dapr run --app-id hello --app-port 5000 --dapr-http-port 3500 -- python hello_world.py
3. Invoke: curl http://localhost:3500/v1.0/invoke/hello/method/hello

"""

from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/hello', methods=['GET'])
def hello():
    """Simple hello endpoint"""
    return jsonify({
        "message": "Hello from Dapr!",
        "app_id": os.getenv('APP_ID', 'hello'),
        "dapr_enabled": True
    }), 200

@app.route('/healthz', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.getenv('APP_PORT', 5000))
    app.run(host='0.0.0.0', port=port)
