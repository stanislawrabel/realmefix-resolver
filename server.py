from flask import Flask, request, jsonify, render_template_string
import requests
import re
from urllib.parse import urlparse
import os

# ---------- CONFIG ----------
UA = "Dalvik/2.1.0 (Linux; U; Android 13; RMX5011 Build/TKQ1.230329.002)"
DEFAULT_TIMEOUT = 12
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept": "*/*",
    "Connection": "keep-alive"
})

app = Flask(__name__)

# ---------- LINK FIX ----------
def fix_domain(u: str) -> str:
    u = u.replace("allawnos.com", "allawnofs.com")
    u = u.replace("component-ota-eu.allawnos.com", "component-ota-eu.allawnofs.com")
    return u.strip()

# ---------- RESOLUTION CORE ----------
def resolve_link(original_url):
    url = fix_domain(original_url)

    # 1) HEAD request
    try:
        r = SESSION.head(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
        ct = r.headers.get("Content-Type", "")
        cd = r.headers.get("Content-Disposition", "")

        if r.url.endswith(".zip") or ".zip" in cd or "zip" in ct:
            return r.url
    except:
        pass

    # 2) GET + HTML/JSON scan
    try:
        r = SESSION.get(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
        ct = r.headers.get("Content-Type", "")

        # JSON with URL inside
        if "application/json" in ct:
            try:
                j = r.json()
                candidate = (
                    j.get("data", {}).get("url")
                    or j.get("url")
                    or j.get("resolved_url")
                )
                if candidate:
                    return candidate
            except:
                pass

        # Extract ZIP manually
        m = re.search(r'https?://[^\s"\']+?\.zip', r.text)
        if m:
            return m.group(0)
    except:
        pass

    # 3) Manual redirect probe
    try:
        r = SESSION.get(url, timeout=10, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            loc = r.headers.get("Location")
            if loc and loc.endswith(".zip"):
                return loc
    except:
        pass

    return None


# ---------- HTML UI ----------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
<title>RealmeFix OTA Resolver</title>
<style>
body { font-family: sans-serif; background: #111; color: #eee; text-align: center; padding: 40px; }
input { width: 80%%; padding: 10px; font-size: 18px; border-radius: 8px; border: none; }
button { padding: 12px 20px; font-size: 18px; border-radius: 8px; border: none; background: #00c853; color: #fff; cursor: pointer; }
button:hover { background: #00e676; }
.result { margin-top: 30px; font-size: 20px; }
a { color: #00e5ff; }
</style>
</head>
<body>

<h1>RealmeFix OTA Resolver</h1>
<p>Zadaj Realme OTA link (about / download / downloadCheck)</p>

<form method="GET" action="/">
    <input type="text" name="url" placeholder="https://..." required>
    <br><br>
    <button type="submit">Resolve</button>
</form>

{% if result %}
<div class="result">
    {% if result == "ERROR" %}
        <p style="color:#ff5252;">❌ Nepodarilo sa extrahovať odkaz.</p>
    {% else %}
        <p>✔ Final URL:</p>
        <p><a href="{{result}}" target="_blank">{{result}}</a></p>
    {% endif %}
</div>
{% endif %}

</body>
</html>
"""

# ---------- ROUTES ----------

@app.route("/")
def home():
    url = request.args.get("url")
    result = None

    if url:
        resolved = resolve_link(url)
        result = resolved if resolved else "ERROR"

    return render_template_string(HTML_PAGE, result=result)

@app.route("/api/resolve", methods=["POST"])
def api_resolve():
    data = request.get_json(silent=True) or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "missing url"}), 400

    resolved = resolve_link(url)
    if not resolved:
        return jsonify({"error": "cannot_resolve"}), 400

    return jsonify({"final_url": resolved})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
