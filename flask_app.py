import asyncio
import uuid

from flask import Flask, jsonify, request

from agent import chat_with_agent

app = Flask(__name__)


@app.post("/api/agent/chat")
def agent_chat():
    """Accepts a chat message and invokes the Google ADK agent."""
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    session_id = str(payload.get("session_id") or uuid.uuid4())
    user_id = str(payload.get("user_id") or "anonymous")

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        # ADK Runner.run_async streams Events. The helper consumes those events,
        # captures final text, and includes function-call/function-response parts.
        result = asyncio.run(
            chat_with_agent(
                message=message,
                session_id=session_id,
                user_id=user_id,
            )
        )
        return jsonify(result)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
