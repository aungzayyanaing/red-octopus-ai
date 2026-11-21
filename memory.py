"""Persistent memory for Red Octopus AI.

Everything is stored in memory.json next to the code:
  - user profile (name, language)
  - facts the user teaches it
  - learned Q&A pairs (from /teach)
  - notes
  - conversation history (last 100 turns)

Memory survives restarts: it is loaded on start and saved after
every change.
"""

import json
import os

MEMORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "memory.json")
MAX_HISTORY = 100

DEFAULT_DATA = {
    "user": {"name": None, "lang": "en"},
    "facts": {},
    "learned": {},
    "notes": [],
    "todos": [],
    "lessons": [],
    "history": [],
}


class Memory:
    """JSON-backed memory store."""

    def __init__(self, path=MEMORY_FILE):
        self.path = path
        self.data = self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            merged = json.loads(json.dumps(DEFAULT_DATA))
            merged.update(data)
            merged["user"] = {**DEFAULT_DATA["user"], **data.get("user", {})}
            # Octo is English only — migrate any old Burmese setting.
            if merged["user"].get("lang") != "en":
                merged["user"]["lang"] = "en"
            merged["facts"] = data.get("facts", {})
            merged["learned"] = data.get("learned", {})
            merged["notes"] = data.get("notes", [])
            merged["todos"] = data.get("todos", [])
            merged["lessons"] = data.get("lessons", [])
            merged["history"] = data.get("history", [])
            return merged
        except (FileNotFoundError, json.JSONDecodeError, AttributeError):
            return json.loads(json.dumps(DEFAULT_DATA))

    def save(self):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        self.write_memory_md()

    def write_memory_md(self):
        """Also keep a human-readable MEMORY.md next to memory.json.

        The user can read it (and edit it) like a notebook; the bot
        reads the JSON, but the Markdown file is the readable twin.
        """
        d = self.data
        lines = ["# Octo Memory", ""]
        lines.append("## About you")
        lines.append("- Name: %s" % (d["user"].get("name") or "(unknown)"))
        lines.append("- Language: %s" % d["user"].get("lang", "en"))
        lines.append("")
        lines.append("## Facts")
        if d["facts"]:
            for k, v in d["facts"].items():
                lines.append("- %s: %s" % (k, v))
        else:
            lines.append("- (none yet)")
        lines.append("")
        lines.append("## Learned answers")
        if d["learned"]:
            for q, a in d["learned"].items():
                lines.append("- Q: %s" % q)
                lines.append("  A: %s" % a)
        else:
            lines.append("- (none yet)")
        lines.append("")
        lines.append("## Notes")
        if d["notes"]:
            for n in d["notes"]:
                lines.append("- %s" % n)
        else:
            lines.append("- (none yet)")
        lines.append("")
        lines.append("## Todos")
        if d.get("todos"):
            for t in d["todos"]:
                mark = "x" if t.get("done") else " "
                lines.append("- [%s] %s" % (mark, t["text"]))
        else:
            lines.append("- (none yet)")
        lines.append("")
        lines.append("## Lessons")
        if d.get("lessons"):
            for lesson in d["lessons"]:
                lines.append("- %s" % lesson)
        else:
            lines.append("- (none yet)")
        lines.append("")
        path = os.path.join(os.path.dirname(os.path.abspath(self.path)), "MEMORY.md")
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))
        except OSError:
            pass

    # ------------------------------------------------------------------
    # user profile
    # ------------------------------------------------------------------
    def set_name(self, name):
        self.data["user"]["name"] = name.strip()
        self.save()

    def get_name(self):
        return self.data["user"].get("name")

    def set_lang(self, lang):
        if lang == "en":
            self.data["user"]["lang"] = lang
            self.save()
            return True
        return False

    def get_lang(self):
        return self.data["user"].get("lang", "en")

    # ------------------------------------------------------------------
    # facts
    # ------------------------------------------------------------------
    def remember_fact(self, key, value):
        self.data["facts"][key.strip()] = value.strip()
        self.save()

    def recall_fact(self, key):
        return self.data["facts"].get(key)

    def search_facts(self, keyword):
        kw = keyword.lower()
        return {k: v for k, v in self.data["facts"].items()
                if kw in k.lower() or kw in str(v).lower()}

    def forget_fact(self, keyword):
        kw = keyword.lower()
        removed = [k for k in self.data["facts"]
                   if kw in k.lower() or kw in str(self.data["facts"][k]).lower()]
        for k in removed:
            del self.data["facts"][k]
        if removed:
            self.save()
        return removed

    # ------------------------------------------------------------------
    # learned Q&A (from /teach)
    # ------------------------------------------------------------------
    def teach(self, question, answer):
        self.data["learned"][question.strip().lower()] = answer.strip()
        self.save()

    def learned_answer(self, question):
        return self.data["learned"].get(question.strip().lower())

    def forget_learned(self, keyword):
        kw = keyword.lower()
        removed = [q for q in self.data["learned"] if kw in q]
        for q in removed:
            del self.data["learned"][q]
        if removed:
            self.save()
        return removed

    # ------------------------------------------------------------------
    # notes
    # ------------------------------------------------------------------
    def add_note(self, text):
        self.data["notes"].append(text.strip())
        self.save()
        return len(self.data["notes"])

    def list_notes(self):
        return list(self.data["notes"])

    # ------------------------------------------------------------------
    # conversation history
    # ------------------------------------------------------------------
    def add_turn(self, role, text):
        self.data["history"].append({"role": role, "text": text})
        self.data["history"] = self.data["history"][-MAX_HISTORY:]
        self.save()

    def recent_history(self, n=10):
        return self.data["history"][-n:]

    # ------------------------------------------------------------------
    # todos (persistent todo memory)
    # ------------------------------------------------------------------
    def add_todo(self, text):
        self.data.setdefault("todos", []).append({"text": text.strip(), "done": False})
        self.save()
        return len(self.data["todos"])

    def list_todos(self):
        return list(self.data.get("todos", []))

    def complete_todo(self, index):
        todos = self.data.get("todos", [])
        if 1 <= index <= len(todos):
            todos[index - 1]["done"] = True
            self.save()
            return todos[index - 1]["text"]
        return None

    def pending_todos(self):
        return [t for t in self.data.get("todos", []) if not t.get("done")]

    # ------------------------------------------------------------------
    # lessons (self-improvement notes from /improve)
    # ------------------------------------------------------------------
    def add_lesson(self, text):
        lessons = self.data.setdefault("lessons", [])
        if text not in lessons:
            lessons.append(text)
            self.save()
            return True
        return False

    def list_lessons(self):
        return list(self.data.get("lessons", []))

    # ------------------------------------------------------------------
    # checkpoints (save / rewind a session)
    # ------------------------------------------------------------------
    def checkpoint_dir(self):
        d = os.path.join(os.path.dirname(os.path.abspath(self.path)), "checkpoints")
        os.makedirs(d, exist_ok=True)
        return d

    def save_checkpoint(self, name):
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        safe = safe or "checkpoint"
        path = os.path.join(self.checkpoint_dir(), safe + ".json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        return safe

    def list_checkpoints(self):
        d = self.checkpoint_dir()
        return sorted(f[:-5] for f in os.listdir(d) if f.endswith(".json"))

    def restore_checkpoint(self, name):
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_")).strip()
        path = os.path.join(self.checkpoint_dir(), safe + ".json")
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.save()
        return True

    def summary(self):
        return {
            "name": self.get_name(),
            "lang": self.get_lang(),
            "facts": len(self.data["facts"]),
            "learned": len(self.data["learned"]),
            "notes": len(self.data["notes"]),
            "todos": len(self.pending_todos()),
            "lessons": len(self.data.get("lessons", [])),
            "history_turns": len(self.data["history"]),
        }
