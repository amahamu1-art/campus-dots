import os
import certifi
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

import json
import base64
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from negotiation import run_negotiation
import anthropic

load_dotenv(Path(__file__).parent / ".env")

app = Flask(__name__, static_folder="static")
SOULS_DIR = Path(__file__).parent / "souls"


@app.route("/")
@app.route("/home")
def home():
    return send_from_directory("static", "home.html")

@app.route("/app")
def index():
    return send_from_directory("static", "index.html")


@app.route("/api/souls", methods=["GET"])
def list_souls():
    souls = []
    for p in SOULS_DIR.glob("*.json"):
        with open(p) as f:
            souls.append(json.load(f))
    return jsonify(souls)


@app.route("/api/soul", methods=["POST"])
def create_soul():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "Name is required"}), 400

    webhook = data.get("webhook", "").strip()

    soul = {
        "owner": name,
        "emoji": data.get("emoji", "🤖"),
        "priorities": data.get("priorities", ""),
        "webhook": webhook,
        "hard_constraints": {
            "classes": data.get("classes", []),
            "clubs": data.get("clubs", []),
            "routines": data.get("routines", []),
        },
        "current_context": data.get("context", ""),
    }

    filename = SOULS_DIR / f"{name.lower().replace(' ', '_')}.json"
    with open(filename, "w") as f:
        json.dump(soul, f, indent=2)

    # Auto-write webhook to .env so the bot picks it up on next restart
    if webhook:
        env_key = f"WEBHOOK_{name.upper().replace(' ', '_')}"
        env_path = Path(__file__).parent / ".env"
        env_lines = env_path.read_text().splitlines() if env_path.exists() else []
        updated = False
        for i, line in enumerate(env_lines):
            if line.startswith(f"{env_key}="):
                env_lines[i] = f"{env_key}={webhook}"
                updated = True
                break
        if not updated:
            env_lines.append(f"{env_key}={webhook}")
        env_path.write_text("\n".join(env_lines) + "\n")

    return jsonify({"success": True, "soul": soul})


@app.route("/api/parse-soul", methods=["POST"])
def parse_soul():
    data = request.get_json()
    context = data.get("context", "").strip()
    if not context:
        return jsonify({"error": "No context provided"}), 400
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    message = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=600,
        system="""You are extracting a student's schedule constraints from their description.
Return ONLY valid JSON with exactly these fields:
{
  "classes": ["list of class names/codes"],
  "routines": ["list of recurring commitments like gym, work, sleep schedule"],
  "clubs": ["list of clubs or extracurriculars"],
  "priorities": "1-2 sentence string about their scheduling priorities"
}
Be concise. Extract only what's clearly stated. No extra text.""",
        messages=[{"role": "user", "content": f"Extract from this student's description:\n\n{context}"}],
    )
    import re as _re
    raw = message.content[0].text.strip()
    m = _re.search(r'\{.*\}', raw, _re.DOTALL)
    if not m:
        return jsonify({"error": "Could not parse response"}), 500
    try:
        parsed = json.loads(m.group())
        return jsonify(parsed)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/negotiate", methods=["POST"])
def negotiate():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    try:
        result = run_negotiation(prompt)
        if "---" in result:
            log, answer = result.split("---", 1)
        else:
            log, answer = result, ""
        return jsonify({"log": log.strip(), "answer": answer.strip()})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=3000, debug=False)
