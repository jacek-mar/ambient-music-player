# Ambient Music Player - Function Description

## Application Overview

**Ambient Music Player** is a local ambient music player with dual-interface control (GUI + Web) designed for continuous playback in office, pub, or home environments.

## Core Features

### Playback Controls
- ▶️ **Play** - Start playback
- ⏸️ **Pause** - Pause playback  
- ⏹️ **Stop** - Stop and reset position
- ⏭️/⏮️ **Next/Previous** - Navigate tracks
- 🔀 **Shuffle** - Random playback mode
- 🔊 **Volume** - Adjustable volume control (0-100%)

### Display Information
- 🎵 Current track title and artist
- ⏱️ Playback time and total duration
- 📋 Current playlist name
- 📊 Playback status (Playing/Paused/Stopped)

### Continuous Playback
- 💾 **Auto-Resume** - Remembers last track and position on restart
- 🔄 **State Persistence** - Saves volume, shuffle mode, current playlist
- ⚡ **Auto-Save** - Saves state every 5 seconds during playback

### Audio Support
- 🎵 **Formats**: MP3, WAV, FLAC, OGG, M4A, AAC (via VLC)
- 📖 **Metadata** - Reads title, artist, duration from audio files

### GUI Features
- 📁 **Add Files** - Select individual audio files
- 📂 **Add Folder** - Add all audio from a folder
- ⚙️ **Manage Playlists** - Create, rename, delete playlists
- 🎶 **Track Management** - Edit metadata, reorder, remove
- ⬆️⬇️ **Move Up/Down** - Reorder tracks in playlist
- 🔌 **Configurable Port** - Change web server port (1024-65535)
- 🖥️ **System Tray** - Minimize to tray on close
- ⚠️ **Close Dialog** - Prompt: Minimize to Tray / Exit / Cancel
- 🌙 **Dark Theme** - Modern subdued color scheme (#1E1E2E background, #7C3AED accent)

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| Space | Play/Pause |
| ← | Previous track |
| → | Next track |
| ↑ | Volume up |
| ↓ | Volume down |

### Web Interface Features
- 🌐 **Remote Control** - Control from any device on local network
- 📱 **Responsive Design** - Works on phone, tablet, desktop
- 🎛️ **Full Control** - Playback, volume, shuffle, playlist selection
- 📋 **Track List** - View and select tracks from playlist
- ➕ **Playlist Management** - Create, rename, delete playlists via web

## Technical Stack

- **Language**: Python 3.8+
- **GUI Framework**: PyQt6
- **Web Framework**: Flask
- **Audio Engine**: VLC (python-vlc)
- **Metadata**: mutagen
- **Database**: SQLite
- **Data Storage**: Platform-specific user data directory
  - Windows: `%LOCALAPPDATA%\AmbientMusicPlayer`
  - macOS: `~/Library/Application Support/AmbientMusicPlayer`
  - Linux: `~/.local/share/AmbientMusicPlayer`

## Architecture

```
ambient-music-player/
├── src/
│   ├── main.py          # Application entry point
│   ├── player.py        # VLC audio player
│   ├── state.py         # State management (thread-safe with RLock)
│   ├── database.py      # SQLite database operations
│   ├── config.py        # Application configuration
│   ├── logger.py        # Logging configuration
│   ├── gui/             # PyQt6 GUI
│   │   └── main_window.py
│   └── web/             # Flask web server
│       ├── app.py       # REST API endpoints
│       └── templates/
│           └── index.html
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
└── run.py              # Run script
```

## Database Schema

### Tables
- **tracks** - id, file_path, title, artist, duration, date_added
- **playlists** - id, name, created_at
- **playlist_tracks** - id, playlist_id, track_id, position
- **app_state** - id, current_playlist_id, current_track_id, position, volume, is_playing, server_port, shuffle

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/state` | GET | Get current player state |
| `/api/play` | POST | Start playback |
| `/api/pause` | POST | Pause playback |
| `/api/stop` | POST | Stop playback |
| `/api/toggle` | POST | Play/Pause toggle |
| `/api/volume` | POST | Set volume (0.0-1.0) |
| `/api/next` | POST | Next track |
| `/api/prev` | POST | Previous track |
| `/api/shuffle` | POST | Toggle shuffle |
| `/api/position` | POST | Seek (0.0-1.0 normalized) |
| `/api/playlists` | GET/POST | List/create playlists |
| `/api/playlists/<id>` | DELETE | Delete playlist |
| `/api/playlists/<id>/rename` | PUT | Rename playlist |
| `/api/playlists/<id>/tracks` | GET | Get tracks in playlist |
| `/api/playlists/<id>/tracks/<tid>` | DELETE | Remove track |
| `/api/tracks` | GET | List all tracks |
| `/api/tracks/<id>` | PUT/DELETE | Update/delete track |

## Notes

- 🔒 **Local Network Only** - No security required (runs on localhost/local network)
- ⚡ **Thread-Safe** - Uses RLock for thread safety
- 💾 **Data Migration** - Auto-migrates from old location on first run
- 🎯 **UX Best Practices** - Intuitive controls, clear feedback, keyboard shortcuts

## Development Instructions

- Use local `.venv` for Python commands
- Work in stages, record progress in roadmap
- Update technical documentation before implementation
- Mark progress in documentation for session continuity
