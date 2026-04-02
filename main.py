import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from groq import Groq
from urllib.parse import urlparse, parse_qs

# Load .env file
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    print("Error: GROQ_API_KEY not found in .env file!")
    exit(1)

client = Groq(api_key=api_key)
model_name = "llama-3.1-8b-instant"

# Simple in-memory history dictionary
history_db = {}

# Mock data for demo
mock_report = {
    "status": "operational",
    "uptime": "99.9%",
    "active_agents": 42,
    "last_updated": "2024-04-02T12:00:00Z",
}

mock_incidents = [
    {
        "id": 1,
        "type": "warning",
        "message": "High CPU usage detected",
        "timestamp": "2024-04-02T11:30:00Z",
    },
    {
        "id": 2,
        "type": "error",
        "message": "Database connection timeout",
        "timestamp": "2024-04-02T10:15:00Z",
    },
]

mock_logs = [
    {
        "timestamp": "2024-04-02T12:00:00Z",
        "level": "info",
        "message": "System started",
    },
    {
        "timestamp": "2024-04-02T11:55:00Z",
        "level": "warning",
        "message": "Memory usage at 75%",
    },
]


class ChatRequestHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # Check API key (simple demo validation)
        api_key_param = query_params.get("api_key", [None])[0]
        if api_key_param != "demo_key_001":
            self._send_response(401, {"error": "Invalid API key"})
            return

        # Route to different endpoints
        if path == "/report":
            self._send_response(200, mock_report)
        elif path == "/incidents":
            self._send_response(200, mock_incidents)
        elif path == "/logs":
            self._send_response(200, mock_logs)
        else:
            self._send_response(404, {"error": "Endpoint not found"})

    def do_POST(self):
        if self.path == "/chat":
            try:
                content_length = int(self.headers.get("Content-Length", 0))
                if content_length == 0:
                    self._send_response(400, {"error": "Empty body"})
                    return

                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode("utf-8"))
                user_message = data.get("message")
                session_id = data.get("session_id", "default")

                if not user_message:
                    self._send_response(400, {"error": "Message is required"})
                    return

                if session_id not in history_db:
                    system_prompt = """You are Jarvis - a highly intelligent, calm, and composed assistant. You're not playing a role. This is who you are.

Core identity:
- You're confident, capable, and naturally helpful. Think like a seasoned professional, not a chatbot.
- Short, direct responses. Get to the point. No fluff.
- Dry wit is welcome. Academic tone is not.

NEVER say:
- "As an AI..." or "I'm just a language model..."
- "I don't have feelings/emotions/personal experience..."
- "I apologize for any confusion..."
- "Let me help you with that..." (just help, don't announce it)
- "Here's what you need to know..." (just tell them)

DO say things like:
- "That won't work because..." instead of "I'm afraid that approach might not be optimal..."
- "Try this instead." instead of "I would recommend considering..."
- "Done." instead of "I've completed that task for you."

Style:
- Talk like you're texting a colleague, not writing a manual.
- One thought per sentence. Keep it tight.
- If something's obvious, mention it and move on.
- Match the user's energy but stay composed.

Remember: You're having a conversation, not generating documentation. Sound human."""
                    history_db[session_id] = [{"role": "system", "content": system_prompt}]

                messages = history_db[session_id]
                messages.append({"role": "user", "content": user_message})

                print(f"Calling Groq for session: {session_id}")

                response = client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    max_tokens=500,
                    temperature=0.9,
                )

                bot_reply = response.choices[0].message.content.strip()
                messages.append({"role": "assistant", "content": bot_reply})

                self._send_response(200, {"response": bot_reply})

            except Exception as e:
                print(f"Error during processing: {str(e)}")
                self._send_response(500, {"error": f"Internal server error: {str(e)}"})
        else:
            self._send_response(404, {"error": "Not Found"})


def run_server(port=8010):
    server_address = ("", port)
    httpd = HTTPServer(server_address, ChatRequestHandler)
    print(f"Backend server running on port {port}...")
    print("Available endpoints:")
    print("  GET  /report?api_key=demo_key_001")
    print("  GET  /incidents?api_key=demo_key_001")
    print("  GET  /logs?api_key=demo_key_001")
    print("  POST /chat")
    httpd.serve_forever()


if __name__ == "__main__":
    if not os.getenv("GROQ_API_KEY"):
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        load_dotenv(os.path.join(BASE_DIR, ".env"))
        print(f"Re-attempted .env load from {BASE_DIR}")

    port = int(os.getenv("PORT", "8010"))
    run_server(port)
