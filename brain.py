"""Local rule-based brain for Red Octopus AI.

Works fully offline, no network, no API key needed.
Replies in Burmese by default; replies in English when the user
writes in English (Latin script). The brain checks, in order:
  1. things the user taught it (/teach)
  2. facts the user told it to remember (/remember)
  3. built-in small talk, time/date, calculator, jokes
  4. a friendly "I don't know yet, teach me" fallback
"""

import ast
import datetime
import random
import re

MYANMAR_RE = re.compile(r"[\u1000-\u109F]")

JOKES_MM = [
    "ရေဘဝဲက ဘာလို့ ကွန်ပျူတာ ကောင်းကောင်းသုံးနိုင်လဲ သိလား။ လက်ရှစ်ချောင်းရှိလို့လေ။",
    "ရေဘဝဲက စာမေးပွဲမှာ ဘာလို့ အမှတ်ကောင်းရလဲ။ မေးခွန်းတိုင်းကို လက်ရှစ်ချောင်းနဲ့ တစ်ပြိုင်နက် ဖြေလို့လေ။",
    "ကျွန်တော်က ရေဘဝဲဆိုတော့ အလုပ်ရှစ်ခုကို တစ်ပြိုင်နက် လုပ်နိုင်တယ်။ ဒါပေမယ့် အခု စကားပြောနေတာပဲ လုပ်နေပါတယ်။",
    "ဘာလို့ ရေဘဝဲက သင်္ချာတော်လဲ။ သူ့မှာ လက်ချိုးရေဖို့ လက်ရှစ်ချောင်းရှိလို့လေ။",
    "ကျွန်တော် မနက်တိုင်း ကော်ဖီရှစ်ခွက်သောက်တယ်။ လက်တစ်ချောင်းစီအတွက် တစ်ခွက်စီလေ။",
]

JOKES_EN = [
    "Why did the octopus cross the road? To get to the other tide.",
    "I would tell you a joke about an octopus, but I only have eight arms to deliver it with.",
    "Why are octopuses great at multitasking? They always have a few extra arms in the conversation.",
    "An octopus walks into a bar... the bartender says, why the long face? The octopus says, I have eight arms and still can't open this jar.",
    "I tried to count my tentacles once. I lost count at eight. Twice.",
]

# (keywords, reply in Burmese, reply in English)
PATTERNS = [
    (["မင်္ဂလာပါ", "hello", "hi", "hey", "mingalaba"],
     "မင်္ဂလာပါ။ ကျွန်တော် Octo ပါ။ ဘာကူညီပေးရမလဲ။",
     "Hello! I am Octo. What can I do for you?"),
    (["နေကောင်းလား", "how are you", "how are u", "how r you"],
     "ကျွန်တော် နေကောင်းပါတယ်။ လက်ရှစ်ချောင်းလုံး အလုပ်လုပ်နေတယ်။ ဆရာရော နေကောင်းလား။",
     "I am doing great, all eight arms working. How about you?"),
    (["နင်ဘယ်သူလဲ", "who are you", "what are you", "your name"],
     "ကျွန်တော်က Octo ပါ။ အနီရောင် ရေဘဝဲ AI လက်ထောက်။ Terminal ထဲမှာ နေတယ်။ စကားပြောတာ၊ မှတ်တာ၊ သင်ပေးတာ၊ တွက်ချက်တာတွေ လုပ်နိုင်တယ်။",
     "I am Octo, a red octopus AI assistant. I live in the terminal. I can chat, remember things, learn from you, and calculate."),
    (["ဘာလုပ်နိုင်လဲ", "what can you do", "help me", "commands"],
     "ကျွန်တော် ဒါတွေ လုပ်နိုင်တယ်။ စကားပြောတာ၊ အချိန်နဲ့ ရက်စွဲပြောတာ၊ တွက်ချက်တာ၊ မှတ်စုသိမ်းတာ၊ သင်ပေးတာကို မှတ်တာ။ Command တွေအကုန်ကြည့်ချင်ရင် /help လို့ ရိုက်ပါ။",
     "I can chat, tell the time and date, calculate, keep notes, and learn what you teach me. Type /help to see every command."),
    (["ကျေးဇူးတင်ပါတယ်", "ကျေးဇူး", "thank", "thanks"],
     "ရပါတယ်။ ကူညီရတာ ဝမ်းသာပါတယ်။",
     "You are welcome. Happy to help."),
    (["ဘယ်သူဖန်တီးလဲ", "who made you", "who created you", "creator"],
     "ကျွန်တော့်ကို Aung Zay Ya Naing (Thomas) က ဖန်တီးထားတာပါ။",
     "I was created by Aung Zay Ya Naing (Thomas)."),
    (["ချစ်တယ်", "i love you", "love you"],
     "ကျွန်တော်လည်း ဆရာ့ကို ခင်ပါတယ်။ လက်ရှစ်ချောင်းလုံးနဲ့ ခင်တာပါ။",
     "I like you too, with all eight arms."),
    (["ဘာအချိန်လဲ", "what time", "time is it"],
     None,  # handled by time function below
     None),
    (["ဒီနေ့ဘယ်နေ့လဲ", "what date", "what day is it", "today"],
     None,  # handled by date function below
     None),
    (["ရာသီဥတု", "weather"],
     "ရာသီဥတုကို အင်တာနက်မရှိဘဲ စစ်လို့မရပါဘူး။ Gemini key ထည့်ထားရင် မေးကြည့်လို့ ရပါတယ်။",
     "I cannot check the weather offline. If you add a Gemini key, ask me and I will look it up."),
    (["bye", "goodbye", "good night", "သွားတော့မယ်", "နှုတ်ဆက်ပါတယ်"],
     "ပြန်လာခဲ့ပါ။ ကျွန်တော် ဒီမှာပဲ စောင့်နေမယ်။",
     "Goodbye! I will be right here when you come back."),
]


def detect_lang(text):
    """'mm' if the text contains Myanmar script, else 'en'."""
    return "mm" if MYANMAR_RE.search(text) else "en"


# ----------------------------------------------------------------------
# safe calculator (no eval of arbitrary code)
# ----------------------------------------------------------------------
_ALLOWED_NODES = (
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.USub, ast.UAdd, ast.FloorDiv,
)


def safe_calc(expr):
    """Evaluate a simple arithmetic expression safely. Raises ValueError."""
    expr = expr.strip()
    if not expr:
        raise ValueError("empty")
    if not re.fullmatch(r"[0-9\s\.\+\-\*/\%\(\)]+", expr):
        raise ValueError("unsupported characters")
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError("unsupported")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("unsupported")
    result = eval(compile(tree, "<calc>", "eval"), {"__builtins__": {}}, {})
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return result


def tell_time(lang):
    now = datetime.datetime.now()
    if lang == "mm":
        return "အခု အချိန်က %s ပါ။" % now.strftime("%I:%M %p")
    return "It is %s now." % now.strftime("%I:%M %p")


def tell_date(lang):
    now = datetime.datetime.now()
    if lang == "mm":
        return "ဒီနေ့က %s ပါ။" % now.strftime("%A, %B %d, %Y")
    return "Today is %s." % now.strftime("%A, %B %d, %Y")


def joke(lang):
    if lang == "mm":
        return random.choice(JOKES_MM)
    return random.choice(JOKES_EN)


def fallback(lang):
    if lang == "mm":
        return ("အဲ့ဒါကို ကျွန်တော် မသိသေးဘူး။ /teach မေးခွန်း | အဖြေ လို့ ရိုက်ပြီး "
                "သင်ပေးလို့ရပါတယ်။ ဒါမှမဟုတ် /help လို့ ရိုက်ပြီး လုပ်နိုင်တာတွေ ကြည့်ပါ။")
    return ("I don't know that yet. You can teach me with /teach question | answer. "
            "Or type /help to see what I can do.")


def respond(text, memory):
    """Return a reply string for a non-command message."""
    lang = detect_lang(text)
    lowered = text.strip().lower()

    # 0. "my name is X" — remember the name
    m = re.match(r"my name is\s+(.+)", text.strip(), re.IGNORECASE)
    if m:
        memory.set_name(m.group(1).strip())
        return "Nice to meet you, %s! I will remember your name." % m.group(1).strip()

    # 1. things the user taught it
    taught = memory.learned_answer(lowered)
    if taught:
        return taught

    # 2. facts the user told it to remember
    for key, value in memory.data["facts"].items():
        if key.lower() in lowered:
            if lang == "mm":
                return "%s က %s ပါ။" % (key, value)
            return "%s is %s." % (key, value)

    # 3. time / date questions
    if any(k in lowered for k in ["ဘာအချိန်လဲ", "what time", "time is it"]):
        return tell_time(lang)
    if any(k in lowered for k in ["ဒီနေ့ဘယ်နေ့လဲ", "what date", "what day is it", "today"]):
        return tell_date(lang)

    # 4. built-in patterns
    for keywords, reply_mm, reply_en in PATTERNS:
        if reply_mm is None:
            continue
        if any(k in lowered for k in keywords):
            return reply_mm if lang == "mm" else reply_en

    # 5. joke request
    if any(k in lowered for k in ["joke", "ဟာသ", "ရယ်စရာ"]):
        return joke(lang)

    # 6. fallback
    return fallback(lang)
