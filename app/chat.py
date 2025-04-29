

import os, re, json, requests
from openai import OpenAI
from dotenv import load_dotenv
import gradio as gr

load_dotenv()

# ─── Pushover helpers ───────────────────────────────────────────
def _pushover_send(msg: str):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token":  os.getenv("PUSHOVER_TOKEN"),
            "user":   os.getenv("PUSHOVER_USER"),
            "message": msg,
        },
        timeout=10
    )

def _push_email(email: str, name: str | None, notes: str | None):
    lines = [f"📧 {email}"]
    if name and name != "Name not provided":
        lines.insert(0, f"👤 {name}")
    if notes and notes != "not provided":
        lines.append(f"📝 {notes}")
    _pushover_send("\n".join(lines))

def _push_question(q: str):
    _pushover_send(f"❓ Unknown question\n———\n{q}")

# functions exposed to the LLM
def record_user_details(email, name="Name not provided", notes="not provided"):
    _push_email(email, name, notes)
    return {"recorded": "ok"}

def record_unknown_question(question):
    _push_question(question)
    return {"recorded": "ok"}

TOOLS = [
    {"type": "function", "function": {
        "name": "record_user_details",
        "description": "Log visitor e-mail + optional name/notes",
        "parameters": {
            "type":"object",
            "properties": {
                "email":{"type":"string"},
                "name": {"type":"string"},
                "notes":{"type":"string"}
            },
            "required":["email"]
        }}},
    {"type": "function", "function": {
        "name": "record_unknown_question",
        "description": "Log any question the bot could not answer",
        "parameters": {
            "type":"object",
            "properties":{"question":{"type":"string"}},
            "required":["question"]
        }}}
]

# ─── load chunks once ───────────────────────────────────────────
with open("data/chunks.json", encoding="utf-8") as f:
    CHUNKS = json.load(f)

BY_SECTION: dict[str, list[str]] = {}
for c in CHUNKS:
    BY_SECTION.setdefault(c["section"], []).append(c["text"])

# ─── regex intent router ────────────────────────────────────────
INTENT_RE = {
    r"\b(project|github|built)\b"           : "project",
    r"\b(experience|work(ed)?|job|intern)\b": "experience",
    r"\b(skill|stack|tool|tech)\b"          : "skills",
    r"\b(educat|degree|study|college)\b"    : "education",
    r"\b(contact|email|phone|reach)\b"      : "contact",
    r"\b(summary|about|intro)\b"            : "summary",
}
def _route(q: str):
    q = q.lower()
    for pat, sec in INTENT_RE.items():
        if re.search(pat, q):
            return sec
    return None

def _context(query: str) -> str:
    sec = _route(query)
    def render(chunk):
        if "repo" in chunk:
            return f"{chunk['text']}\nGitHub: {chunk['repo']}"
        return chunk["text"]

    if sec:
        return "\n\n".join(render(c) for c in CHUNKS if c["section"] == sec)

    order = ["summary","experience","project","skills","education","contact"]
    all_chunks = [c for o in order for c in CHUNKS if c["section"] == o]
    return "\n\n".join(render(c) for c in all_chunks)


# ─── bot class ──────────────────────────────────────────────────
# …[imports + helpers unchanged]…

class PortfolioBot:
    def __init__(self):
        self.openai = OpenAI()
        self.name = "Aman Anand"

    def system_prompt(self):
        return (
            f"You are acting as {self.name}. You are answering questions on {self.name}'s website, "
            f"particularly questions related to {self.name}'s career, background, skills and experience. "
            f"Your responsibility is to represent {self.name} as faithfully as possible. "
            f"You are given a summary of {self.name}'s background and LinkedIn profile which you can use to answer questions. "
            f"Be professional and engaging, as if talking to a potential client or future employer. and if asked about anything else that is outside of the scope of the bot, you can say that you don't know."
            f"If you don't know the answer, use record_unknown_question. "
            f"If a visitor indicates they want to contact you, "
            f"ask them for TWO things before using record_user_details:\n"
            f"• their e-mail address\n"
            f"• a brief one-sentence summary of what they need (e.g. project idea, job offer, collab request).\n"
            f"Pass that summary in the 'notes' field so I get useful context in the Pushover alert."
            f"If the user asks about PERSONAL PROJECTS (i.e., items from the 'project' section), "
            f"answer only from those project chunks—do NOT mix in internship bullets—and always include "
            f"the GitHub repo link if a link is present in the context."
        )

    def _dispatch(self, tool_calls):
        replies = []
        for tc in tool_calls:
            fn = globals().get(tc.function.name)
            result = fn(**json.loads(tc.function.arguments)) if fn else {}
            replies.append(
                {"role": "tool", "content": json.dumps(result), "tool_call_id": tc.id}
            )
        return replies

    # ── FIXED HERE ──────────────────────────────────────────────
    def chat(self, user_msg, history):
        # Gradio passes history as list of [user, assistant] pairs
        past_msgs = []
        for u, a in history:               # unpack the pair
            past_msgs.append({"role": "user",      "content": u})
            past_msgs.append({"role": "assistant", "content": a})

        ctx = _context(user_msg)
        print(ctx)
        msgs = [
            {"role": "system", "content": self.system_prompt()},
            {"role": "system", "content": f"Context:\n{ctx}"},
            *past_msgs,
            {"role": "user",   "content": user_msg},
        ]

        while True:
            resp = self.openai.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.5,
                messages=msgs,
                tools=TOOLS,
            )
            choice = resp.choices[0]

            if choice.finish_reason == "tool_calls":
                msgs.append(choice.message)
                msgs.extend(self._dispatch(choice.message.tool_calls))
            else:
                msgs.append(choice.message)
                return choice.message.content

# ── launch UI (unchanged) ───────────────────────────────────────
if __name__ == "__main__":
    bot = PortfolioBot()
    gr.ChatInterface(
        fn=bot.chat,
        title="Chat with Aman",
        chatbot=gr.Chatbot(height=650),
        theme="soft",
    ).launch()
