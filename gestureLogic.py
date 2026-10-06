

"""Turns MediaPipe hand landmarks into a Chinese-style number (1-10).
 
Key idea: instead of comparing y-coordinates (breaks when your hand tilts),
we compare DISTANCES to the wrist. A finger is "extended" when its tip is
farther from the wrist than the joint below it (the PIP joint).
 
Landmark reference:
 0 wrist | thumb 1-4 | index 5-8 | middle 9-12 | ring 13-16 | pinky 17-20
 (tips are 4, 8, 12, 16, 20)
"""
import math
from collections import Counter, deque
 
# ---- Tunable thresholds (adjust if a gesture is flaky) -------------------
THUMB_OUT_RATIO = 1.2    # thumb tip vs. thumb base distance to pinky knuckle
PINCH_RATIO = 0.40       # for 7: tip-to-tip distance / palm size
HOOK_RATIO = 1.3         # for 9: index PIP lift above knuckle / its MCP dist
# --------------------------------------------------------------------------
 
FINGERS = {            # name: (mcp, pip, tip)
    "index": (5, 6, 8),
    "middle": (9, 10, 12),
    "ring": (13, 14, 16),
    "pinky": (17, 18, 20),
}
 
 
def _d(lm, a, b):
    """2D distance between two landmarks (normalized coordinates)."""
    return math.hypot(lm[a].x - lm[b].x, lm[a].y - lm[b].y)
 
 
def finger_states(lm):
    """Return {'thumb':bool, 'index':bool, ...}; True = extended."""
    states = {}
    for name, (_, pip, tip) in FINGERS.items():
        states[name] = _d(lm, tip, 0) > _d(lm, pip, 0)
 
    # Thumb moves sideways, so compare against the pinky knuckle (17):
    # extended -> tip is far from 17, folded -> tip sits near/over the palm.
    states["thumb"] = _d(lm, 4, 17) > THUMB_OUT_RATIO * _d(lm, 2, 17)
    return states
 
 
def classify(lm):
    """Return an int 1-10, or None if the pose isn't recognised."""
    s = finger_states(lm)
    t, i, m, r, p = (s["thumb"], s["index"], s["middle"], s["ring"], s["pinky"])
    palm = _d(lm, 0, 9)  # wrist -> middle knuckle = hand size reference
 
    # 7: thumb + index + middle tips pinched together, ring & pinky folded.
    # Tips must be away from the wrist, otherwise a fist would look like a pinch.
    if (not r and not p
            and _d(lm, 4, 8) < PINCH_RATIO * palm
            and _d(lm, 4, 12) < PINCH_RATIO * palm
            and _d(lm, 8, 0) > 1.1 * palm):
        return 7
 
    # 9: index finger hooked (PIP lifted, tip curled back), everything else folded.
    hooked = (not i) and _d(lm, 6, 0) > HOOK_RATIO * _d(lm, 5, 0)
    if hooked and not t and not m and not r and not p:
        return 9
 
    pattern = (t, i, m, r, p)
    table = {
        (False, True, False, False, False): 1,
        (False, True, True, False, False): 2,
        (False, True, True, True, False): 3,
        (False, True, True, True, True): 4,
        (True, True, True, True, True): 5,
        (True, False, False, False, True): 6,
        (True, True, False, False, False): 8,
        (False, False, False, False, False): 10,
    }
    return table.get(pattern)
 
 
class Smoother:
    """Only change the output when the same value wins most of the last frames.
 
    Stops the number from flickering while your fingers move between poses.
    """
 
    def __init__(self, window=8, needed=6):
        self.buf = deque(maxlen=window)
        self.needed = needed
        self.current = None
 
    def update(self, value):
        self.buf.append(value)
        top, count = Counter(self.buf).most_common(1)[0]
        if count >= self.needed:
            self.current = top
        return self.current
 
