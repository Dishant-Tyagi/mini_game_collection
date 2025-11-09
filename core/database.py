# =====================================
# database.py — Match-based session model
# =====================================
from pymongo import MongoClient
from datetime import datetime
import logging, atexit

# Silence PyMongo debug logs
logging.getLogger("pymongo").setLevel(logging.WARNING)


class Database:
    def __init__(self, uri="mongodb://localhost:27017/", db_name="mini_game_collection"):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.db = self.client[db_name]
            self.user_col = self.db["user"]
            self.stats_col = self.db["match_history"]
            self.settings_col = self.db["settings"]

            self.init_defaults()
            self.reset_session_data()  # clear matches on startup
            atexit.register(self.reset_session_data)  # clear again when app closes

            print("[DB] Connected successfully — session match tracking active.")
        except Exception as e:
            print(f"[DB ERROR] Connection failed: {e}")

    # -----------------------------------------------------------
    # Initialization
    # -----------------------------------------------------------
    def init_defaults(self):
        if self.user_col.count_documents({}) == 0:
            self.user_col.insert_one({
                "_id": 1,
                "username": "Player1",
                "games_played": 0,
                "total_matches": 0,
                "last_login": datetime.now().isoformat()
            })
            print("[DB] Default user created.")

        if self.settings_col.count_documents({}) == 0:
            self.settings_col.insert_one({
                "_id": 1,
                "theme": "dark",
                "sound": True,
                "difficulty": "medium"
            })
            print("[DB] Default settings created.")

    # -----------------------------------------------------------
    # Session Reset
    # -----------------------------------------------------------
    def reset_session_data(self):
        result = self.stats_col.delete_many({})
        print(f"[DB] Cleared {result.deleted_count} old matches (new session).")

    # -----------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------
    def record_match(self, game_name: str, winner: str, result: str):
        doc = {
            "game_name": game_name,
            "winner": winner,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        self.stats_col.insert_one(doc)
        print(f"[DB] Recorded match: {game_name} | {result} | winner={winner}")

    def get_matches(self):
        return list(self.stats_col.find({}).sort("timestamp", -1))
