import sys
import threading
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database import init_db
from src.player import AudioPlayer
from src.state import StateManager
from src.web import app as flask_app, init_app
from src.logger import logger
from werkzeug.serving import make_server


class FlaskServerController:
    def __init__(self):
        self._server = None
        self._thread = None

    def start(self, port: int):
        self._server = make_server('0.0.0.0', port, flask_app)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Flask server started on port {port}")

    def stop(self):
        if self._server:
            self._server.shutdown()
            self._server = None
            self._thread = None

    def restart(self, port: int):
        logger.info(f"Restarting Flask server on port {port}...")
        self.stop()
        self.start(port)

    @property
    def port(self):
        return self._server.port if self._server else None


def main():
    try:
        logger.info("Starting Ambient Music Player")
        
        logger.info("Migrating data directory...")
        from src.database import migrate_data_dir
        migrate_data_dir()
        
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized")
        
        logger.info("Creating audio player...")
        player = AudioPlayer()
        logger.info("Audio player created")
        
        logger.info("Initializing state manager...")
        state_manager = StateManager(player)
        logger.info("State manager initialized")
        
        logger.info("Initializing Flask app...")
        init_app(state_manager)
        logger.info("Flask app initialized")
        
        server_controller = FlaskServerController()
        port = state_manager.state.server_port
        server_controller.start(port)
        
        from PyQt6.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        
        logger.info("Creating Qt application...")
        app = QApplication(sys.argv)
        app.setApplicationName("Ambient Music Player")
        
        logger.info("Creating main window...")
        window = MainWindow(state_manager, app, server_controller)
        window.show()
        logger.info("Main window shown")
        
        state_manager.start_auto_save()
        logger.info("Auto-save started")
        
        logger.info("Entering Qt event loop...")
        sys.exit(app.exec())
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
