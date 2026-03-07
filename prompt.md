## Ambient Music Player - Function Description
Application Features:
- Standard functions: play, pause, off, volume
- Standard display of information about the currently playing song, its playlist, duration, playback time, etc.
- Continuous playback. Continues playback upon application or machine restart (last track memory, including time)
- Support for basic audio files
- GUI only: selecting files and folders from the local machine and adding them to the playlist
- Player - GUI + Web Interface: Selecting a playlist, creating a new playlist based on saved tracks, controlling playback and volume
- Player - GUI + Web Interface: Ability to sort, edit, delete, and display music files and playlists previously added to the database
- Elegant design, subdued colors
- Ease of use, best UI and UX practices
- Development stack: Python + PyQT6 + SQLite
- Interface GUI, as small as possible, compact layout. Warning before closing with the option to minimize to the taskbar.
- GUI first, connected to its own HTML server, running side-by-side and communicating with each other, launched via a shared startup file or other solution.
- Configurable HTML server port from the GUI.

Note: The application will run on a secure local network only. It does not require security.

Instructions:
- If it is necessary to run Python commands, always use the application's local .venv environment.
- Work in stages. Record your progress in the roadmap.
- First, create the design. Record it in the technical documentation files.
- In the next steps, proceed to project implementation.
- Mark the progress of the created stages in the appropriate documentation file so that work can easily be resumed in the event of an interrupt.