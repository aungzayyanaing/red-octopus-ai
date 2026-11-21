"""Every /command for Red Octopus AI.

dispatch(text, ctx) -> (reply, should_exit)
  ctx is a SimpleNamespace with: memory, lang
  reply "__CLEAR__" means: clear the screen (handled by octo.py).
"""

import bank
import brain
import llm
import time


HELP_EN = """How to use Octo — Commands

  /help              Show this list
  /time              Tell the current time
  /date              Tell today's date
  /calc 12*8+5       Calculate (e.g. /calc 12*8+5)
  /note <text>        Save a note (e.g. /note meeting at 9 AM)
  /notes             List your saved notes
  /remember <key> = <value>   Remember a fact (e.g. /remember favorite color = red)
  /recall [word]     Search remembered facts
  /forget <word>     Delete remembered facts, answers or notes
  /teach <question> | <answer>   Teach an answer (e.g. /teach what is the capital of Myanmar? | Naypyidaw)
  /memory            Show what Octo remembers about you
  /brain             Show brain chips and memory count
  /llm [provider]    Show free AI providers / test one (e.g. /llm groq)
  /name <name>       Tell Octo your name (e.g. /name Aung)
  /todo <text>       Add a todo (e.g. /todo buy a book)
  /todos             List your todos
  /done <number>     Mark a todo done (e.g. /done 1)
  /improve           Find questions Octo could not answer and save them as lessons
  /lessons           List saved lessons
  /checkpoint <name> Save the current memory as a checkpoint
  /checkpoints       List checkpoints
  /rewind <name>     Restore a checkpoint
  /joke              Tell a joke
  /clear             Clear the screen
  /exit              Quit

You can also just chat. For example — hello, how are you, what time is it?
One-shot mode: python octo.py "question" answers once and exits.
"""


def _help_text():
    return HELP_EN


def dispatch(text, ctx):
    """Handle one /command line. Returns (reply, should_exit)."""
    mem = ctx.memory
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        return _help_text(), False

    if cmd == "/time":
        return brain.tell_time(), False

    if cmd == "/date":
        return brain.tell_date(), False

    if cmd == "/calc":
        if not arg:
            return "Write the expression to calculate. Example: /calc 12*8+5", False
        try:
            result = brain.safe_calc(arg)
            return "%s = %s" % (arg, result), False
        except Exception:
            return "I cannot calculate that. Only numbers and + - * / % ( ) are allowed.", False

    if cmd == "/note":
        if not arg:
            return "Write the note. Example: /note meeting at 9 AM", False
        n = mem.add_note(arg)
        return "Note #%d saved." % n, False

    if cmd == "/notes":
        notes = mem.list_notes()
        if not notes:
            return "No notes yet. Save one with /note <text>.", False
        lines = ["Your notes:"]
        for i, note in enumerate(notes, 1):
            lines.append("  %d. %s" % (i, note))
        return "\n".join(lines), False

    if cmd == "/remember":
        if not arg:
            return "Write what to remember. Example: /remember favorite color = red", False
        sep = "=" if "=" in arg else (":" if ":" in arg else None)
        if sep is None:
            key = "fact-%d" % (len(mem.data["facts"]) + 1)
            mem.remember_fact(key, arg)
            return "Remembered: \"%s\"." % arg, False
        key, value = arg.split(sep, 1)
        key, value = key.strip(), value.strip()
        if not key or not value:
            return "Format is /remember <key> = <value>.", False
        mem.remember_fact(key, value)
        return "Remembered: %s is %s." % (key, value), False

    if cmd == "/recall":
        if arg:
            found = mem.search_facts(arg)
            learned = {q: a for q, a in mem.data["learned"].items()
                       if arg.lower() in q.lower()}
            if found or learned:
                lines = ["Found:"]
                for k, v in found.items():
                    lines.append("  %s = %s" % (k, v))
                for q, a in learned.items():
                    lines.append("  When asked \"%s\" I answer \"%s\"" % (q, a))
                return "\n".join(lines), False
            return "Nothing remembered about \"%s\"." % arg, False
        facts = mem.data["facts"]
        learned = mem.data["learned"]
        if not facts and not learned:
            return "Nothing remembered yet. Use /remember to teach me.", False
        lines = ["Remembered facts:"]
        for k, v in facts.items():
            lines.append("  %s = %s" % (k, v))
        if learned:
            lines.append("Answers taught:")
            for q, a in learned.items():
                lines.append("  “%s” → “%s”" % (q, a))
        return "\n".join(lines), False

    if cmd == "/forget":
        if not arg:
            return "Write what to forget. Example: /forget color", False
        gone_facts = mem.forget_fact(arg)
        gone_learned = mem.forget_learned(arg)
        notes_before = len(mem.data["notes"])
        mem.data["notes"] = [n for n in mem.data["notes"] if arg.lower() not in n.lower()]
        gone_notes = notes_before - len(mem.data["notes"])
        if gone_notes:
            mem.save()
        total = len(gone_facts) + len(gone_learned) + gone_notes
        if total:
            return "Deleted %d item(s) about \"%s\"." % (total, arg), False
        return "Nothing remembered about \"%s\"." % arg, False

    if cmd == "/teach":
        if "|" not in arg:
            return "Format is /teach <question> | <answer>.", False
        question, answer = arg.split("|", 1)
        question, answer = question.strip(), answer.strip()
        if not question or not answer:
            return "Write both the question and the answer.", False
        mem.teach(question, answer)
        return "Learned! When you ask \"%s\" I will answer \"%s\"." % (question, answer), False

    if cmd == "/memory":
        s = mem.summary()
        lines = ["What Octo remembers:"]
        lines.append("  Name: %s" % (s["name"] or "unknown"))
        lines.append("  Language: %s" % s["lang"])
        lines.append("  Facts remembered: %d" % s["facts"])
        lines.append("  Answers taught: %d" % s["learned"])
        lines.append("  Notes: %d" % s["notes"])
        lines.append("  Todos pending: %d" % s["todos"])
        lines.append("  Lessons: %d" % s["lessons"])
        lines.extend(bank.gauge_lines())
        lines.append("  Conversation turns: %d" % s["history_turns"])
        return "\n".join(lines), False

    if cmd == "/brain":
        return "\n".join(bank.brain_lines()), False

    if cmd == "/llm":
        if not arg:
            lines = ["Free AI providers (5 — no Gemini):"]
            for name, ready, model, note in llm.provider_status():
                mark = "[+]" if ready else "[ ]"
                lines.append("  %s %-11s %s (%s)" % (mark, name, model, note))
            last = llm.last_used_provider()
            if last:
                lines.append("  Last provider that answered: %s" % last)
            lines.append("  Add keys in .env. Reorder with OCTO_LLM_ORDER=groq,pollinations.")
            return "\n".join(lines), False
        name = arg.strip().lower()
        if name not in ("groq", "openrouter", "mistral", "nvidia", "pollinations"):
            return "Unknown provider. Available: groq, openrouter, mistral, nvidia, pollinations.", False
        start = time.time()
        reply, used = llm.ask_provider(
            "Say OK in one short sentence.", mem)
        took = time.time() - start
        if reply:
            return "%s works (%.1f s). Reply: %s" % (used, took, reply), False
        return "%s is not answering right now. Check the key or try another provider." % name, False

    if cmd == "/todo":
        if not arg:
            return "Write the todo. Example: /todo buy a book", False
        n = mem.add_todo(arg)
        return "Todo #%d added." % n, False

    if cmd == "/todos":
        todos = mem.list_todos()
        if not todos:
            return "No todos yet. Add one with /todo <text>.", False
        lines = ["Your todos:"]
        for i, t in enumerate(todos, 1):
            mark = "[x]" if t.get("done") else "[ ]"
            lines.append("  %d. %s %s" % (i, mark, t["text"]))
        return "\n".join(lines), False

    if cmd == "/done":
        if not arg.isdigit():
            return "Write the number. Example: /done 1", False
        done = mem.complete_todo(int(arg))
        if done:
            return "Done: \"%s\"." % done, False
        return "No todo #%s." % arg, False

    if cmd == "/improve":
        from collections import Counter
        history = mem.data["history"]
        fb_mm = brain.fallback("mm")
        fb_en = brain.fallback("en")
        unanswered = []
        seen = set()
        for i in range(len(history) - 1):
            if history[i]["role"] == "user" and history[i + 1]["role"] == "octo":
                if history[i + 1]["text"] in (fb_mm, fb_en):
                    q = history[i]["text"]
                    if q not in seen and not q.startswith("/"):
                        seen.add(q)
                        unanswered.append(q)
        counts = Counter(t["text"] for t in history if t["role"] == "user")
        repeated = [q for q, c in counts.items()
                    if c >= 2 and mem.learned_answer(q) is None
                    and q not in seen and not q.startswith("/")]
        for q in unanswered + repeated:
            mem.add_lesson("Teach me: %s" % q)
        lines = ["Self-improvement check:"]
        lines.append("  Conversation turns checked: %d" % len(history))
        if unanswered:
            lines.append("  Questions I could not answer (%d):" % len(unanswered))
            for q in unanswered[:5]:
                lines.append("    - %s" % q)
        else:
            lines.append("  No unanswered questions.")
        if repeated:
            lines.append("  Repeated questions (%d):" % len(repeated))
            for q in repeated[:5]:
                lines.append("    - %s" % q)
        lines.append("  Saved as lessons. See them with /lessons. "
                         "Teach me with /teach <question> | <answer>.")
        return "\n".join(lines), False

    if cmd == "/lessons":
        lessons = mem.list_lessons()
        if not lessons:
            return "No lessons yet. Run /improve to analyze.", False
        lines = ["Lessons:"]
        for i, lesson in enumerate(lessons, 1):
            lines.append("  %d. %s" % (i, lesson))
        return "\n".join(lines), False

    if cmd == "/checkpoint":
        name = arg or "session"
        safe = mem.save_checkpoint(name)
        return "Checkpoint \"%s\" saved." % safe, False

    if cmd == "/checkpoints":
        cps = mem.list_checkpoints()
        if not cps:
            return "No checkpoints yet. Save one with /checkpoint <name>.", False
        lines = ["Checkpoints:"]
        for c in cps:
            lines.append("  - %s" % c)
        return "\n".join(lines), False

    if cmd == "/rewind":
        if not arg:
            return "Write the name. Example: /rewind session", False
        if mem.restore_checkpoint(arg):
            ctx.lang = "en"
            return "Rewound to checkpoint \"%s\"." % arg, False
        return "No checkpoint \"%s\"." % arg, False

    if cmd == "/name":
        if not arg:
            name = mem.get_name()
            if name:
                return "Your name is %s, as far as I remember." % name, False
            return "I don't know your name yet. Tell me with /name <name>.", False
        mem.set_name(arg)
        return "Nice to meet you, %s! I will remember your name." % arg, False

    if cmd == "/joke":
        return brain.joke(), False

    if cmd == "/clear":
        return "__CLEAR__", False

    if cmd == "/exit":
        return "Goodbye! I will be right here when you come back.", True

    # unknown command
    return "Unknown command. Type /help to see all commands.", False
