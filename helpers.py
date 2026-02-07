import difflib
import string
from config import FUZZY_THRESHOLD, WRAP_LENGTH

def normalise(text):
    return text.lower().strip().translate(str.maketrans("", "", string.punctuation))

def fuzzy_match(user, correct):
    return difflib.SequenceMatcher(None, user, correct).ratio() >= FUZZY_THRESHOLD

def wrap_text(text, length=WRAP_LENGTH):
    if not text:
        return ""
    words, lines, line = str(text).split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 <= length:
            line += (" " if line else "") + w
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return "\n".join(lines)

def safe_data(field, default=""):
    return field if field else default
