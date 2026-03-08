import sys
from pathlib import Path
from typing import Optional
import os

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSlider, QLabel, QComboBox,
    QMessageBox, QSystemTrayIcon, QMenu, QFileDialog,
    QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
    QFrame, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSettings, QMetaObject
from PyQt6.QtGui import QIcon, QAction, QShortcut, QKeySequence

from ..config import STYLE_DARK, APP_NAME
from ..state import StateManager
from ..database import (
    get_all_playlists, get_playlist_tracks, create_playlist,
    delete_playlist, add_track, add_track_to_playlist,
    get_all_tracks, delete_track, remove_track_from_playlist,
    rename_playlist, update_track, reorder_tracks, get_track,
    is_track_in_playlist
)


class CloseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Close Application")
        self.setMinimumWidth(300)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("What would you like to do?"))
        
        btn_layout = QHBoxLayout()
        
        self.minimize_btn = QPushButton("Minimize to Tray")
        self.minimize_btn.setDefault(False)
        self.minimize_btn.setAutoDefault(False)
        self.minimize_btn.clicked.connect(self._on_minimize)
        
        self.exit_btn = QPushButton("Exit")
        self.exit_btn.setDefault(False)
        self.exit_btn.setAutoDefault(False)
        self.exit_btn.clicked.connect(self._on_exit)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setDefault(True)
        self.cancel_btn.setAutoDefault(True)
        self.cancel_btn.clicked.connect(self._on_cancel)
        
        btn_layout.addWidget(self.minimize_btn)
        btn_layout.addWidget(self.exit_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
    
    def _on_minimize(self):
        self.done(1)
    
    def _on_exit(self):
        self.done(2)
    
    def _on_cancel(self):
        self.done(0)


class AddFilesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Music")
        self.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(self)
        
        self.file_list = QListWidget()
        layout.addWidget(self.file_list)
        
        btn_layout = QHBoxLayout()
        add_files_btn = QPushButton("Add Files")
        add_folder_btn = QPushButton("Add Folder")
        
        add_files_btn.clicked.connect(self.add_files)
        add_folder_btn.clicked.connect(self.add_folder)
        
        btn_layout.addWidget(add_files_btn)
        btn_layout.addWidget(add_folder_btn)
        layout.addLayout(btn_layout)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
        
        self.files = []
    
    def add_files(self, files=None):
        if files is None:
            result = QFileDialog.getOpenFileNames(
                self, "Select Audio Files", "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)"
            )
            if not result:
                return
            files = result[0] if result else []
        if not files:
            return
        for f in files:
            if f not in self.files:
                self.files.append(f)
                self.file_list.addItem(Path(f).name)
    
    def add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        audio_exts = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac')
        for root, dirs, dir_files in os.walk(folder):
            for file in dir_files:
                if file.lower().endswith(audio_exts):
                    file_path = os.path.join(root, file)
                    self.add_files([file_path])
    
    def get_files(self):
        return self.files


class MainWindow(QMainWindow):
    state_changed = pyqtSignal(dict)
    media_parsed_signal = pyqtSignal()
    
    def __init__(self, state_manager: StateManager, app: QApplication, server_controller=None):
        super().__init__()
        self.state_manager = state_manager
        self.app = app
        self.server_controller = server_controller
        self.settings = QSettings("AmbientMusicPlayer", "MainWindow")
        
        self.tray_icon: Optional[QSystemTrayIcon] = None
        
        self.init_ui()
        self.init_tray()
        self.restore_state()
        
        self.state_manager.add_listener(self.on_state_changed)
        
        self.state_changed.connect(self.update_from_state)
        
        self.media_parsed_signal.connect(self.update_display)
        
        self.state_manager.player.set_on_media_parsed(self.on_media_parsed)
        
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
        self.update_timer.start(500)
        
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        QShortcut(QKeySequence(Qt.Key.Key_Space), self, self.on_play_pause_shortcut)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.on_prev_shortcut)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.on_next_shortcut)
        QShortcut(QKeySequence(Qt.Key.Key_Up), self, self.volume_up)
        QShortcut(QKeySequence(Qt.Key.Key_Down), self, self.volume_down)
    
    def on_play_pause_shortcut(self):
        if self.state_manager.state.current_track_id:
            self.state_manager.toggle_play_pause()
    
    def on_prev_shortcut(self):
        if self.state_manager.state.current_playlist_id:
            self.state_manager.prev_track()
    
    def on_next_shortcut(self):
        if self.state_manager.state.current_playlist_id:
            self.state_manager.next_track()
    
    def volume_up(self):
        new_val = min(100, self.volume_slider.value() + 5)
        self.volume_slider.setValue(new_val)
    
    def volume_down(self):
        new_val = max(0, self.volume_slider.value() - 5)
        self.volume_slider.setValue(new_val)
    
    def init_ui(self):
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(420, 480)
        self.setStyleSheet(STYLE_DARK)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        self.title_label = QLabel(f"♪ {APP_NAME}")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)
        
        self.track_label = QLabel("No track loaded")
        self.track_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.track_label.setStyleSheet("color: #9CA3AF;")
        layout.addWidget(self.track_label)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.sliderMoved.connect(self.on_seek)
        layout.addWidget(self.progress_slider)
        
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.time_label.setStyleSheet("font-size: 10px; color: #9CA3AF;")
        layout.addWidget(self.time_label)
        
        transport_layout = QHBoxLayout()
        transport_layout.setSpacing(8)
        
        self.prev_btn = QPushButton("⏮")
        self.prev_btn.setFixedSize(36, 36)
        self.prev_btn.clicked.connect(self.state_manager.prev_track)
        
        self.play_btn = QPushButton("⏯")
        self.play_btn.setFixedSize(36, 36)
        self.play_btn.clicked.connect(self.state_manager.toggle_play_pause)
        
        self.stop_btn = QPushButton("⏹")
        self.stop_btn.setFixedSize(36, 36)
        self.stop_btn.clicked.connect(self.state_manager.stop)
        
        self.next_btn = QPushButton("⏭")
        self.next_btn.setFixedSize(36, 36)
        self.next_btn.clicked.connect(self.state_manager.next_track)
        
        self.shuffle_btn = QPushButton("🔀")
        self.shuffle_btn.setFixedSize(36, 36)
        self.shuffle_btn.setCheckable(True)
        self.shuffle_btn.clicked.connect(self.on_shuffle_toggled)
        
        transport_layout.addStretch()
        transport_layout.addWidget(self.prev_btn)
        transport_layout.addWidget(self.play_btn)
        transport_layout.addWidget(self.stop_btn)
        transport_layout.addWidget(self.next_btn)
        transport_layout.addWidget(self.shuffle_btn)
        transport_layout.addStretch()
        
        volume_layout = QHBoxLayout()
        volume_layout.setSpacing(8)
        
        self.volume_label = QLabel("🔊")
        volume_layout.addWidget(self.volume_label)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)
        
        volume_layout.addWidget(self.volume_slider)
        
        controls_container = QWidget()
        controls_container_layout = QVBoxLayout(controls_container)
        controls_container_layout.setSpacing(8)
        controls_container_layout.setContentsMargins(0, 0, 0, 0)
        controls_container_layout.addLayout(transport_layout)
        controls_container_layout.addLayout(volume_layout)
        layout.addWidget(controls_container)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #4B5563;")
        layout.addWidget(separator)
        
        playlist_header = QLabel("Playlist")
        playlist_header.setStyleSheet("font-weight: bold; color: #D1D5DB;")
        layout.addWidget(playlist_header)
        
        playlist_controls_layout = QHBoxLayout()
        
        self.playlist_combo = QComboBox()
        self.playlist_combo.currentIndexChanged.connect(self.on_playlist_changed)
        playlist_controls_layout.addWidget(self.playlist_combo, 1)
        
        self.add_playlist_btn = QPushButton("+")
        self.add_playlist_btn.setFixedSize(30, 30)
        self.add_playlist_btn.clicked.connect(self.add_playlist)
        
        playlist_controls_layout.addWidget(self.add_playlist_btn)
        
        layout.addLayout(playlist_controls_layout)
        
        self.track_list = QListWidget()
        self.track_list.itemDoubleClicked.connect(self.on_track_double_clicked)
        self.track_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.track_list.customContextMenuRequested.connect(self.on_track_context_menu)
        layout.addWidget(self.track_list, 1)
        
        track_buttons_layout = QHBoxLayout()
        
        self.add_files_btn = QPushButton("Add Files")
        self.add_files_btn.clicked.connect(self.show_add_files)
        
        self.add_folder_btn = QPushButton("Add Folder")
        self.add_folder_btn.clicked.connect(self.add_folder_to_playlist)
        
        self.manage_playlists_btn = QPushButton("Manage Playlists")
        self.manage_playlists_btn.clicked.connect(self.show_playlists_dialog)
        
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.clicked.connect(self.move_track_up)
        
        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.clicked.connect(self.move_track_down)
        
        track_buttons_layout.addWidget(self.add_files_btn)
        track_buttons_layout.addWidget(self.add_folder_btn)
        track_buttons_layout.addWidget(self.manage_playlists_btn)
        track_buttons_layout.addStretch()
        track_buttons_layout.addWidget(self.move_up_btn)
        track_buttons_layout.addWidget(self.move_down_btn)
        
        layout.addLayout(track_buttons_layout)
        
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.HLine)
        separator2.setStyleSheet("color: #4B5563;")
        layout.addWidget(separator2)
        
        server_layout = QHBoxLayout()
        
        self.port_input = QComboBox()
        self.port_input.setEditable(True)
        self.port_input.addItems(["8080", "8081", "8082", "3000", "5000"])
        self.port_input.setCurrentText(str(self.state_manager.state.server_port))
        self.port_input.setFixedWidth(80)
        
        self.port_btn = QPushButton("Apply Port")
        self.port_btn.clicked.connect(self.apply_port)
        
        server_layout.addWidget(QLabel("Server:"))
        server_layout.addWidget(self.port_input)
        server_layout.addWidget(self.port_btn)
        server_layout.addStretch()
        
        layout.addLayout(server_layout)
    
    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        
        menu = QMenu()
        
        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show_from_tray)
        menu.addAction(show_action)
        
        play_pause_action = QAction("Play/Pause", self)
        play_pause_action.triggered.connect(self.state_manager.toggle_play_pause)
        menu.addAction(play_pause_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def show_from_tray(self):
        self.show()
        self.activateWindow()
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()
    
    def restore_state(self):
        geo = self.settings.value("geometry")
        if geo:
            self.setGeometry(geo)
        
        self.volume_slider.setValue(int(self.state_manager.state.volume * 100))
        self.refresh_playlists()
        
        state = self.state_manager.get_state_dict()
        self.update_from_state(state)
    
    def closeEvent(self, event):
        dialog = CloseDialog(self)
        result = dialog.exec()
        
        if result == 1:
            event.ignore()
            self.hide()
        elif result == 2:
            event.accept()
            self.quit_app()
        else:
            event.ignore()
    
    def quit_app(self):
        self.state_manager.save_state()
        self.state_manager.stop_auto_save()
        self.tray_icon.hide()
        self.app.quit()
    
    def on_state_changed(self, state: dict):
        self.state_changed.emit(state)
    
    def on_media_parsed(self):
        self.media_parsed_signal.emit()
    
    def update_from_state(self, state: dict):
        track = state.get('current_track')
        if track:
            title = track.get('title', 'Unknown')
            artist = track.get('artist', 'Unknown Artist')
            self.track_label.setText(f"{title} - {artist}")
        else:
            self.track_label.setText("No track loaded")
        
        self.play_btn.setText("⏸" if state['is_playing'] else "⏯")
        
        volume = int((state.get('volume', 0.7)) * 100)
        if self.volume_slider.value() != volume:
            self.volume_slider.blockSignals(True)
            self.volume_slider.setValue(volume)
            self.volume_slider.blockSignals(False)
        
        if volume == 0:
            vol_icon = "🔇"
        elif volume <= 33:
            vol_icon = "🔈"
        elif volume <= 66:
            vol_icon = "🔉"
        else:
            vol_icon = "🔊"
        self.volume_label.setText(vol_icon)
        
        if hasattr(self, 'shuffle_btn'):
            shuffle_active = state.get('shuffle', False)
            self.shuffle_btn.setChecked(shuffle_active)
            self.shuffle_btn.setStyleSheet("" if shuffle_active else "opacity: 0.5;")
    
    def update_display(self):
        player = self.state_manager.player
        
        if player.get_duration() > 0:
            position = player.get_position()
            self.progress_slider.setValue(int(position * 1000))
            
            current_ms = player.get_time()
            total_ms = player.get_duration()
            
            current_str = self.format_time(current_ms / 1000)
            total_str = self.format_time(total_ms / 1000)
            self.time_label.setText(f"{current_str} / {total_str}")
    
    def format_time(self, seconds: float) -> str:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"
    
    def on_seek(self, value: int):
        position = value / 1000.0
        self.state_manager.set_position(position)
    
    def on_shuffle_toggled(self, checked: bool):
        self.state_manager.toggle_shuffle()
        self.shuffle_btn.setText("🔀" if checked else "🔀")
        self.shuffle_btn.setStyleSheet("" if checked else "")
    
    def on_volume_changed(self, value: int):
        volume = value / 100.0
        self.state_manager.set_volume(volume)
        
        if value == 0:
            icon = "🔇"
        elif value <= 33:
            icon = "🔈"
        elif value <= 66:
            icon = "🔉"
        else:
            icon = "🔊"
        self.volume_label.setText(icon)
    
    def on_playlist_changed(self, index):
        if index > 0:
            playlist_id = self.playlist_combo.currentData()
            if playlist_id:
                self.state_manager.set_playlist(playlist_id)
    
    def refresh_playlists(self):
        self.playlist_combo.blockSignals(True)
        self.playlist_combo.clear()
        self.playlist_combo.addItem("Select Playlist...", None)
        
        playlists = get_all_playlists()
        for p in playlists:
            self.playlist_combo.addItem(p['name'], p['id'])
        
        current_id = self.state_manager.state.current_playlist_id
        if current_id:
            idx = self.playlist_combo.findData(current_id)
            if idx >= 0:
                self.playlist_combo.setCurrentIndex(idx)
        
        self.playlist_combo.blockSignals(False)
        self.refresh_track_list()
    
    def refresh_track_list(self):
        self.track_list.blockSignals(True)
        self.track_list.clear()
        
        playlist_id = self.state_manager.state.current_playlist_id
        if playlist_id:
            tracks = get_playlist_tracks(playlist_id)
            for t in tracks:
                item = QListWidgetItem(f"{t['title']} - {t.get('artist', 'Unknown')}")
                item.setData(Qt.ItemDataRole.UserRole, t['id'])
                self.track_list.addItem(item)
        
        self.track_list.blockSignals(False)
    
    def on_track_double_clicked(self, item: QListWidgetItem):
        track_id = item.data(Qt.ItemDataRole.UserRole)
        if track_id:
            self.state_manager.play_track(track_id)
    
    def on_track_context_menu(self, pos):
        item = self.track_list.itemAt(pos)
        if not item:
            return
        
        track_id = item.data(Qt.ItemDataRole.UserRole)
        playlist_id = self.state_manager.state.current_playlist_id
        
        if not track_id or not playlist_id:
            return
        
        menu = QMenu(self)
        
        play_action = QAction("Play", self)
        play_action.triggered.connect(lambda: self.state_manager.play_track(track_id))
        menu.addAction(play_action)
        
        edit_action = QAction("Edit Track", self)
        edit_action.triggered.connect(lambda: self.edit_track(track_id))
        menu.addAction(edit_action)
        
        menu.addSeparator()
        
        remove_action = QAction("Remove from playlist", self)
        remove_action.triggered.connect(lambda: self.remove_track_from_playlist(playlist_id, track_id))
        menu.addAction(remove_action)
        
        menu.exec(self.track_list.mapToGlobal(pos))
    
    def edit_track(self, track_id: int):
        from PyQt6.QtWidgets import QInputDialog
        
        track = get_track(track_id)
        if not track:
            return
        
        title = track.get('title', '')
        artist = track.get('artist', '')
        
        new_title, ok = QInputDialog.getText(self, "Edit Track", "Title:", text=title)
        if not ok:
            return
        
        new_artist, ok = QInputDialog.getText(self, "Edit Track", "Artist:", text=artist)
        if not ok:
            return
        
        update_track(track_id, new_title, new_artist)
        self.refresh_track_list()
    
    def remove_track_from_playlist(self, playlist_id: int, track_id: int):
        reply = QMessageBox.question(
            self, "Remove Track",
            "Are you sure you want to remove this track from the playlist?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            remove_track_from_playlist(playlist_id, track_id)
            self.refresh_track_list()
    
    def move_track_up(self):
        current_row = self.track_list.currentRow()
        if current_row <= 0:
            return
        
        playlist_id = self.state_manager.state.current_playlist_id
        if not playlist_id:
            return
        
        tracks = get_playlist_tracks(playlist_id)
        if current_row >= len(tracks):
            return
        
        track_ids = [t['id'] for t in tracks]
        track_ids[current_row], track_ids[current_row - 1] = track_ids[current_row - 1], track_ids[current_row]
        
        reorder_tracks(playlist_id, track_ids)
        self.refresh_track_list()
        self.track_list.setCurrentRow(current_row - 1)
    
    def move_track_down(self):
        current_row = self.track_list.currentRow()
        
        playlist_id = self.state_manager.state.current_playlist_id
        if not playlist_id:
            return
        
        tracks = get_playlist_tracks(playlist_id)
        if current_row < 0 or current_row >= len(tracks) - 1:
            return
        
        track_ids = [t['id'] for t in tracks]
        track_ids[current_row], track_ids[current_row + 1] = track_ids[current_row + 1], track_ids[current_row]
        
        reorder_tracks(playlist_id, track_ids)
        self.refresh_track_list()
        self.track_list.setCurrentRow(current_row + 1)
    
    def add_playlist(self):
        from PyQt6.QtWidgets import QInputDialog
        
        name, ok = QInputDialog.getText(self, "New Playlist", "Playlist name:")
        if ok and name:
            playlist_id = create_playlist(name)
            self.refresh_playlists()
    
    def show_add_files(self):
        playlists = get_all_playlists()
        if not playlists:
            QMessageBox.warning(
                self, "No Playlists",
                "Please create a playlist first before adding music."
            )
            return
        
        result = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)"
        )
        if not result or not result[0]:
            return
        
        files = result[0]
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Music")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select target playlist:"))
        
        playlist_combo = QComboBox()
        for p in playlists:
            playlist_combo.addItem(p['name'], p['id'])
        layout.addWidget(playlist_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if not dialog.exec():
            return
        
        playlist_id = playlist_combo.currentData()
        playlist_name = playlist_combo.currentText()
        
        added_count = 0
        skipped_count = 0
        
        for file_path in files:
            track_id = add_track(file_path)
            if track_id:
                if not is_track_in_playlist(playlist_id, track_id):
                    add_track_to_playlist(playlist_id, track_id)
                    added_count += 1
                else:
                    skipped_count += 1
        
        self.refresh_playlists()
        
        if skipped_count > 0:
            QMessageBox.information(
                self, "Tracks Added",
                f"{added_count} new tracks added to {playlist_name}.\n{skipped_count} tracks skipped (already in playlist)."
            )
        else:
            QMessageBox.information(
                self, "Tracks Added",
                f"{added_count} tracks added to {playlist_name}."
            )
    
    def add_folder_to_playlist(self):
        playlists = get_all_playlists()
        if not playlists:
            QMessageBox.warning(
                self, "No Playlists",
                "Please create a playlist first before adding music."
            )
            return
        
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if not folder:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Folder")
        dialog.setMinimumWidth(300)
        
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select target playlist:"))
        
        playlist_combo = QComboBox()
        for p in playlists:
            playlist_combo.addItem(p['name'], p['id'])
        layout.addWidget(playlist_combo)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if not dialog.exec():
            return
        
        playlist_id = playlist_combo.currentData()
        playlist_name = playlist_combo.currentText()
        
        audio_exts = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac')
        added_count = 0
        skipped_count = 0
        
        for root, dirs, dir_files in os.walk(folder):
            for file in dir_files:
                if file.lower().endswith(audio_exts):
                    file_path = os.path.join(root, file)
                    track_id = add_track(file_path)
                    if track_id:
                        if not is_track_in_playlist(playlist_id, track_id):
                            add_track_to_playlist(playlist_id, track_id)
                            added_count += 1
                        else:
                            skipped_count += 1
        
        self.refresh_playlists()
        
        if skipped_count > 0:
            QMessageBox.information(
                self, "Tracks Added",
                f"{added_count} new tracks added from folder to {playlist_name}.\n{skipped_count} tracks skipped (already in playlist)."
            )
        else:
            QMessageBox.information(
                self, "Tracks Added",
                f"{added_count} tracks added from folder to {playlist_name}."
            )
    
    def apply_port(self):
        try:
            port = int(self.port_input.currentText())
            if not (1024 <= port <= 65535):
                raise ValueError("Port out of range")
        except ValueError:
            QMessageBox.warning(self, "Invalid Port", "Port must be a number between 1024 and 65535.")
            return
        
        self.state_manager.set_server_port(port)
        
        if self.server_controller:
            self.server_controller.restart(port)
            QMessageBox.information(
                self, "Port Changed",
                f"Server restarted on port {port}."
            )
    
    def show_playlists_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Manage Playlists")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        playlist_list = QListWidget()
        layout.addWidget(playlist_list)
        
        playlists = get_all_playlists()
        for p in playlists:
            item = QListWidgetItem(p['name'])
            item.setData(Qt.ItemDataRole.UserRole, p['id'])
            playlist_list.addItem(item)
        
        btn_layout = QHBoxLayout()
        
        delete_btn = QPushButton("Delete Selected")
        delete_btn.clicked.connect(lambda: self.delete_selected_playlist(playlist_list))
        
        rename_btn = QPushButton("Rename")
        rename_btn.clicked.connect(lambda: self.rename_selected_playlist(playlist_list))
        
        view_btn = QPushButton("View Tracks")
        view_btn.clicked.connect(lambda: self.view_playlist_tracks(playlist_list))
        
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(rename_btn)
        btn_layout.addWidget(view_btn)
        btn_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.exec()
        
        self.refresh_playlists()
        self.refresh_track_list()
    
    def delete_selected_playlist(self, list_widget: QListWidget):
        item = list_widget.currentItem()
        if item:
            playlist_id = item.data(Qt.ItemDataRole.UserRole)
            reply = QMessageBox.question(
                self, "Delete Playlist",
                "Are you sure you want to delete this playlist?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                delete_playlist(playlist_id)
                self.refresh_playlists()
    
    def rename_selected_playlist(self, list_widget: QListWidget):
        item = list_widget.currentItem()
        if not item:
            return
        
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        current_name = item.text()
        
        from PyQt6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self, "Rename Playlist", "New name:",
            text=current_name
        )
        
        if ok and new_name and new_name != current_name:
            rename_playlist(playlist_id, new_name)
            self.refresh_playlists()
    
    def view_playlist_tracks(self, list_widget: QListWidget):
        item = list_widget.currentItem()
        if not item:
            return
        
        playlist_id = item.data(Qt.ItemDataRole.UserRole)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Tracks in {item.text()}")
        dialog.setMinimumSize(400, 300)
        
        layout = QVBoxLayout(dialog)
        
        track_list = QListWidget()
        layout.addWidget(track_list)
        
        tracks = get_playlist_tracks(playlist_id)
        for t in tracks:
            track_list.addItem(f"{t['title']} - {t.get('artist', 'Unknown')}")
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
