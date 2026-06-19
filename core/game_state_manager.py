class GameStateManager:
    MENU = "MENU"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    GAME_OVER = "GAME_OVER"
    STATS = "STATS"

    def __init__(self):
        self.current_state = self.MENU
        self.active_game = None

    def set_state(self, new_state):
        print(f"[GameState] {self.current_state} → {new_state}")
        self.current_state = new_state

    def get_state(self):
        return self.current_state

    def set_active_game(self, game):
        self.active_game = game

    def clear_active_game(self):
        self.active_game = None

    def get_active_game(self):
        return self.active_game
    def notify_move(self, move_data):
        if self.app.multiplayer_manager and self.app.multiplayer_manager.enabled:
            self.app.multiplayer_manager.send_move(move_data)
