# Ambient Music Player 🎵

A modern ambient music player with GUI and web interface for controlling playback.

## Purpose 🎧

The **Ambient Music Player** is designed for **continuous playback of ambient music** in various settings:

- 🏢 **Office** - Create a relaxing background atmosphere for work
- 🍺 **Pub/Bar** - Set the mood with continuous ambient playlists
- 🏠 **Apartment/Home** - Ambient sounds for relaxation or productivity
- 🏥 **Waiting Room** - Pleasant background music for clients/visitors

### Key Benefits

| Feature | Benefit |
|---------|---------|
| 🌐 **Web Interface** | Control music from any device on your local network |
| 🎛️ **Dual Control** | Use the desktop GUI or browser on phone/tablet |
| 🔄 **Auto-Play** | Remembers your playlist and continues where you left off |
| 👥 **Multi-Device** | Anyone on the network can control playback |

Control your music from anywhere on your local network using any web browser!

---

## About This Project

This project was created as an entry to **Kilo League Challenge #5**.

> **Kilo League Challenge #5** | Win $500 of Credits 💰 🚀
> 
> Build ANYTHING with the Kilo CLI
> 
> It's simple: "Install/update the Kilo CLI and Build ANYTHING, but you must use the CLI the entire time and submit your project."

This project was implemented entirely using the [KiloCode CLI](https://kilo.ai/) and the MiniMax M2.5 AI Agent, which was free on KiloCode at the time of project creation.

---

## Features

- 🎵 **Local Audio Playback** - Support for MP3, WAV, FLAC, OGG, M4A, AAC formats via VLC
- 📋 **Playlist Management** - Create, rename, and delete playlists
- 🎶 **Track Management** - Add individual files or entire folders, edit metadata
- 🔀 **Shuffle Mode** - Random playback within playlists
- 🖥️ **Dual Interface** - Both PyQt6 GUI and web interface
- 🌐 **Remote Control** - Control playback from any device via web browser
- 📥 **System Tray** - Minimize to system tray
- 💾 **Auto-Resume** - Remembers playback state across restarts
- 🌙 **Dark Theme** - Modern dark UI design

## Screenshots

### GUI
<img width="504" height="577" alt="gui-interface-ambient-music-player" src="https://github.com/user-attachments/assets/d6f416aa-b0be-48b8-8bd0-5ee803b04b57" />


### Web Interface
<img width="640" height="817" alt="web-interface-ambient-music-player" src="https://github.com/user-attachments/assets/2cc293a4-6a84-4cba-a422-53654b51202b" />


## Installation

### Prerequisites

- Python 3.8+
- VLC Media Player (must be installed on system)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ambient-music-player
cd ambient-music-player
```

> **Note:** This project was built using KiloCode CLI. Learn more at [https://kilo.ai/](https://kilo.ai/)

2. Create and activate virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/macOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python run.py
```

## Usage

### GUI Controls

- ▶️/⏸️ **Play/Pause** - Toggle playback
- ⏹️ **Stop** - Stop playback and reset position
- ⏭️/⏮️ **Next/Previous** - Navigate tracks
- 🔀 **Shuffle** - Toggle shuffle mode
- 🔊 **Volume** - Adjust volume with slider or arrow keys
- 📁 **Add Files** - Add audio files to playlist
- 📂 **Add Folder** - Add all audio files from a folder
- ⚙️ **Manage Playlists** - Create, rename, delete playlists

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ␣ Space | Play/Pause |
| ← | Previous track |
| → | Next track |
| ↑ | Volume up |
| ↓ | Volume down |

### Web Interface 🌐

Access the web interface at `http://localhost:8080` (or configured port) from any device on your network:

- ▶️⏸️ Playback controls
- 🔊 Volume control  
- 📋 Playlist selection
- 🎵 Track list with click-to-play
- 🔀 Shuffle toggle

## Configuration

### Port Configuration

Change the server port in the GUI or via the web API (default: 8080).

### Data Directory

The application stores data in the platform-specific user data directory:
- **Windows:** `%LOCALAPPDATA%\AmbientMusicPlayer`
- **macOS:** `~/Library/Application Support/AmbientMusicPlayer`
- **Linux:** `~/.local/share/AmbientMusicPlayer`

## API Documentation

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
| `/api/tracks` | GET | List all tracks |

## Development

### Running Tests
```bash
pytest
```

### Project Structure

```
ambient-music-player/
├── src/
│   ├── main.py          # Application entry point
│   ├── player.py        # VLC audio player
│   ├── state.py         # State management
│   ├── database.py      # SQLite database
│   ├── config.py        # Configuration
│   ├── logger.py       # Logging
│   ├── gui/            # PyQt6 GUI
│   └── web/            # Flask web server
├── docs/                # Documentation
├── requirements.txt     # Python dependencies
└── run.py              # Run script
```

## License

MIT License - see [LICENSE](LICENSE) file.

## Acknowledgments

- [VLC](https://www.videolan.org/) for media playback
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) for GUI
- [Flask](https://flask.palletsprojects.com/) for web interface
- [mutagen](https://mutagen.readthedocs.io/) for audio metadata

---

## About Kilo Code 🤖

This project was built using **Kilo Code** - a powerful AI-powered CLI tool that brings the power of AI to your terminal! 🚀

**Key Features:**
- ✨ AI-powered code generation and assistance
- 💻 Interactive CLI with intelligent autocomplete
- 🔧 Seamless integration with popular programming languages
- 🏗️ Build anything from simple scripts to complex applications

**Get Started with Kilo Code:**
👉 [https://kilo.ai/](https://kilo.ai/)
