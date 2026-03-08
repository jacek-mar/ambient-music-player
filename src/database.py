import sqlite3
from pathlib import Path
from typing import Optional, List, Tuple
import os
import traceback
import shutil

from .config import DB_PATH, DATA_DIR
from .logger import logger

try:
    import mutagen
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False


def migrate_data_dir():
    """Move existing data from old project-relative location to new user data dir."""
    old_data = Path(__file__).parent.parent / "data"
    if old_data.exists() and old_data != DATA_DIR:
        for f in old_data.iterdir():
            dest = DATA_DIR / f.name
            if not dest.exists():
                shutil.move(str(f), str(dest))
                logger.info(f"Migrated {f.name} to {DATA_DIR}")


class _UNSET:
    pass

_UNSET_INSTANCE = _UNSET()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    logger.info("Creating database tables...")
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL UNIQUE,
            title TEXT,
            artist TEXT,
            duration REAL,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playlist_tracks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            playlist_id INTEGER NOT NULL,
            track_id INTEGER NOT NULL,
            position INTEGER NOT NULL,
            FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
            FOREIGN KEY (track_id) REFERENCES tracks(id) ON DELETE CASCADE,
            UNIQUE(playlist_id, track_id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_playlist_id INTEGER,
            current_track_id INTEGER,
            position REAL DEFAULT 0,
            volume REAL DEFAULT 0.7,
            is_playing INTEGER DEFAULT 0,
            server_port INTEGER DEFAULT 8080,
            shuffle INTEGER DEFAULT 0,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (current_playlist_id) REFERENCES playlists(id),
            FOREIGN KEY (current_track_id) REFERENCES tracks(id)
        )
    """)
    
    try:
        cursor.execute("ALTER TABLE app_state ADD COLUMN shuffle INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    cursor.execute("SELECT id FROM app_state WHERE id = 1")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO app_state (id, volume, server_port) 
            VALUES (1, 0.7, 8080)
        """)

    conn.commit()
    conn.close()
    logger.info("Database tables created successfully")


def read_audio_metadata(file_path: str) -> Tuple[Optional[str], Optional[str], float]:
    if not MUTAGEN_AVAILABLE:
        return None, None, 0
    
    try:
        audio = mutagen.File(file_path)
        if audio is None:
            return None, None, 0
        
        title = None
        artist = None
        duration = 0
        
        if hasattr(audio, 'tags') and audio.tags:
            title_tag = audio.tags.get('TIT2') or audio.tags.get('title')
            artist_tag = audio.tags.get('TPE1') or audio.tags.get('artist')
            
            if title_tag:
                title = str(title_tag.text[0]) if hasattr(title_tag, 'text') else str(title_tag)
            if artist_tag:
                artist = str(artist_tag.text[0]) if hasattr(artist_tag, 'text') else str(artist_tag)
        
        if hasattr(audio, 'info'):
            duration = getattr(audio.info, 'length', 0)
        
        return title, artist, duration
    except Exception:
        return None, None, 0


def add_track(file_path: str, title: str = None, artist: str = None, duration: float = 0) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    
    if title is None or artist is None or duration == 0:
        meta_title, meta_artist, meta_duration = read_audio_metadata(file_path)
        
        if title is None:
            title = meta_title if meta_title else Path(file_path).stem
        if artist is None:
            artist = meta_artist
        if duration == 0:
            duration = meta_duration
    
    try:
        cursor.execute("""
            INSERT INTO tracks (file_path, title, artist, duration)
            VALUES (?, ?, ?, ?)
        """, (file_path, title, artist, duration))
        track_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM tracks WHERE file_path = ?", (file_path,))
        track_id = cursor.fetchone()[0]
    finally:
        conn.close()
    
    return track_id


def get_track(track_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def update_track(track_id: int, title: str, artist: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tracks SET title = ?, artist = ? WHERE id = ?", 
                  (title, artist, track_id))
    conn.commit()
    conn.close()


def get_all_tracks() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tracks ORDER BY date_added DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_track(track_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tracks WHERE id = ?", (track_id,))
    conn.commit()
    conn.close()


def create_playlist(name: str) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO playlists (name) VALUES (?)", (name,))
    playlist_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return playlist_id


def get_playlist(playlist_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return None


def get_all_playlists() -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM playlists ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def delete_playlist(playlist_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM playlists WHERE id = ?", (playlist_id,))
    conn.commit()
    conn.close()


def rename_playlist(playlist_id: int, new_name: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE playlists SET name = ? WHERE id = ?", (new_name, playlist_id))
    conn.commit()
    conn.close()


def add_track_to_playlist(playlist_id: int, track_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT COALESCE(MAX(position), 0) + 1 
        FROM playlist_tracks 
        WHERE playlist_id = ?
    """, (playlist_id,))
    position = cursor.fetchone()[0]
    
    try:
        cursor.execute("""
            INSERT INTO playlist_tracks (playlist_id, track_id, position)
            VALUES (?, ?, ?)
        """, (playlist_id, track_id, position))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    finally:
        conn.close()


def is_track_in_playlist(playlist_id: int, track_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM playlist_tracks WHERE playlist_id = ? AND track_id = ?", 
                   (playlist_id, track_id))
    result = cursor.fetchone() is not None
    conn.close()
    return result


def remove_track_from_playlist(playlist_id: int, track_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM playlist_tracks 
        WHERE playlist_id = ? AND track_id = ?
    """, (playlist_id, track_id))
    conn.commit()
    conn.close()


def reorder_tracks(playlist_id: int, ordered_track_ids: List[int]):
    conn = get_connection()
    cursor = conn.cursor()
    
    for position, track_id in enumerate(ordered_track_ids, start=1):
        cursor.execute(
            "UPDATE playlist_tracks SET position = ? WHERE playlist_id = ? AND track_id = ?",
            (position, playlist_id, track_id)
        )
    
    conn.commit()
    conn.close()


def get_playlist_tracks(playlist_id: int) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT t.*, pt.position 
        FROM tracks t
        JOIN playlist_tracks pt ON t.id = pt.track_id
        WHERE pt.playlist_id = ?
        ORDER BY pt.position
    """, (playlist_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_state_data(track_id: Optional[int], playlist_id: Optional[int]) -> Tuple[Optional[dict], Optional[dict], List[dict], List[dict]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    track = None
    playlist = None
    
    if track_id:
        cursor.execute("SELECT * FROM tracks WHERE id = ?", (track_id,))
        row = cursor.fetchone()
        if row:
            track = dict(row)
    
    if playlist_id:
        cursor.execute("SELECT * FROM playlists WHERE id = ?", (playlist_id,))
        row = cursor.fetchone()
        if row:
            playlist = dict(row)
    
    cursor.execute("SELECT * FROM playlists ORDER BY created_at DESC")
    playlists = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM tracks ORDER BY date_added DESC")
    tracks = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return track, playlist, playlists, tracks


def get_app_state() -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM app_state WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(row)
    return {
        'volume': 0.7,
        'server_port': 8080,
        'is_playing': 0,
        'position': 0,
        'current_playlist_id': None,
        'current_track_id': None
    }


def save_app_state(
    volume: float = _UNSET_INSTANCE,
    is_playing: int = _UNSET_INSTANCE,
    position: float = _UNSET_INSTANCE,
    current_playlist_id: int = _UNSET_INSTANCE,
    current_track_id: int = _UNSET_INSTANCE,
    server_port: int = _UNSET_INSTANCE,
    shuffle: int = _UNSET_INSTANCE
):
    conn = get_connection()
    cursor = conn.cursor()
    
    updates = []
    values = []
    
    if not isinstance(volume, _UNSET):
        updates.append("volume = ?")
        values.append(volume)
    if not isinstance(is_playing, _UNSET):
        updates.append("is_playing = ?")
        values.append(is_playing)
    if not isinstance(position, _UNSET):
        updates.append("position = ?")
        values.append(position)
    if not isinstance(current_playlist_id, _UNSET):
        updates.append("current_playlist_id = ?")
        values.append(current_playlist_id)
    if not isinstance(current_track_id, _UNSET):
        updates.append("current_track_id = ?")
        values.append(current_track_id)
    if not isinstance(server_port, _UNSET):
        updates.append("server_port = ?")
        values.append(server_port)
    if not isinstance(shuffle, _UNSET):
        updates.append("shuffle = ?")
        values.append(shuffle)
    
    if updates:
        updates.append("last_updated = CURRENT_TIMESTAMP")
        values.append(1)
        
        query = f"UPDATE app_state SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
