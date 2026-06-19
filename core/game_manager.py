# =====================================
# game_manager.py — FINAL CLEAN VERSION
# =====================================
import os
import sys
import importlib.util
import inspect
from core.base_game import BaseGame


# -----------------------------------------------------------
# Resource Path (for .exe and dev mode)
# -----------------------------------------------------------
def resource_path(relative_path):
    """
    Returns absolute path to resource.
    Works both in development and PyInstaller EXE.
    """
    try:
        base_path = sys._MEIPASS  # PyInstaller temp folder
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


# -----------------------------------------------------------
# Game Manager
# -----------------------------------------------------------
class GameManager:

    def __init__(self, db, games_path="games"):
        self.db = db          # ✅ THIS LINE IS MISSING IN YOUR FILE
        self.games_path = games_path
        self.games = {}
        self.load_games()

    # -----------------------------------------------------------
    # Scan and Load Games
    # -----------------------------------------------------------
    def load_games(self):
        print(f"[GameManager] Scanning games in: {self.games_path}")

        if not os.path.exists(self.games_path):
            print("[GameManager] Games folder not found.")
            return

        for folder in os.listdir(self.games_path):
            folder_path = os.path.join(self.games_path, folder)
            game_file = os.path.join(folder_path, "game.py")

            if not os.path.isdir(folder_path) or not os.path.exists(game_file):
                continue

            try:
                spec = importlib.util.spec_from_file_location(
                    f"games.{folder}.game", game_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseGame) and obj is not BaseGame:
                        self.games[folder] = obj
                        print(f"[GameManager] Loaded: {folder}")

            except Exception as e:
                print(f"[GameManager] Failed loading {folder}: {e}")

    # -----------------------------------------------------------
    # Access Methods
    # -----------------------------------------------------------
    def get_game_list(self):
        return list(self.games.keys())

    def launch_game(self, game_key):
        if game_key not in self.games:
            raise ValueError(f"Game not found: {game_key}")

        game_class = self.games[game_key]
        return game_class(self.db)

