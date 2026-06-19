from .lan_transport import LanTransport
from kivy.clock import Clock

class MultiplayerManager:

    def __init__(self, app):
        self.app = app
        self.transport = None
        self.active_game = None
        self.enabled = False

    # --------------------------
    # Setup
    # --------------------------
    def host_game(self, port=5555):
        self.enabled = True
        self.transport = LanTransport(self._on_receive, host=True, port=port)
        self.transport.start()

    def join_game(self, ip, port=5555):
        self.enabled = True
        self.transport = LanTransport(self._on_receive, host=False, ip=ip, port=port)
        self.transport.start()

    def attach_game(self, game):
        self.active_game = game
        game.multiplayer_enabled = True

        if self.transport.host:
            game.player_role = 1  # Red
            game.is_my_turn = True
        else:
            game.player_role = 2  # White
            game.is_my_turn = False


    # --------------------------
    # Sending Moves
    # --------------------------
    def send_move(self, move_data):
        if self.transport:
            self.transport.send(move_data)

    # --------------------------
    # Receiving Moves
    # --------------------------
    

    def _on_receive(self, data):
        if self.active_game:
        # Ensure UI updates happen in main thread
            Clock.schedule_once(
                lambda dt: self.active_game.apply_remote_move(eval(data))
            )

    # --------------------------
    # Cleanup
    # --------------------------
    def close(self):
        if self.transport:
            self.transport.close()
        self.enabled = False