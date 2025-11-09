# =====================================
# game_manager.py
# =====================================
import os
import importlib.util
import inspect
from core.base_game import BaseGame


class GameManager:
    """
    Scans, loads, and manages all game modules under /games/.
    Enables dynamic discovery of games without manual registration.
    """

    def __init__(self, db, games_path="games"):
        self.db = db
        self.games_path = games_path
        self.games = {}  # {game_name: class_ref}
        self.load_games()

    # -----------------------------------------------------------
    #  Game Discovery & Loading
    # -----------------------------------------------------------
    def load_games(self):
        """Scans the games directory and imports all valid games."""
        print("[GameManager] Scanning for games...")
        if not os.path.exists(self.games_path):
            print(f"[GameManager] Directory '{self.games_path}' not found.")
            return

        for folder in os.listdir(self.games_path):
            folder_path = os.path.join(self.games_path, folder)
            game_file = os.path.join(folder_path, "game.py")

            if not os.path.isdir(folder_path) or not os.path.exists(game_file):
                continue  # skip invalid entries

            try:
                # dynamic import
                spec = importlib.util.spec_from_file_location(f"games.{folder}.game", game_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # find classes inheriting from BaseGame
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseGame) and obj is not BaseGame:
                        self.games[folder] = obj
                        print(f"[GameManager] Loaded game: {folder} ({name})")

            except Exception as e:
                print(f"[GameManager] Error loading '{folder}': {e}")

    # -----------------------------------------------------------
    #  Access Methods
    # -----------------------------------------------------------
    def get_game_list(self):
        """Returns a list of discovered games."""
        return list(self.games.keys())

    def launch_game(self, game_name):
        """Creates a new instance of the selected game."""
        if game_name not in self.games:
            raise ValueError(f"Game '{game_name}' not found.")
        game_class = self.games[game_name]
        return game_class(self.db)

    def reload_games(self):
        """Re-scan the games directory."""
        self.games.clear()
        self.load_games()
        print("[GameManager] Game list reloaded.")
