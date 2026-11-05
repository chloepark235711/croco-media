"""Official character lock for Croco's Little World.

Copied VERBATIM from the owner-approved brand bible (Claude project
company/01-brand-bible.md, revision 2026-11-02 17:30 MT: closed-mouth / no-teeth
standard, Pebble approved). The two-character mouth line is the one used in
company/03-content-backlog.md for Pebble scenes.

This is the ONLY character definition the automation uses. Never paraphrase it.
A design change must be approved by the owner in the brand bible first, then
copied here character-for-character.
"""
import re

CHARACTER_LOCK = 'Croco, a chubby mint-green baby crocodile with a rounded head, short snout, peach-cream belly, rosy cheeks, big chocolate-brown eyes, a gentle closed-mouth smile with no visible teeth, short arms and legs, chunky tail, wearing orange dungaree overalls with two small wooden buttons and a yellow star embroidered on the front pocket. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm.'

MOUTH_LINE = 'Mouth detail: closed-mouth smile, no teeth visible at any time.'
MOUTH_LINE_PAIR = 'Mouth detail: closed-mouth smiles for both characters, no teeth visible at any time.'

# Standard negative line; scene prompts carry it as "\nNegative: " + NEGATIVE
NEGATIVE = "no scary expressions, no sharp teeth, no rows of teeth, no teeth, no open mouth with teeth, no realistic reptile skin, no extra limbs, no text, no letters, no other franchises' characters, no flashing lights, no twinkling flashes, no fast camera moves, no hats or extra clothing, do not change the pocket star design."

PEBBLE_LOCK = 'Pebble, a small round lavender baby turtle with a cream-colored belly, a smooth lavender shell with exactly three soft sky-blue round spots, big round gray eyes, short stubby legs, a gentle closed-mouth smile, and no clothing or accessories. Soft 3D animated preschool style, gentle pastel lighting, friendly and calm.'
PEBBLE_NEGATIVE = "No clothing or accessories on Pebble, no sharp beak, do not change Pebble's lavender color or the three sky-blue shell spots, no resemblance to other franchises' turtle characters."

# Characters allowed on screen (brand bible: Croco + approved supporting character Pebble only).
APPROVED_CHARACTERS = ("Croco", "Pebble")

# Elements that contradict the bible (the first V2 draft 20261105-01 used a red
# scarf, a yellow belly and a bunny) plus the no-teeth standard and the
# "no hats or extra clothing" rule.
DRIFT_TERMS = ["scarf", "yellow belly", "bunny", "rabbit", "hat", "hats", "cap", "pajamas",
               "boots", "sharp teeth", "showing teeth", "big open mouth", "open mouth",
               "yawn", "yawning", "laughing loudly", "singing", "momo",
               "green baby crocodile with a yellow"]


def positive_part(prompt):
    """Everything before the Negative line (negatives may legitimately say 'no scary ...')."""
    return prompt.split("Negative:")[0]


def check_scene(prompt):
    """Return a list of brand problems for one scene prompt (empty list = on-model)."""
    errs = []
    if not isinstance(prompt, str) or not prompt.startswith(CHARACTER_LOCK):
        return ["prompt must start with the exact brand-bible character lock"]
    rest = positive_part(prompt)[len(CHARACTER_LOCK):]
    if "Pebble" in rest:
        if not rest.lstrip().startswith(PEBBLE_LOCK):
            errs.append("Pebble scenes need the exact Pebble lock right after the Croco lock")
        if PEBBLE_NEGATIVE not in prompt:
            errs.append("Pebble scenes need the Pebble negative line")
    if MOUTH_LINE not in prompt and MOUTH_LINE_PAIR not in prompt:
        errs.append("missing Mouth detail line (closed-mouth smile, no teeth)")
    if "\nNegative: " + NEGATIVE not in prompt:
        errs.append("missing the standard brand negative line")
    low = rest.lower()
    for t in DRIFT_TERMS:
        if re.search(rf"\b{re.escape(t)}\b", low):
            errs.append(f"off-model element: {t}")
    return errs


def scene_prompt(scene, pebble=False, extra_negative=""):
    """Build a bible-compliant prompt: lock (+ Pebble lock) + Scene + Mouth line + Negative."""
    head = CHARACTER_LOCK + (" " + PEBBLE_LOCK if pebble else "")
    mouth = MOUTH_LINE_PAIR if pebble else MOUTH_LINE
    neg = NEGATIVE + (" " + PEBBLE_NEGATIVE if pebble else "") + (" " + extra_negative if extra_negative else "")
    return f"{head} Scene: {scene} {mouth}\nNegative: {neg}"
