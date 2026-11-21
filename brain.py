"""Local rule-based brain for Red Octopus AI.

Works fully offline, no network, no API key needed. English only.
The brain checks, in order:
  1. things the user taught it (/teach)
  2. facts the user told it to remember (/remember)
  3. built-in small talk, time/date, calculator, jokes
  4. a friendly "I don't know yet, teach me" fallback
"""

import ast
import datetime
import random
import re

import bank

JOKES = [
    "Why did the octopus cross the road? To get to the other tide.",
    "I would tell you a joke about an octopus, but I only have eight arms to deliver it with.",
    "Why are octopuses great at multitasking? They always have a few extra arms in the conversation.",
    "An octopus walks into a bar... the bartender says, why the long face? The octopus says, I have eight arms and still can't open this jar.",
    "I tried to count my tentacles once. I lost count at eight. Twice.",
]

# (keywords, reply)
PATTERNS = [
    (["hello", "hi", "hey"],
     "Hello! I am Octo. What can I do for you?"),
    (["how are you", "how are u", "how r you"],
     "I am doing great, all eight arms working. How about you?"),
    (["who are you", "what are you", "your name"],
     "I am Octo, a red octopus AI assistant. I live in the terminal. I can chat, remember things, learn from you, and calculate."),
    (["what can you do", "help me", "commands"],
     "I can chat, tell the time and date, calculate, keep notes, and learn what you teach me. Type /help to see every command."),
    (["thank", "thanks"],
     "You are welcome. Happy to help."),
    (["who made you", "who created you", "creator"],
     "I was created by Aung Zay Ya Naing (Thomas)."),
    (["i love you", "love you"],
     "I like you too, with all eight arms."),
    (["what time", "time is it"],
     None),  # handled by time function below
    (["what date", "what day is it", "today"],
     None),  # handled by date function below
    (["weather"],
     "I cannot check the weather offline. If you add a free API key, ask me and I will look it up."),
    (["bye", "goodbye", "good night"],
     "Goodbye! I will be right here when you come back."),
]


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


def tell_time():
    now = datetime.datetime.now()
    return "It is %s now." % now.strftime("%I:%M %p")


def tell_date():
    now = datetime.datetime.now()
    return "Today is %s." % now.strftime("%A, %B %d, %Y")


def joke():
    return random.choice(JOKES)


def fallback():
    return ("I don't know that yet. You can teach me with /teach question | answer. "
            "Or type /help to see what I can do.")


def _matches(text, keywords):
    """True if any keyword appears as a whole word (or phrase) in text.

    Plain substring matching is wrong here: "hi" hides inside "thing",
    "bye" inside "maybe", "hey" inside "they".
    """
    return any(re.search(r"\b" + re.escape(k) + r"\b", text)
               for k in keywords)


def respond(text, memory):
    """Return a reply string for a non-command message."""
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
            return "%s is %s." % (key, value)

    # 3. time / date questions
    if _matches(lowered, ["what time", "time is it"]):
        return tell_time()
    if _matches(lowered, ["what date", "what day is it", "today"]):
        return tell_date()

    # 4. built-in patterns
    for keywords, reply in PATTERNS:
        if reply is None:
            continue
        if _matches(lowered, keywords):
            return reply

    # 5. memory bank — the big offline knowledge store
    bank_answer = bank.lookup(text)
    if bank_answer:
        return bank_answer

    # 6. joke request
    if re.search(r"\bjokes?\b", lowered):
        return joke()

    # 7. fallback
    return fallback()
