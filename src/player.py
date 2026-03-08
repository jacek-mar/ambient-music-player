import vlc
import time
from pathlib import Path
from typing import Optional, Callable

from .config import DEFAULT_VOLUME


class AudioPlayer:
    def __init__(self):
        self.instance = vlc.Instance()
        self.media_player = self.instance.media_player_new()
        self.current_media: Optional[vlc.Media] = None
        self.current_file_path: Optional[str] = None
        self._volume = DEFAULT_VOLUME
        self._is_playing = False
        self._on_track_end: Optional[Callable] = None
        self._on_media_parsed: Optional[Callable] = None
        self._media_parsed = False
        
        self._set_volume(self._volume)
        self._setup_events()
    
    def _setup_events(self):
        emitter = self.media_player.event_manager()
        emitter.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
    
    def _on_media_parsed_changed(self, event):
        self._media_parsed = True
        if self._on_media_parsed:
            self._on_media_parsed()
    
    def _on_end_reached(self, event):
        self._is_playing = False
        if self._on_track_end:
            self._on_track_end()
    
    def load(self, file_path: str) -> bool:
        if not Path(file_path).exists():
            return False
        
        self._media_parsed = False
        self.current_media = self.instance.media_new(str(file_path))
        self.current_media.event_manager().event_attach(
            vlc.EventType.MediaParsedChanged, self._on_media_parsed_changed
        )
        self.media_player.set_media(self.current_media)
        self.current_file_path = file_path
        return True
    
    def play(self):
        if self.current_media:
            self.media_player.play()
            self._is_playing = True
    
    def pause(self):
        if self.media_player.can_pause():
            self.media_player.pause()
            self._is_playing = False
    
    def stop(self):
        self.media_player.stop()
        self._is_playing = False
    
    def toggle_play_pause(self):
        if self._is_playing:
            self.pause()
        else:
            self.play()
    
    def set_volume(self, volume: float):
        self._volume = max(0.0, min(1.0, volume))
        self._set_volume(self._volume)
    
    def _set_volume(self, volume: float):
        self.media_player.audio_set_volume(int(volume * 100))
    
    def get_volume(self) -> float:
        return self._volume
    
    def set_position(self, position: float):
        if self.media_player.get_length() > 0:
            self.media_player.set_position(position)
    
    def get_position(self) -> float:
        return self.media_player.get_position()
    
    def get_time(self) -> int:
        return self.media_player.get_time()
    
    def get_duration(self) -> int:
        if not self._media_parsed:
            return 0
        return self.media_player.get_length()
    
    def is_playing(self) -> bool:
        return self._is_playing
    
    def get_current_file(self) -> Optional[str]:
        return self.current_file_path
    
    def set_on_track_end(self, callback: Callable):
        self._on_track_end = callback
    
    def set_on_media_parsed(self, callback: Callable):
        self._on_media_parsed = callback
    
    def release(self):
        self.media_player.stop()
        self.media_player.release()
        self.instance.release()
