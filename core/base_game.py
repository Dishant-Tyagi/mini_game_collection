# =====================================
# BaseGame — Abstract Base for All Mini Games
# =====================================
from abc import ABC
from datetime import datetime


class BaseGame(ABC):
    """
    Unified base class for all mini-games.
    Handles:
      - session tracking
      - DB connection
      - metadata setup
    Subclasses can override `update()` and `get_score()` if needed.
    """

    def __init__(self, db, game_name):
        self.db = db
        self.game_name = game_name
        self.start_time = None
        self.session_active = False

    # -----------------------------------------------------------
    # Session Handling
    # -----------------------------------------------------------
    def begin_session(self):
        """Mark the start of a new game session."""
        self.start_time = datetime.now()
        self.session_active = True

    def end_session(self):
        """Mark end of session and compute duration."""
        if not self.start_time:
            return None
        duration = datetime.now() - self.start_time
        self.session_active = False
        return str(duration).split('.')[0]

    # -----------------------------------------------------------
    # Optional Override Hooks
    # -----------------------------------------------------------
    def update(self, dt):
        """Optional update loop — used by dynamic games like Snake."""
        pass

    def get_score(self):
        """Optional score retrieval — used by scoring games."""
        return 0

    # -----------------------------------------------------------
    # Abstract API (to be implemented by subclass)
    # -----------------------------------------------------------
    def start(self):
        """Initialize game UI and logic."""
        raise NotImplementedError("Subclasses must implement start().")

    def reset(self):
        """Reset game state for replay."""
        raise NotImplementedError("Subclasses must implement reset().")
