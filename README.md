
# 🗂️ Portfolio-Bot — a 5-minute chatbot for your personal site  
Lightweight, no database, just JSON + OpenAI function-calling.

![demo](assets/demo.gif)

## What it does
* Answers “About”, “Projects”, “Skills”, etc. as **you**.
* Logs every unknown question to your phone via **Pushover**.
* Captures visitor e-mails + a one-line pitch, sends the lead to Pushover too.
* Runs locally with **Gradio**; deploy on Render/Fly/Heroku the same way.

---

## 1 · Clone & install
```bash
git clone https://github.com/<your-handle>/portfolio-bot.git
cd portfolio-bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt        # gradio, openai, python-dotenv, requests
```

---

## 2 · Create `data/chunks.json`
We keep content in a single file, each record ≤ 350 tokens.

### Easiest: let ChatGPT format it
1. Open GPT → paste your résumé & LinkedIn “About” text.  
2. Prompt:  
   > “Turn this into a JSON list of chunks.  
   >  One chunk per **coherent idea**: summary paragraph, each job, each project, skills, education, contact.  
   >  Keys: `id`, `section`, `text`, and for projects add `repo` if you have one.  
   >  Section must be one of `summary, experience, project, skills, education, contact`.”  
3. Copy the assistant’s response → save as `data/chunks.json`.

### Manual template
```jsonc
[
  { "id":"summary",
    "section":"summary",
    "text":"2nd-year CS undergrad focusing on applied ML…" },

  { "id":"exp_videoverse",
    "section":"experience",
    "text":"Machine-Learning Engineer Intern at VideoVerse (Aug–Nov 2024)…" },

  { "id":"prj_fire_detection",
    "section":"project",
    "repo":"https://github.com/NeuralNoble/fire-detection",
    "text":"Drone fire-detection system using YOLOv8-Nano…" },

  { "id":"skills_core",
    "section":"skills",
    "text":"Python · PyTorch · TensorFlow · AWS · Docker…" },

  { "id":"contact",
    "section":"contact",
    "text":"✉️ you@example.com · 🔗 linkedin.com/in/you · 💻 github.com/you" }
]
```

> **Tip:** keep chunks < 350 tokens so the model can fit several in context.

---

## 3 · Add secrets
Create `.env` in project root:
```env
OPENAI_API_KEY=sk-…
PUSHOVER_TOKEN=…
PUSHOVER_USER=…
```

---

## 4 · Run
```bash
python chat.py
```
Gradio prints a local URL (add `share=True` in `launch()` if you want a public link).

---

## 5 · How it works (quick tour)

| File            | Role |
|-----------------|------|
| `chat.py`       | Loads chunks, routes queries, calls GPT-4o-mini, dispatches tool calls. |
| `data/chunks.json` | Your knowledge base (replace with your own). |
| `requirements.txt` | Minimal deps. |
| `assets/`       | Optional GIF / screenshots for README. |

The bot routes a user query with a regex table:

| Regex hit | Section pulled into context |
|-----------|-----------------------------|
| `project|github|built`  | `project` |
| `experience|job`        | `experience` |
| `skill|tech|tool`       | `skills` |
| …                       | … |

It then sends:

```
system
└── persona + instructions
context
└── only the relevant chunks
user
└── original question
```

to OpenAI.  
If the answer is unknown, GPT calls `record_unknown_question(question)`.  
If it captures contact details, GPT calls  
`record_user_details(email, name, notes)`.

Both functions send you a structured Pushover notification.



  

PRs welcome!

---


