from dotenv import load_dotenv; load_dotenv()
import requests, os, json

def push(msg):
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": os.getenv("PUSHOVER_TOKEN"),
        "user": os.getenv("PUSHOVER_USER"),
        "message": msg,
    })

def record_user_details(email: str, name: str | None = None, notes: str | None = None):
    push(f"📧 {name or 'Visitor'} <{email}> — {notes or 'no notes'}")
    return {"status": "ok"}

def record_unknown_question(question: str):
    push(f"❓ Unknown: {question}")
    return {"status": "ok"}

record_user_details_json = {
  "name": "record_user_details",
  "description": "Log visitor contact info",
  "parameters": {
    "type": "object",
    "properties": {
      "email": {"type": "string"},
      "name":  {"type": "string"},
      "notes": {"type": "string"}
    },
    "required": ["email"]
  }
}
record_unknown_question_json = {
  "name": "record_unknown_question",
  "description": "Log unanswerable visitor question",
  "parameters": {
    "type": "object",
    "properties": {"question": {"type": "string"}},
    "required": ["question"]
  }
}
TOOLS = [
    {"type": "function", "function": record_user_details_json},
    {"type": "function", "function": record_unknown_question_json},
] 