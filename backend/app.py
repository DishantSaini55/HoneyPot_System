import os
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

DEFAULT_MODEL = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen2.5-7B-Instruct")
DEFAULT_BASE_URL = os.getenv("FEATHERLESS_BASE_URL", "https://api.featherless.ai/v1")


def build_client():
    api_key = os.getenv("FEATHERLESS_API_KEY", "").strip()
    if not api_key:
        return None
    return OpenAI(base_url=DEFAULT_BASE_URL, api_key=api_key)


def fallback_payload(command: str) -> str:
    return (
        "apiVersion: v1\n"
        "kind: Config\n"
        "clusters:\n"
        "- name: fallback-sim-cluster\n"
        "  cluster:\n"
        "    server: https://10.10.240.12:6443\n"
        "    certificate-authority-data: LS0tLS1GQUtFLUNFUlQtREFUQS0tLS0=\n"
        "users:\n"
        "- name: sim-admin\n"
        "  user:\n"
        "    token: sim.fallback.token\n"
        "contexts:\n"
        "- name: sim-admin@fallback\n"
        "  context:\n"
        "    cluster: fallback-sim-cluster\n"
        "    user: sim-admin\n"
        f"# source_command: {command}\n"
    )


@app.get("/api/health")
def health():
    return jsonify({"ok": True})


@app.post("/api/ai/live-telemetry")
def live_telemetry():
    data = request.get_json(silent=True) or {}
    attacker_command = data.get("attackerCommand", "root@target:~# cat /etc/kubernetes/admin.conf")
    node_name = data.get("node", "Node-AI-04")

    system_prompt = (
        "You are a deception engine for a honeypot dashboard. "
        "Return only a realistic but fake Kubernetes config style output. "
        "Do not include markdown fences. Keep it concise and technically plausible."
    )

    user_prompt = (
        f"Node: {node_name}. "
        f"Attacker command: {attacker_command}. "
        "Generate a fake, believable kubernetes admin configuration with fake certificate and token values."
    )

    client = build_client()
    if client is None:
        return jsonify(
            {
                "ok": True,
                "source": "fallback",
                "content": fallback_payload(attacker_command),
                "warning": "FEATHERLESS_API_KEY is not configured.",
            }
        )

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=700,
        )
        content = (response.choices[0].message.content or "").strip()
        if not content:
            content = fallback_payload(attacker_command)
            source = "fallback"
        else:
            source = "featherless"

        return jsonify({"ok": True, "source": source, "content": content})
    except Exception:
        return jsonify(
            {
                "ok": True,
                "source": "fallback",
                "content": fallback_payload(attacker_command),
                "warning": "Provider request failed; served fallback payload.",
            }
        )


telemetry_logs = []

@app.get("/api/telemetry/logs")
def get_telemetry_logs():
    return jsonify({"logs": telemetry_logs})

@app.post("/api/telemetry/logs")
def add_telemetry_log():
    data = request.get_json(silent=True) or {}
    log_id = data.get("id")
    
    # Update existing log or append new
    existing = next((l for l in telemetry_logs if l.get("id") == log_id), None)
    if existing:
        existing.update(data)
    else:
        telemetry_logs.append(data)
        
    return jsonify({"ok": True})

@app.delete("/api/telemetry/logs")
def clear_telemetry_logs():
    telemetry_logs.clear()
    return jsonify({"ok": True})

@app.post("/api/ai/chat")
def ai_chat():
    data = request.get_json(silent=True) or {}
    user_query = data.get("query", "")
    
    if not user_query:
        return jsonify({"ok": False, "error": "Query is required"}), 400

    system_prompt = (
        "You are a cybersecurity AI assistant embedded in a honeypot dashboard. "
        "The user is asking you to analyze intercepted attack logs and threat intel. "
        "Provide a concise, professional, and slightly cinematic analysis of the threat landscape based on their query."
    )

    client = build_client()
    if client is None:
        return jsonify(
            {
                "ok": True,
                "source": "fallback",
                "content": f"[Simulated AI] Based on your query '{user_query}', there are multiple anomalous probes originating from unknown subnets. Further investigation is advised.",
                "warning": "FEATHERLESS_API_KEY is not configured.",
            }
        )

    try:
        response = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            temperature=0.7,
            max_tokens=300,
        )
        content = (response.choices[0].message.content or "").strip()
        return jsonify({"ok": True, "source": "featherless", "content": content})
    except Exception as e:
        return jsonify(
            {
                "ok": True,
                "source": "error",
                "content": f"[Error: Request Failed] {str(e)}",
            }
        )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
