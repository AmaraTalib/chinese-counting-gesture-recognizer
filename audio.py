
"""Speaks Chinese numbers 1-10.
 
mp3s are generated once with gTTS (needs internet the first time) and cached
in assets/audio/, so later runs work offline. pygame plays them without
blocking the video loop.
"""
from pathlib import Path
 
import pygame
from gtts import gTTS
 
CHARS = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五",
         6: "六", 7: "七", 8: "八", 9: "九", 10: "十"}
 
 
class NumberSpeaker:
    def __init__(self, audio_dir):
        self.dir = Path(audio_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        pygame.mixer.init()
        self.sounds = {}
 
    def prepare(self):
        """Create any missing mp3s, then load all sounds into memory."""
        for n, char in CHARS.items():
            path = self.dir / f"{n}.mp3"
            if not path.exists():
                try:
                    print(f"Generating audio for {n} ({char})...")
                    gTTS(text=char, lang="zh-CN").save(str(path))
                except Exception as e:
                    print(f"Could not generate audio for {n}: {e}")
                    continue
            self.sounds[n] = pygame.mixer.Sound(str(path))
 
    def say(self, n):
        """Play the sound for n (non-blocking). Stops any sound still playing."""
        pygame.mixer.stop()
        sound = self.sounds.get(n)
        if sound:
            sound.play()
 
