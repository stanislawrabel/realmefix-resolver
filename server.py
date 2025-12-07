import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Resolver server is running!"

@app.route("/resolve", methods=["POST"])
def resolve():
    data = request.json
    if not data or "url" not in data:
        return jsonify({"error": "Missing 'url'"}), 400
    # zatiaľ len test
    return jsonify({"resolved": data["url"]})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
