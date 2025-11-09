from core.database import Database
from core.game_manager import GameManager

db = Database()
gm = GameManager(db)

print("\nAvailable Games:", gm.get_game_list())
game = gm.launch_game("dummy_test")
game.start()
