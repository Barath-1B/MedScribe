"""Stage 1 — OCR Error Injection for controlled degradation study."""

import random
import string

VISUAL_CONFUSIONS = {
    "m": ["rn", "nn"], "r": ["n", "t"],  "n": ["ri", "h"],
    "l": ["1", "I", "|"],  "I": ["l", "1", "|"], "O": ["0", "Q"],
    "0": ["O", "o"],  "o": ["0", "c"],  "1": ["l", "I"],
    "c": ["e", "o"],  "e": ["c", "a"],  "a": ["o", "e"],
    "t": ["f", "r"],  "f": ["t", "r"],  "h": ["b", "n"],
    "b": ["h", "d"],  "d": ["b", "cl"], "g": ["q", "9"],
    "q": ["g", "9"],  "5": ["S", "s"],  "S": ["5", "s"],
    "8": ["B", "3"],  "B": ["8", "3"],  "u": ["v", "n"],
    "v": ["u", "w"],  "w": ["vv", "vu"],
}

_MIXED_WEIGHTS = (
    ["substitution"] * 40 + ["deletion"] * 20 + ["insertion"] * 15
    + ["merge"] * 15 + ["split"] * 10
)


def inject_errors(text: str, error_rate: float, error_type: str = "mixed") -> str:
    """Inject realistic OCR-like errors into clean text at the given rate."""
    if error_rate <= 0 or not text:
        return text

    chars = list(text)
    n_errors = max(1, int(len(chars) * error_rate))
    eligible = [i for i, c in enumerate(chars) if c not in "\n\t"]
    positions = random.sample(eligible, min(n_errors, len(eligible)))
    weights = _MIXED_WEIGHTS if error_type == "mixed" else [error_type]

    for pos in sorted(positions, reverse=True):
        if pos >= len(chars):
            continue
        etype = random.choice(weights)
        ch = chars[pos]

        if etype == "substitution":
            if ch in VISUAL_CONFUSIONS:
                chars[pos] = random.choice(VISUAL_CONFUSIONS[ch])
            elif ch.isalpha():
                pool = string.ascii_lowercase if ch.islower() else string.ascii_uppercase
                chars[pos] = random.choice(pool)
            elif ch.isdigit():
                chars[pos] = random.choice(string.digits)
        elif etype == "deletion" and ch != " ":
            chars[pos] = ""
        elif etype == "insertion":
            chars[pos] = ch + random.choice(string.ascii_lowercase)
        elif etype == "merge":
            for j in range(pos, min(pos + 15, len(chars))):
                if chars[j] == " ":
                    chars[j] = ""
                    break
        elif etype == "split" and ch != " " and ch.isalpha():
            chars[pos] = ch + " "

    return "".join(chars)
