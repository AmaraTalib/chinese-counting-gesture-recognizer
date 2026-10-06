
"""Small white info card: number, Chinese character, pinyin.
 
OpenCV can't draw Chinese text, so each card is rendered once with Pillow,
cached, and then pasted onto the video frame (fast, no per-frame Pillow work).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
 
NUMBERS = {
    1: ("一", "yī"),
    2: ("二", "èr"),
    3: ("三", "sān"),
    4: ("四", "sì"),
    5: ("五", "wǔ"),
    6: ("六", "liù"),
    7: ("七", "qī"),
    8: ("八", "bā"),
    9: ("九", "jiǔ"),
    10: ("十", "shí"),
}
 
TEXT_DARK = (30, 30, 30)
ACCENT = (200, 30, 30)   # red for the Chinese character
MUTED = (110, 110, 110)
 
 
class InfoPanel:
    def __init__(self, font_path, frame_width, margin=20):
        # Panel is ~14% of the frame width so it stays small
        self.w = max(150, int(frame_width * 0.14))
        self.h = int(self.w * 1.15)
        self.margin = margin
        self.cache = {}
 
        h = self.h
        self.f_num = ImageFont.truetype(str(font_path), int(h * 0.20))
        self.f_char = ImageFont.truetype(str(font_path), int(h * 0.34))
        self.f_pin = ImageFont.truetype(str(font_path), int(h * 0.15))
 
    def _render(self, n):
        char, pinyin = NUMBERS[n]
        w, h = self.w, self.h
 
        panel = Image.new("RGB", (w, h), (255, 255, 255))
        d = ImageDraw.Draw(panel)
        cx = w // 2
 
        d.text((cx, h * 0.17), str(n), font=self.f_num, fill=MUTED, anchor="mm")
        d.line((w * 0.25, h * 0.30, w * 0.75, h * 0.30), fill=(220, 220, 220), width=2)
        d.text((cx, h * 0.55), char, font=self.f_char, fill=ACCENT, anchor="mm")
        d.text((cx, h * 0.86), pinyin, font=self.f_pin, fill=TEXT_DARK, anchor="mm")
 
        # Rounded-corner mask
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=18, fill=255)
 
        bgr = np.array(panel)[:, :, ::-1].copy()   # RGB -> BGR for OpenCV
        return bgr, np.array(mask) > 0
 
    def draw(self, frame, n):
        """Paste the card for number n onto the top-right of the frame."""
        if n is None:
            return
        if n not in self.cache:
            self.cache[n] = self._render(n)
        panel, mask = self.cache[n]
 
        x = frame.shape[1] - self.w - self.margin
        y = self.margin
        roi = frame[y:y + self.h, x:x + self.w]
        roi[mask] = panel[mask]
 
