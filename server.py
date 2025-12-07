from flask import Flask, request, jsonify
import requests
import re

app = Flask(__name__)

UA = "Dalvik/2.1.0 (Linux; U; Android 13; RMX5011 Build/TKQ1.230329.002)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept": "*/*", "Connection": "keep-alive"})

def fix_domain(u: str) -> str:
    u = u.replace("allawnos.com", "allawnofs.com")
    u = u.replace("component-ota-eu.allawnos.com", "component-ota-eu.allawnofs.com")
    return u.strip()

def find_zip(text):
    m = re.search(r'https?://[^\s"\']+?\.zip', text)
    return m.group(0) if m else None

@app.route("/api/resolve")
def resolve():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing ?url="}), 400

    fixed = fix_domain(url)

    # Try GET
    try:
        r = SESSION.get(fixed, timeout=12)
    except:
        return jsonify({"error": "primary request failed"}), 500

    # JSON route
    if "json" in r.headers.get("Content-Type", ""):
        try:
            j = r.json()
            candidate = (
                j.get("data", {}).get("url")
                or j.get("url")
                or j.get("resolved_url")
            )
            if candidate:
                return jsonify({"final": candidate})
        except:
            pass

    # Try to find zip in HTML
    z = find_zip(r.text)
    if z:
        return jsonify({"final": z})

    # Try Gauss API resolver
    api = "https://gauss-componentotamanual.allawnofs.com/gauss/api/component/v1/downloadCheck"
    try:
        j = SESSION.post(api, json={"downloadUrl": fixed}, timeout=10).json()
        candidate = (
            j.get("data", {}).get("url")
            or j.get("url")
            or j.get("resolved_url")
        )
        if candidate:
            return jsonify({"final": candidate})
    except:
        pass

    return jsonify({"error": "no zip found"}), 404

@app.route("/")
def home():
    return """
    <h1>Realme OTA Resolver API</h1>
    <p>Use: <code>/api/resolve?url=YOUR_OTA_LINK</code></p>
    """
