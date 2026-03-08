# Ambient Music Player - Technical Design

## 1. Overview

**Project:** Ambient Music Player  
**Tech Stack:** Python + PyQt6 + SQLite + Flask + VLC  
**Purpose:** A local ambient music player with GUI and web interface for controlling playback
**License:** MIT

## 2. Architecture

### 2.1 Components

| Component | File | Description |
|-----------|------|-------------|
| Main Entry | `src/main.py` | Initializes all components, starts Qt event loop |
| Audio Player | `src/player.py` | VLC-based audio playback |
| State Manager | `src/state.py` | Manages playback state, persistence, thread-safe |
| Database | `src/database.py` | SQLite for tracks, playlists, app state |
| Config | `src/config.py` | Application settings, dark theme, platform-aware data directory |
| Logger | `src/logger.py` | Logging configuration |
| GUI | `src/gui/main_window.py` | PyQt6 main window |
| Web Server | `src/web/app.py` | Flask REST API + HTML template |

### 2.2 Data Model

**Tables:**
- `tracks` - id, file_path, title, artist, duration, date_added
- `playlists` - id, name, created_at
- `playlist_tracks` - id, playlist_id, track_id, position (UNIQUE constraint)
- `app_state` - id, current_playlist_id, current_track_id, position, volume, is_playing, server_port, shuffle

### 2.3 Thread Safety

- Uses `threading.RLock` for reentrant locking
- State updates notify listeners via Qt signals with queued connections
- Auto-save releases lock before database write to prevent contention
- Volume slider uses signal blocking to prevent feedback loops

## 3. GUI Design

### 3.1 Layout (420x480 minimum)

```
┌─────────────────────────────────────┐
│       ♪ Ambient Music Player        │
│    Track Title - Artist Name        │
│  [==========○===============]       │
│         00:00 / 03:45               │
│  ⏮   ⏯   ⏹   ⏭   🔀              │
│  🔊 [==========]                    │
│  [Select Playlist... ▼] [+]         │
│  ┌─────────────────────────────┐    │
│  │ Track 1                     │    │
│  │ Track 2                     │    │
│  │ Track 3                     │    │
│  └─────────────────────────────┘    │
│  [Add Files] [Add Folder] [Manage]  │
│  [Move Up] [Move Down]              │
│  Server: [8080▼] [Apply Port]       │
└─────────────────────────────────────┘
```

### 3.2 Features

- System tray with minimize-to-tray on close
- Close dialog: Minimize to Tray / Exit / Cancel
- Dark theme (#1E1E2E background, #7C3AED accent)
- Add files/folders dialog with playlist selection
- Playlist management dialog (create, rename, delete)
- Shuffle mode toggle
- Volume control with dynamic icon (🔇/🔈/🔉/🔊)
- Progress bar seeking
- Keyboard shortcuts (Space, Left/Right arrows, Up/Down volume)

## 4. Web Interface Design

### 4.1 Layout (400px centered)

```
┌──────────────────────────────────┐
│    ♪ Ambient Music Player        │
│  Track Title                     │
│  Artist Name                     │
│  [━━━━━━━○━━━━━━━━━━]            │
│  00:00        03:45              │
│    ⏮   ⏯   ⏹   ⏭   🔀         │
│  🔊 [━━━━━━━━━]                   │
│  [Select Playlist ▼]             │
│  Track list (scrollable)         │
│  Playing/Paused/Stopped           │
│  [Manage Playlists] [Manage Tracks]│
└──────────────────────────────────┘
```

### 4.2 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | HTML interface |
| `/api/state` | GET | Current player state (JSON) |
| `/api/play` | POST | Start playback |
| `/api/pause` | POST | Pause playback |
| `/api/stop` | POST | Stop playback |
| `/api/toggle` | POST | Play/Pause toggle |
| `/api/volume` | POST | Set volume (0.0-1.0) |
| `/api/next` | POST | Next track |
| `/api/prev` | POST | Previous track |
| `/api/shuffle` | POST | Toggle shuffle mode |
| `/api/playlist` | POST | Set playlist (playlist_id) |
| `/api/track` | POST | Play specific track |
| `/api/position` | POST | Seek to position (0.0-1.0 normalized) |
| `/api/playlists` | GET | List all playlists |
| `/api/playlists` | POST | Create playlist |
| `/api/playlists/<id>` | DELETE | Delete playlist |
| `/api/playlists/<id>/rename` | PUT | Rename playlist |
| `/api/playlists/<id>/tracks` | GET | Get tracks in playlist |
| `/api/playlists/<id>/tracks/<tid>` | DELETE | Remove track from playlist |
| `/api/tracks` | GET | List all tracks |
| `/api/tracks/<id>` | PUT | Update track metadata |
| `/api/tracks/<id>` | DELETE | Delete track |

## 5. State Persistence

- Auto-save every 5 seconds during playback
- Saves: volume, position, current playlist, current track, playing state, shuffle mode
- Restores on application restart with auto-resume if was playing
- Data stored in platform-specific user data directory:
  - Windows: `%LOCALAPPDATA%\AmbientMusicPlayer`
  - macOS: `~/Library/Application Support/AmbientMusicPlayer`
  - Linux: `~/.local/share/AmbientMusicPlayer`
- Automatic migration from old project-relative data directory on first run

## 6. Supported Audio Formats

Via VLC: MP3, WAV, FLAC, OGG, M4A, AAC

## 7. Dependencies

- Python 3.8+
- PyQt6 - GUI framework
- Flask - Web server
- python-vlc - VLC bindings
- mutagen - Audio metadata extraction
- werkzeug - WSGI utilities

## 8. Features

### Implemented
- Local audio file playback
- Playlist management (create, rename, delete)
- Track management (add, edit, delete)
- Drag-and-drop reordering (move up/down)
- Shuffle mode
- Volume control with persistence
- Progress bar seeking
- System tray integration
- Web interface for remote control
- Keyboard shortcuts
- Auto-resume on restart
- Dark theme
- Platform-aware data directory
- Database migration

### Keyboard Shortcuts
- `Space` - Play/Pause
- `Left Arrow` - Previous track
- `Right Arrow` - Next track
- `Up Arrow` - Volume up
- `Down Arrow` - Volume down
