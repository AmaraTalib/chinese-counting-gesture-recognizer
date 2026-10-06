

"""Chinese Counting Gesture Recognizer.
 
Keys:  q = quit   l = toggle hand skeleton   d = toggle debug (finger states)
"""
import sys
from pathlib import Path
 
import cv2
import mediapipe as mp
 
from gestureLogic import Smoother, classify, finger_states
from ui import InfoPanel

from audio import NumberSpeaker
 
BASE = Path(__file__).parent
fonts = sorted((BASE / "assets" / "fonts").glob("*.ttf"))
if not fonts:
    sys.exit("No font found. Put NotoSansSC .ttf in assets/fonts/")
FONT_PATH = fonts[0]
 
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
 
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
 
smoother = Smoother(window=8, needed=6)
panel = None
show_skeleton = True
debug = False

speaker = NumberSpeaker(BASE / "assets" / "audio")
speaker.prepare()
last_number = None
 
with mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7,
) as hands:
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
 
        if panel is None:  # build once we know the frame size
            panel = InfoPanel(FONT_PATH, frame.shape[1])
 
        results = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
 
        raw = None
        if results.multi_hand_landmarks:
            hand = results.multi_hand_landmarks[0]
            lm = hand.landmark
            raw = classify(lm)
 
            if show_skeleton:
                mp_draw.draw_landmarks(frame, hand, mp_hands.HAND_CONNECTIONS)
            if debug:
                s = finger_states(lm)
                text = " ".join(f"{k[0].upper()}:{int(v)}" for k, v in s.items())
                cv2.putText(frame, text, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                            0.9, (0, 255, 255), 2)
                cv2.putText(frame, f"raw: {raw}", (20, 80),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
 
        number = smoother.update(raw)   # stable value, no flicker
        panel.draw(frame, number)
        if number != last_number:
           if number is not None:
             speaker.say(number)
           last_number = number

        cv2.imshow("Chinese Counting Gestures", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("l"):
            show_skeleton = not show_skeleton
        elif key == ord("d"):
            debug = not debug

 
cap.release()
cv2.destroyAllWindows()
 
