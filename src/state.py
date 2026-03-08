import threading
import time
import random
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field

from .player import AudioPlayer
from .database import (
    get_app_state, save_app_state, get_track, get_playlist_tracks,
    get_all_playlists, get_all_tracks, get_playlist, _UNSET_INSTANCE,
    get_state_data
)
from .config import STATE_SAVE_INTERVAL
from .logger import logger


@dataclass
class PlayerState:
    current_playlist_id: Optional[int] = None
    current_track_id: Optional[int] = None
    position: float = 0.0
    volume: float = 0.7
    is_playing: bool = False
    server_port: int = 8080
    shuffle: bool = False


class StateManager:
    def __init__(self, player: AudioPlayer):
        self.player = player
        self.state = PlayerState()
        self._lock = threading.RLock()
        self._auto_save_thread: Optional[threading.Thread] = None
        self._running = False
        self._listeners: List[Callable] = []
        
        self._load_state()
        self._setup_player_callbacks()
    
    def _load_state(self):
        db_state = get_app_state()
        
        self.state.volume = db_state.get('volume', 0.7)
        self.state.server_port = db_state.get('server_port', 8080)
        self.state.is_playing = db_state.get('is_playing', 0) == 1
        self.state.position = db_state.get('position', 0)
        self.state.current_playlist_id = db_state.get('current_playlist_id')
        self.state.current_track_id = db_state.get('current_track_id')
        self.state.shuffle = db_state.get('shuffle', 0) == 1
        
        self.player.set_volume(self.state.volume)
        
        if self.state.current_track_id:
            track = get_track(self.state.current_track_id)
            if track and self.player.load(track['file_path']):
                if self.state.position > 0:
                    self.player.set_position(self.state.position)
                if self.state.is_playing:
                    self.player.play()
    
    def _setup_player_callbacks(self):
        self.player.set_on_track_end(self._on_track_end)
        self.player.set_on_media_parsed(self._on_media_parsed)
    
    def _on_track_end(self):
        self.next_track()
    
    def _on_media_parsed(self):
        self.notify_listeners()
    
    def start_auto_save(self):
        self._running = True
        self._auto_save_thread = threading.Thread(target=self._auto_save_loop, daemon=True)
        self._auto_save_thread.start()
    
    def stop_auto_save(self):
        self._running = False
        if self._auto_save_thread:
            self._auto_save_thread.join(timeout=2)
    
    def _auto_save_loop(self):
        while self._running:
            time.sleep(STATE_SAVE_INTERVAL)
            if self.state.is_playing:
                with self._lock:
                    snapshot = {
                        'volume': self.state.volume,
                        'is_playing': 1 if self.state.is_playing else 0,
                        'position': self.player.get_position(),
                        'current_playlist_id': self.state.current_playlist_id,
                        'current_track_id': self.state.current_track_id,
                        'server_port': self.state.server_port,
                        'shuffle': 1 if self.state.shuffle else 0,
                    }
                save_app_state(**snapshot)
    
    def _save_state(self):
        save_app_state(
            volume=self.state.volume,
            is_playing=1 if self.state.is_playing else 0,
            position=self.player.get_position(),
            current_playlist_id=self.state.current_playlist_id,
            current_track_id=self.state.current_track_id,
            server_port=self.state.server_port,
            shuffle=1 if self.state.shuffle else 0
        )
    
    def add_listener(self, callback: Callable):
        self._listeners.append(callback)
    
    def notify_listeners(self):
        state_dict = self.get_state_dict()
        self.notify_listeners_with_state(state_dict)
    
    def notify_listeners_with_state(self, state_dict: Dict[str, Any]):
        for listener in self._listeners:
            try:
                listener(state_dict)
            except Exception:
                pass
    
    def get_state_dict(self) -> Dict[str, Any]:
        with self._lock:
            track, playlist, playlists, tracks = get_state_data(
                self.state.current_track_id,
                self.state.current_playlist_id
            )
            
            return {
                'is_playing': self.state.is_playing,
                'volume': self.state.volume,
                'position': self.player.get_position(),
                'duration': self.player.get_duration() / 1000.0,
                'current_time': self.player.get_time() / 1000.0,
                'current_track': track,
                'current_playlist': playlist,
                'server_port': self.state.server_port,
                'playlists': playlists,
                'tracks': tracks,
                'shuffle': self.state.shuffle
            }
    
    def play(self):
        state_snapshot = None
        with self._lock:
            if not self.state.current_track_id and self.state.current_playlist_id:
                tracks = get_playlist_tracks(self.state.current_playlist_id)
                if tracks:
                    self.state.current_track_id = tracks[0]['id']
                    self.player.load(tracks[0]['file_path'])
            
            if self.state.current_track_id and not self.player.get_current_file():
                track = get_track(self.state.current_track_id)
                if track:
                    self.player.load(track['file_path'])
            
            self.player.play()
            self.state.is_playing = True
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def pause(self):
        state_snapshot = None
        with self._lock:
            self.player.pause()
            self.state.is_playing = False
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def stop(self):
        state_snapshot = None
        with self._lock:
            self.player.stop()
            self.state.is_playing = False
            self.state.position = 0
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def toggle_play_pause(self):
        if self.state.is_playing:
            self.pause()
        else:
            self.play()
    
    def set_volume(self, volume: float):
        state_snapshot = None
        with self._lock:
            self.player.set_volume(volume)
            self.state.volume = volume
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def set_position(self, position: float):
        with self._lock:
            self.player.set_position(position)
            self.state.position = position
            self._save_state()
    
    def set_playlist(self, playlist_id: int):
        state_snapshot = None
        with self._lock:
            self.state.current_playlist_id = playlist_id
            tracks = get_playlist_tracks(playlist_id)
            if tracks:
                self.state.current_track_id = tracks[0]['id']
                self.player.load(tracks[0]['file_path'])
            else:
                self.state.current_track_id = None
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def play_track(self, track_id: int):
        state_snapshot = None
        with self._lock:
            track = get_track(track_id)
            if track:
                self.state.current_track_id = track_id
                self.player.load(track['file_path'])
                self.player.play()
                self.state.is_playing = True
                self._save_state()
                state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def next_track(self):
        state_snapshot = None
        with self._lock:
            if not self.state.current_playlist_id:
                return
            
            tracks = get_playlist_tracks(self.state.current_playlist_id)
            if not tracks:
                return
            
            if self.state.shuffle:
                track_ids = [t['id'] for t in tracks if t['id'] != self.state.current_track_id]
                if track_ids:
                    next_track_id = random.choice(track_ids)
                else:
                    next_track_id = self.state.current_track_id
            else:
                current_index = -1
                for i, t in enumerate(tracks):
                    if t['id'] == self.state.current_track_id:
                        current_index = i
                        break
                
                next_index = (current_index + 1) % len(tracks)
                next_track_id = tracks[next_index]['id']
            
            self.state.current_track_id = next_track_id
            for t in tracks:
                if t['id'] == next_track_id:
                    self.player.load(t['file_path'])
                    break
            
            if self.state.is_playing:
                self.player.play()
            
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def prev_track(self):
        state_snapshot = None
        with self._lock:
            if not self.state.current_playlist_id:
                return
            
            tracks = get_playlist_tracks(self.state.current_playlist_id)
            if not tracks:
                return
            
            if self.state.shuffle:
                track_ids = [t['id'] for t in tracks if t['id'] != self.state.current_track_id]
                if track_ids:
                    prev_track_id = random.choice(track_ids)
                else:
                    prev_track_id = self.state.current_track_id
            else:
                current_index = 0
                for i, t in enumerate(tracks):
                    if t['id'] == self.state.current_track_id:
                        current_index = i
                        break
                
                prev_index = (current_index - 1) % len(tracks)
                prev_track_id = tracks[prev_index]['id']
            
            self.state.current_track_id = prev_track_id
            for t in tracks:
                if t['id'] == prev_track_id:
                    self.player.load(t['file_path'])
                    break
            
            if self.state.is_playing:
                self.player.play()
            
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def set_server_port(self, port: int):
        with self._lock:
            self.state.server_port = port
            self._save_state()
            self.notify_listeners()
    
    def toggle_shuffle(self):
        state_snapshot = None
        with self._lock:
            self.state.shuffle = not self.state.shuffle
            self._save_state()
            state_snapshot = self.get_state_dict()
        
        if state_snapshot:
            self.notify_listeners_with_state(state_snapshot)
    
    def save_state(self):
        with self._lock:
            self._save_state()
