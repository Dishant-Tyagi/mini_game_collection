import logging
from pymongo import MongoClient
from datetime import datetime
from threading import Lock

# --- Set up clean logging ---
logger = logging.getLogger("MiniGameCollection.DB")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setFormatter(logging.Formatter("[DB] %(message)s"))
logger.addHandler(console)


class Database:
    """MongoDB handler with session-aware match tracking."""
    _lock = Lock()

    def __init__(self):
        try:
            self.client = MongoClient(
                "mongodb://localhost:27017/",
                serverSelectionTimeoutMS=2000
            )
            self.db = self.client["mini_game_collection"]
            self.stats = self.db["game_stats"]
            self.client.admin.command("ping")
            logger.info("Connected successfully to MongoDB.")
        except Exception as e:
            self.client = None
            self.db = None
            self.stats = None
            logger.error(f"Connection failed: {e}")

    def clear_previous_session(self):
        """Clears old matches from previous runs."""
        if self.stats is None:
            logger.warning("No DB collection initialized.")
            return
        try:
            result = self.stats.delete_many({"session": "active"})
            logger.info(f"Cleared {result.deleted_count} old matches (new session).")
        except Exception as e:
            logger.error(f"Session clear failed: {e}")

    def record_match(self, game_name, result, duration):
        """Insert a match record."""
        if self.stats is None:
            logger.warning("Skipping record — no DB connection.")
            return
        try:
            with self._lock:
                data = {
                    "game_name": game_name,
                    "result": result,
                    "duration": str(duration),
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "session": "active",
                }
                self.stats.insert_one(data)
                logger.info(f"Recorded: {game_name} | {duration} | result={result}")
        except Exception as e:
            logger.error(f"Insert failed: {e}")

    def get_recent_stats(self, limit=10):
        """Fetch recent stats safely."""
        if self.stats is None:
            logger.warning("No DB connection for fetching stats.")
            return []
        try:
            with self._lock:
                return list(self.stats.find().sort("timestamp", -1).limit(limit))
        except Exception as e:
            logger.error(f"Fetch failed: {e}")
            return []
