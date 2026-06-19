# =====================================
# BaseGame — FINAL ARCHITECTURE
# =====================================

from abc import ABC
from datetime import datetime


class BaseGame(ABC):

    def __init__(self, db, game_name):
        self.db = db
        self.game_name = game_name
        self.start_time = None
        self.session_active = False

    # ----------------------------
    # Session Handling
    # ----------------------------
    def begin_session(self):
        self.start_time = datetime.now()
        self.session_active = True

    def end_session(self):
        if not self.start_time:
            return None
        duration = datetime.now() - self.start_time
        self.session_active = False
        return str(duration).split('.')[0]

    # ----------------------------
    # Required Methods
    # ----------------------------
    def start(self, app):
        raise NotImplementedError("Subclasses must implement start(self, app)")

    def reset(self):
        raise NotImplementedError("Subclasses must implement reset()")
    
    def finish_game(self, result=None):
        from kivy.app import App
        app = App.get_running_app()

        if app and hasattr(app, "handle_game_over"):
            app.handle_game_over(self, result)

