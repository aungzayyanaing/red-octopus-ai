"""Every /command for Red Octopus AI.

dispatch(text, ctx) -> (reply, should_exit)
  ctx is a SimpleNamespace with: memory, lang
  reply "__CLEAR__" means: clear the screen (handled by octo.py).
"""

import brain

HELP_MM = """Octo သုံးနည်း — Command များ

  /help              ဒီစာရင်းကို ပြတယ်
  /time              အခုအချိန်ကို ပြောတယ်
  /date              ဒီနေ့ရက်စွဲကို ပြောတယ်
  /calc 12*8+5       တွက်ချက်တယ် (ဥပမာ /calc 12*8+5)
  /note <စာ>         မှတ်စုသိမ်းတယ် (ဥပမာ /note မနက် ၉ နာရီ အစည်းအဝေး)
  /notes             သိမ်းထားတဲ့ မှတ်စုတွေ ပြတယ်
  /remember <key> = <value>   အချက် မှတ်တယ် (ဥပမာ /remember အကြိုက်ဆုံးအရောင် = အနီ)
  /recall [စကားလုံး]  မှတ်ထားတာတွေ ရှာတယ်
  /forget <စကားလုံး>  မှတ်ထားတာကို ဖျက်တယ်
  /teach <မေးခွန်း> | <အဖြေ>   အဖြေ သင်ပေးတယ် (ဥပမာ /teach မြန်မာနိုင်ငံရဲ့မြို့တော်က ဘာလဲ | နေပြည်တော်)
  /memory            Octo ဘာတွေ မှတ်ထားလဲ ပြတယ်
  /name <နာမည်>      နာမည် မှတ်တယ် (ဥပမာ /name အောင်)
  /todo <စာ>         Todo ထည့်တယ် (ဥပမာ /todo စာအုပ်ဝယ်ရန်)
  /todos             Todo တွေ ပြတယ်
  /done <နံပါတ်>      Todo ပြီးသွားပြီလို့ မှတ်တယ် (ဥပမာ /done 1)
  /improve           အဖြေမပေးနိုင်ခဲ့တဲ့ မေးခွန်းတွေကို ရှာပြီး lesson အဖြစ် သိမ်းတယ်
  /lessons           သိမ်းထားတဲ့ lesson တွေ ပြတယ်
  /checkpoint <နာမည်>  အခု memory ကို checkpoint အဖြစ် သိမ်းတယ်
  /checkpoints       Checkpoint တွေ ပြတယ်
  /rewind <နာမည်>    Checkpoint တစ်ခုကို ပြန်ရောက်တယ်
  /joke              ဟာသတစ်ခု ပြောတယ်
  /lang mm|en        ဘာသာစကား ပြောင်းတယ်
  /clear             Screen ရှင်းတယ်
  /exit              ထွက်တယ်

ရိုးရိုး စကားပြောလို့လည်း ရပါတယ်။ ဥပမာ — မင်္ဂလာပါ၊ နေကောင်းလား၊ ဘာအချိန်လဲ။
တစ်ကြောင်းတည်း မေးချင်ရင် Terminal မှာ python octo.py "မေးခွန်း" လို့ ရိုက်ပါ။
"""

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
  /lang mm|en        Switch language
  /clear             Clear the screen
  /exit              Quit

You can also just chat. For example — hello, how are you, what time is it?
One-shot mode: python octo.py "question" answers once and exits.
"""


def _help_text(lang):
    return HELP_MM if lang == "mm" else HELP_EN


def _t(lang, mm, en):
    return mm if lang == "mm" else en


def dispatch(text, ctx):
    """Handle one /command line. Returns (reply, should_exit)."""
    mem = ctx.memory
    lang = ctx.lang
    parts = text.strip().split(None, 1)
    cmd = parts[0].lower()
    arg = parts[1].strip() if len(parts) > 1 else ""

    if cmd == "/help":
        return _help_text(lang), False

    if cmd == "/time":
        return brain.tell_time(lang), False

    if cmd == "/date":
        return brain.tell_date(lang), False

    if cmd == "/calc":
        if not arg:
            return _t(lang, "တွက်ချင်တဲ့ ပုံသေနည်းကို ရေးပါ။ ဥပမာ — /calc 12*8+5",
                      "Write the expression to calculate. Example: /calc 12*8+5"), False
        try:
            result = brain.safe_calc(arg)
            return _t(lang, "%s = %s" % (arg, result), "%s = %s" % (arg, result)), False
        except Exception:
            return _t(lang, "တွက်လို့မရပါဘူး။ ဂဏန်းနဲ့ + - * / % ( ) ပဲ သုံးလို့ရပါတယ်။",
                      "I cannot calculate that. Only numbers and + - * / % ( ) are allowed."), False

    if cmd == "/note":
        if not arg:
            return _t(lang, "မှတ်စုကို ရေးပါ။ ဥပမာ — /note မနက် ၉ နာရီ အစည်းအဝေး",
                      "Write the note. Example: /note meeting at 9 AM"), False
        n = mem.add_note(arg)
        return _t(lang, "မှတ်စု #%d သိမ်းပြီးပါပြီ။" % n,
                  "Note #%d saved." % n), False

    if cmd == "/notes":
        notes = mem.list_notes()
        if not notes:
            return _t(lang, "မှတ်စု မရှိသေးပါဘူး။ /note <စာ> နဲ့ သိမ်းပါ။",
                      "No notes yet. Save one with /note <text>."), False
        lines = [_t(lang, "မှတ်စုများ:", "Your notes:")]
        for i, note in enumerate(notes, 1):
            lines.append("  %d. %s" % (i, note))
        return "\n".join(lines), False

    if cmd == "/remember":
        if not arg:
            return _t(lang, "မှတ်ချင်တာကို ရေးပါ။ ဥပမာ — /remember အကြိုက်ဆုံးအရောင် = အနီ",
                      "Write what to remember. Example: /remember favorite color = red"), False
        sep = "=" if "=" in arg else (":" if ":" in arg else None)
        if sep is None:
            key = "fact-%d" % (len(mem.data["facts"]) + 1)
            mem.remember_fact(key, arg)
            return _t(lang, "မှတ်ပြီးပါပြီ။ “%s” လို့ မှတ်ထားတယ်။" % arg,
                      "Remembered: \"%s\"." % arg), False
        key, value = arg.split(sep, 1)
        key, value = key.strip(), value.strip()
        if not key or not value:
            return _t(lang, "ပုံစံက /remember <key> = <value> ပါ။",
                      "Format is /remember <key> = <value>."), False
        mem.remember_fact(key, value)
        return _t(lang, "မှတ်ပြီးပါပြီ။ %s က %s ဆိုတာ မှတ်ထားတယ်။" % (key, value),
                  "Remembered: %s is %s." % (key, value)), False

    if cmd == "/recall":
        if arg:
            found = mem.search_facts(arg)
            learned = {q: a for q, a in mem.data["learned"].items()
                       if arg.lower() in q.lower()}
            if found or learned:
                lines = [_t(lang, "ရှာတွေ့တာများ:", "Found:")]
                for k, v in found.items():
                    lines.append("  %s = %s" % (k, v))
                for q, a in learned.items():
                    lines.append(_t(lang, "  “%s” မေးရင် “%s” လို့ ဖြေမယ်" % (q, a),
                                     "  When asked \"%s\" I answer \"%s\"" % (q, a)))
                return "\n".join(lines), False
            return _t(lang, "“%s” နဲ့ ပတ်သက်တာ မှတ်ထားတာ မရှိပါဘူး။" % arg,
                      "Nothing remembered about \"%s\"." % arg), False
        facts = mem.data["facts"]
        learned = mem.data["learned"]
        if not facts and not learned:
            return _t(lang, "ဘာမှ မှတ်ထားတာ မရှိသေးပါဘူး။ /remember နဲ့ မှတ်ပါ။",
                      "Nothing remembered yet. Use /remember to teach me."), False
        lines = [_t(lang, "မှတ်ထားတာများ:", "Remembered facts:")]
        for k, v in facts.items():
            lines.append("  %s = %s" % (k, v))
        if learned:
            lines.append(_t(lang, "သင်ပေးထားတဲ့ အဖြေများ:", "Answers taught:"))
            for q, a in learned.items():
                lines.append("  “%s” → “%s”" % (q, a))
        return "\n".join(lines), False

    if cmd == "/forget":
        if not arg:
            return _t(lang, "ဖျက်ချင်တာကို ရေးပါ။ ဥပမာ — /forget အရောင်",
                      "Write what to forget. Example: /forget color"), False
        gone_facts = mem.forget_fact(arg)
        gone_learned = mem.forget_learned(arg)
        notes_before = len(mem.data["notes"])
        mem.data["notes"] = [n for n in mem.data["notes"] if arg.lower() not in n.lower()]
        gone_notes = notes_before - len(mem.data["notes"])
        if gone_notes:
            mem.save()
        total = len(gone_facts) + len(gone_learned) + gone_notes
        if total:
            return _t(lang, "“%s” နဲ့ ပတ်သက်တာ %d ခု ဖျက်ပြီးပါပြီ။" % (arg, total),
                      "Deleted %d item(s) about \"%s\"." % (total, arg)), False
        return _t(lang, "“%s” နဲ့ ပတ်သက်တာ မှတ်ထားတာ မရှိပါဘူး။" % arg,
                  "Nothing remembered about \"%s\"." % arg), False

    if cmd == "/teach":
        if "|" not in arg:
            return _t(lang, "ပုံစံက /teach <မေးခွန်း> | <အဖြေ> ပါ။",
                      "Format is /teach <question> | <answer>."), False
        question, answer = arg.split("|", 1)
        question, answer = question.strip(), answer.strip()
        if not question or not answer:
            return _t(lang, "မေးခွန်းနဲ့ အဖြေ နှစ်ခုလုံး ရေးပါ။",
                      "Write both the question and the answer."), False
        mem.teach(question, answer)
        return _t(lang, "သင်ပြီးပါပြီ။ “%s” လို့ မေးရင် “%s” လို့ ဖြေမယ်။" % (question, answer),
                  "Learned! When you ask \"%s\" I will answer \"%s\"." % (question, answer)), False

    if cmd == "/memory":
        s = mem.summary()
        lines = [_t(lang, "Octo မှတ်ထားတာများ:", "What Octo remembers:")]
        lines.append(_t(lang, "  နာမည်: %s" % (s["name"] or "မသိသေးပါ"),
                         "  Name: %s" % (s["name"] or "unknown")))
        lines.append(_t(lang, "  ဘာသာစကား: %s" % s["lang"], "  Language: %s" % s["lang"]))
        lines.append(_t(lang, "  မှတ်ထားတဲ့ အချက်: %d ခု" % s["facts"],
                         "  Facts remembered: %d" % s["facts"]))
        lines.append(_t(lang, "  သင်ပေးထားတဲ့ အဖြေ: %d ခု" % s["learned"],
                         "  Answers taught: %d" % s["learned"]))
        lines.append(_t(lang, "  မှတ်စု: %d ခု" % s["notes"], "  Notes: %d" % s["notes"]))
        lines.append(_t(lang, "  Todo (မပြီးသေးတာ): %d ခု" % s["todos"],
                         "  Todos pending: %d" % s["todos"]))
        lines.append(_t(lang, "  Lesson: %d ခု" % s["lessons"], "  Lessons: %d" % s["lessons"]))
        lines.append(_t(lang, "  စကားပြောမှတ်တမ်း: %d ကြောင်း" % s["history_turns"],
                         "  Conversation turns: %d" % s["history_turns"]))
        return "\n".join(lines), False

    if cmd == "/todo":
        if not arg:
            return _t(lang, "လုပ်စရာကို ရေးပါ။ ဥပမာ — /todo စာအုပ်ဝယ်ရန်",
                      "Write the todo. Example: /todo buy a book"), False
        n = mem.add_todo(arg)
        return _t(lang, "Todo #%d ထည့်ပြီးပါပြီ။" % n, "Todo #%d added." % n), False

    if cmd == "/todos":
        todos = mem.list_todos()
        if not todos:
            return _t(lang, "Todo မရှိသေးပါဘူး။ /todo <စာ> နဲ့ ထည့်ပါ။",
                      "No todos yet. Add one with /todo <text>."), False
        lines = [_t(lang, "Todo များ:", "Your todos:")]
        for i, t in enumerate(todos, 1):
            mark = "[x]" if t.get("done") else "[ ]"
            lines.append("  %d. %s %s" % (i, mark, t["text"]))
        return "\n".join(lines), False

    if cmd == "/done":
        if not arg.isdigit():
            return _t(lang, "နံပါတ်ကို ရေးပါ။ ဥပမာ — /done 1",
                      "Write the number. Example: /done 1"), False
        done = mem.complete_todo(int(arg))
        if done:
            return _t(lang, "ပြီးသွားပါပြီ။ “%s”" % done, "Done: \"%s\"." % done), False
        return _t(lang, "Todo #%s မရှိပါဘူး။" % arg, "No todo #%s." % arg), False

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
        lines = [_t(lang, "Octo ကို ပိုတော်အောင် လုပ်မယ် — စစ်ဆေးမှု:",
                         "Self-improvement check:")]
        lines.append(_t(lang, "  စစ်တဲ့ စကားပြောမှတ်တမ်း: %d ကြောင်း" % len(history),
                         "  Conversation turns checked: %d" % len(history)))
        if unanswered:
            lines.append(_t(lang, "  အဖြေမပေးနိုင်ခဲ့တဲ့ မေးခွန်း (%d ခု):" % len(unanswered),
                             "  Questions I could not answer (%d):" % len(unanswered)))
            for q in unanswered[:5]:
                lines.append("    - %s" % q)
        else:
            lines.append(_t(lang, "  အဖြေမပေးနိုင်ခဲ့တာ မရှိပါဘူး။",
                             "  No unanswered questions."))
        if repeated:
            lines.append(_t(lang, "  ခဏခဏ မေးတဲ့ မေးခွန်း (%d ခု):" % len(repeated),
                             "  Repeated questions (%d):" % len(repeated)))
            for q in repeated[:5]:
                lines.append("    - %s" % q)
        lines.append(_t(lang, "  Lesson အဖြစ် သိမ်းပြီးပါပြီ။ /lessons နဲ့ ကြည့်ပါ။ "
                              "သင်ပေးဖို့ /teach <မေးခွန်း> | <အဖြေ> ကို သုံးပါ။",
                         "  Saved as lessons. See them with /lessons. "
                         "Teach me with /teach <question> | <answer>."))
        return "\n".join(lines), False

    if cmd == "/lessons":
        lessons = mem.list_lessons()
        if not lessons:
            return _t(lang, "Lesson မရှိသေးပါဘူး။ /improve လို့ ရိုက်ပြီး စစ်ပါ။",
                      "No lessons yet. Run /improve to analyze."), False
        lines = [_t(lang, "Lessons:", "Lessons:")]
        for i, lesson in enumerate(lessons, 1):
            lines.append("  %d. %s" % (i, lesson))
        return "\n".join(lines), False

    if cmd == "/checkpoint":
        name = arg or "session"
        safe = mem.save_checkpoint(name)
        return _t(lang, "Checkpoint “%s” သိမ်းပြီးပါပြီ။" % safe,
                  "Checkpoint \"%s\" saved." % safe), False

    if cmd == "/checkpoints":
        cps = mem.list_checkpoints()
        if not cps:
            return _t(lang, "Checkpoint မရှိသေးပါဘူး။ /checkpoint <နာမည်> နဲ့ သိမ်းပါ။",
                      "No checkpoints yet. Save one with /checkpoint <name>."), False
        lines = [_t(lang, "Checkpoints:", "Checkpoints:")]
        for c in cps:
            lines.append("  - %s" % c)
        return "\n".join(lines), False

    if cmd == "/rewind":
        if not arg:
            return _t(lang, "နာမည်ကို ရေးပါ။ ဥပမာ — /rewind session",
                      "Write the name. Example: /rewind session"), False
        if mem.restore_checkpoint(arg):
            ctx.lang = mem.get_lang()
            return _t(lang, "Checkpoint “%s” ကို ပြန်ရောက်ပြီးပါပြီ။" % arg,
                      "Rewound to checkpoint \"%s\"." % arg), False
        return _t(lang, "Checkpoint “%s” မရှိပါဘူး။" % arg,
                  "No checkpoint \"%s\"." % arg), False

    if cmd == "/name":
        if not arg:
            name = mem.get_name()
            if name:
                return _t(lang, "ဆရာ့နာမည်က %s လို့ မှတ်ထားတယ်။" % name,
                          "Your name is %s, as far as I remember." % name), False
            return _t(lang, "နာမည် မသိသေးပါဘူး။ /name <နာမည်> လို့ ပြောပေးပါ။",
                      "I don't know your name yet. Tell me with /name <name>."), False
        mem.set_name(arg)
        return _t(lang, "မှတ်ပြီးပါပြီ၊ %s။ တွေ့ရတာ ဝမ်းသာပါတယ်။" % arg,
                  "Nice to meet you, %s! I will remember your name." % arg), False

    if cmd == "/joke":
        return brain.joke(lang), False

    if cmd == "/clear":
        return "__CLEAR__", False

    if cmd == "/lang":
        if arg in ("mm", "en"):
            mem.set_lang(arg)
            ctx.lang = arg
            return (_t("mm", "ဘာသာစကားကို မြန်မာလို ပြောင်းပြီးပါပြီ။",
                       "Language switched to Burmese.")
                    if arg == "mm" else
                    _t("en", "ဘာသာစကားကို မြန်မာလို ပြောင်းပြီးပါပြီ။",
                       "Language switched to English.")), False
        return _t(lang, "သုံးလို့ရတာက /lang mm ဒါမှမဟုတ် /lang en ပါ။",
                  "Use /lang mm or /lang en."), False

    if cmd == "/exit":
        return _t(lang, "ပြန်လာခဲ့ပါ။ ကျွန်တော် ဒီမှာပဲ စောင့်နေမယ်။",
                  "Goodbye! I will be right here when you come back."), True

    # unknown command
    return _t(lang, "အဲ့ဒီ command ကို မသိပါဘူး။ /help လို့ ရိုက်ပြီး ကြည့်ပါ။",
              "Unknown command. Type /help to see all commands."), False
