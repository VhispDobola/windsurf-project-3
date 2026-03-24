"""
Audio management system for sound effects and music
"""

import pygame
import os
import math
import logging
from typing import Dict, Optional
from enum import Enum


class SoundType(Enum):
    """Types of game sounds"""
    PLAYER_SHOOT = "player_shoot"
    PLAYER_HIT = "player_hit"
    PLAYER_DASH = "player_dash"
    BOSS_HIT = "boss_hit"
    BOSS_DEFEATED = "boss_defeated"
    UPGRADE = "upgrade"
    MENU_SELECT = "menu_select"
    MENU_CONFIRM = "menu_confirm"
    EXPLOSION = "explosion"


class AudioManager:
    """Centralized audio management"""
    
    def __init__(self, sound_dir: str = "assets/sounds", music_dir: str = "assets/music"):
        self.sound_dir = sound_dir
        self.music_dir = music_dir
        self.sounds: Dict[SoundType, pygame.mixer.Sound] = {}
        self.custom_sounds: Dict[str, pygame.mixer.Sound] = {}
        self.current_music = None
        self.music_volume = 0.7
        self.sound_volume = 0.8
        self.enabled = True
        self.logger = logging.getLogger(__name__)
        
        # Initialize mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        except pygame.error as e:
            self.logger.warning("Could not initialize audio mixer: %s", e)
            self.enabled = False

    def _load_sound_from_candidates(self, filenames):
        for filename in filenames:
            path = os.path.join(self.sound_dir, filename)
            if not os.path.exists(path):
                continue
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(self.sound_volume)
                return sound
            except pygame.error as e:
                self.logger.warning("Could not load sound %s: %s", filename, e)
        return None
    
    def load_sounds(self):
        """Load standard sound files when they are present in the repo."""
        if not self.enabled:
            return
            
        sound_files = {
            SoundType.PLAYER_SHOOT: ("player_shoot.wav", "player_shoot.mp3"),
            SoundType.PLAYER_HIT: ("player_hit.wav", "player_hit.mp3"),
            SoundType.PLAYER_DASH: ("player_dash.wav", "player_dash.mp3", "blade_dash.mp3"),
            SoundType.BOSS_HIT: ("boss_hit.wav", "boss_hit.mp3"),
            SoundType.BOSS_DEFEATED: ("boss_defeated.wav", "boss_defeated.mp3"),
            SoundType.UPGRADE: ("upgrade.wav", "upgrade.mp3"),
            SoundType.MENU_SELECT: ("menu_select.wav", "menu_select.mp3"),
            SoundType.MENU_CONFIRM: ("menu_confirm.wav", "menu_confirm.mp3"),
            SoundType.EXPLOSION: ("explosion.wav", "explosion.mp3"),
        }
        
        missing = []
        for sound_type, filenames in sound_files.items():
            sound = self._load_sound_from_candidates(filenames)
            if sound is not None:
                self.sounds[sound_type] = sound
            else:
                missing.append(sound_type.value)

        if missing:
            self.logger.info(
                "Optional sound effects not bundled; continuing without: %s",
                ", ".join(missing),
            )
    
    def play_sound(self, sound_type: SoundType, volume_scale: float = 1.0):
        """Play a sound effect"""
        if not self.enabled or sound_type not in self.sounds:
            return
        
        try:
            sound = self.sounds[sound_type]
            sound.set_volume(self.sound_volume * volume_scale)
            sound.play()
        except pygame.error as e:
            self.logger.error("Error playing sound %s: %s", sound_type, e)

    def register_custom_sound(self, sound_id: str, filename: str) -> bool:
        """Register a custom sound by ID from the sound directory."""
        if not self.enabled:
            return False

        path = os.path.join(self.sound_dir, filename)
        if not os.path.exists(path):
            self.logger.warning("Custom sound file not found: %s", path)
            return False

        try:
            sound = pygame.mixer.Sound(path)
            sound.set_volume(self.sound_volume)
            self.custom_sounds[sound_id] = sound
            return True
        except pygame.error as e:
            self.logger.warning("Could not load custom sound %s: %s", filename, e)
            return False

    def play_custom_sound(self, sound_id: str, volume_scale: float = 1.0):
        """Play a registered custom sound effect."""
        if not self.enabled:
            return

        sound = self.custom_sounds.get(sound_id)
        if sound is None:
            return

        try:
            sound.set_volume(self.sound_volume * volume_scale)
            sound.play()
        except pygame.error as e:
            self.logger.error("Error playing custom sound %s: %s", sound_id, e)
    
    def play_music(self, filename: str, loops: int = -1):
        """Play background music"""
        if not self.enabled:
            return
        
        path = os.path.join(self.music_dir, filename)
        if not os.path.exists(path):
            self.logger.warning("Music file not found: %s", path)
            return
        
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(loops)
            self.current_music = filename
        except pygame.error as e:
            self.logger.error("Error playing music %s: %s", filename, e)
    
    def stop_music(self):
        """Stop current music"""
        if self.enabled:
            pygame.mixer.music.stop()
            self.current_music = None
    
    def pause_music(self):
        """Pause current music"""
        if self.enabled:
            pygame.mixer.music.pause()
    
    def resume_music(self):
        """Resume paused music"""
        if self.enabled:
            pygame.mixer.music.unpause()
    
    def set_music_volume(self, volume: float):
        """Set music volume (0.0 to 1.0)"""
        self.music_volume = max(0.0, min(1.0, volume))
        if self.enabled:
            pygame.mixer.music.set_volume(self.music_volume)
    
    def set_sound_volume(self, volume: float):
        """Set sound volume (0.0 to 1.0)"""
        self.sound_volume = max(0.0, min(1.0, volume))
        
        # Update volume for all loaded sounds
        for sound in self.sounds.values():
            sound.set_volume(self.sound_volume)
        for sound in self.custom_sounds.values():
            sound.set_volume(self.sound_volume)
    
    def is_music_playing(self) -> bool:
        """Check if music is currently playing"""
        return self.enabled and pygame.mixer.music.get_busy()
    
    def create_sound_effect(self, frequency: int, duration: int, sample_rate: int = 22050) -> pygame.mixer.Sound:
        """Generate a simple sound effect programmatically"""
        if not self.enabled:
            return None
        
        try:
            import numpy as np
            
            # Generate sine wave
            frames = int(duration * sample_rate / 1000)
            arr = np.zeros((frames, 2), dtype=np.int16)
            
            for i in range(frames):
                t = float(i) / sample_rate
                value = int(32767 * 0.3 * math.sin(2 * math.pi * frequency * t))
                arr[i] = [value, value]
            
            # Apply envelope
            for i in range(frames):
                envelope = min(1.0, float(i) / 100) * max(0.0, 1.0 - float(i) / frames)
                arr[i] = [int(val * envelope) for val in arr[i]]
            
            return pygame.sndarray.make_sound(arr)
        except ImportError:
            # Fallback if numpy is not available
            return None
        except Exception as e:
            self.logger.error("Error creating sound effect: %s", e)
            return None
    
    def play_generated_sound(self, frequency: int, duration: int):
        """Play a generated sound effect"""
        sound = self.create_sound_effect(frequency, duration)
        if sound:
            sound.set_volume(self.sound_volume)
            sound.play()
    
    def cleanup(self):
        """Clean up audio resources"""
        if self.enabled:
            pygame.mixer.quit()
