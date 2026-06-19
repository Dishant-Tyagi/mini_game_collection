# =====================================
# Chess — Clean Professional UI
# =====================================
import logging
from kivy.core.window import Window
from kivy.utils import get_color_from_hex

# ------------------ LOGGING CLEANUP ------------------
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("kivy").setLevel(logging.WARNING)
Window.clearcolor = get_color_from_hex("#10121A")

from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.core.image import Image as CoreImage


class ChessGame(BaseGame):

    BOARD_SIZE = 8

    def __init__(self, db):
        super().__init__(db, "Chess")

        self.app = None
        self.board_widget = None
        self.selected = None
        self.valid_moves = []
        self.current_player = "w"

        self.piece_cache = {}

    # --------------------------------------------------
    # Lifecycle
    # --------------------------------------------------
    def start(self, app):
        self.app = app
        self.begin_session()
        self.build_ui()
        self.reset()

    def reset(self):
        self.init_board()
        self.selected = None
        self.valid_moves = []
        self.current_player = "w"
        self.draw_board()

    # --------------------------------------------------
    # UI
    # --------------------------------------------------
    def build_ui(self):
        screen = self.app.game_screen
        screen.clear_widgets()

        root = BoxLayout(orientation="vertical", spacing=0, padding=0)

        self.turn_label = Label(
            text="White Turn",
            size_hint_y=None,
            height=50,
            font_size=22
        )
        root.add_widget(self.turn_label)

        self.board_widget = Widget()
        root.add_widget(self.board_widget)

        btns = BoxLayout(size_hint_y=None, height=50)
        btns.add_widget(Button(text="Restart", on_release=lambda *_: self.reset()))
        btns.add_widget(Button(text="Menu", on_release=lambda *_: self.app.switch_to("menu")))
        root.add_widget(btns)

        screen.add_widget(root)
        self.app.switch_to("game")

        self.board_widget.bind(on_touch_down=self.on_touch)
        self.board_widget.bind(size=lambda *_: self.draw_board())

    # --------------------------------------------------
    # Board Setup
    # --------------------------------------------------
    def init_board(self):
        self.multiplayer_enabled = False
        self.local_player_color = "w"   # default
        self.input_locked = False

        self.board = [
            ["bR","bN","bB","bQ","bK","bB","bN","bR"],
            ["bP"]*8,
            [""]*8,
            [""]*8,
            [""]*8,
            [""]*8,
            ["wP"]*8,
            ["wR","wN","wB","wQ","wK","wB","wN","wR"],
        ]

    # --------------------------------------------------
    # Drawing (Perfect Square + Clean)
    # --------------------------------------------------
    def draw_board(self):
        self.board_widget.canvas.clear()

        w = self.board_widget.width
        h = self.board_widget.height

        board_size = min(w, h)
        cell = board_size / 8

        offset_x = self.board_widget.x + (w - board_size) / 2
        offset_y = self.board_widget.y + (h - board_size) / 2

        with self.board_widget.canvas:

            for r in range(8):
                for c in range(8):

                    x = offset_x + c * cell
                    y = offset_y + r * cell

                    # Modern soft theme
                    if (r + c) % 2 == 0:
                        Color(0.92, 0.92, 0.92)
                    else:
                        Color(0.35, 0.45, 0.55)

                    Rectangle(pos=(x, y), size=(cell, cell))

                    # Selected highlight
                    if self.selected == (r, c):
                        Color(0, 0.6, 1, 0.4)
                        Rectangle(pos=(x, y), size=(cell, cell))

                    # Valid move highlight
                    if (r, c) in self.valid_moves:
                        Color(0, 1, 0, 0.3)
                        Rectangle(pos=(x, y), size=(cell, cell))

                    piece = self.board[r][c]
                    if piece:
                        texture = self.get_piece_texture(piece)
                        Rectangle(
                            texture=texture,
                            pos=(x + cell*0.1, y + cell*0.1),
                            size=(cell*0.8, cell*0.8)
                        )

    # --------------------------------------------------
    # Piece Texture Cache
    # --------------------------------------------------
    def get_piece_texture(self, piece):
        if piece in self.piece_cache:
            return self.piece_cache[piece]

        path = f"games/chess/assets/{piece}.png"
        texture = CoreImage(path).texture
        self.piece_cache[piece] = texture
        return texture

    # --------------------------------------------------
    # Input
    # --------------------------------------------------
    def on_touch(self, widget, touch):
        if self.input_locked:
            return
        if self.multiplayer_enabled:
            if self.current_player != self.local_player_color:
                return

        if not widget.collide_point(*touch.pos):
            return

        w = widget.width
        h = widget.height
        board_size = min(w, h)
        cell = board_size / 8

        offset_x = widget.x + (w - board_size) / 2
        offset_y = widget.y + (h - board_size) / 2

        col = int((touch.x - offset_x) / cell)
        row = int((touch.y - offset_y) / cell)

        if not (0 <= row < 8 and 0 <= col < 8):
            return

        piece = self.board[row][col]

        if self.selected:
            if (row, col) in self.valid_moves:
                self.move_piece(self.selected, (row, col))
                self.switch_turn()
            self.selected = None
            self.valid_moves = []
            self.draw_board()

        elif piece and piece[0] == self.current_player:
            self.selected = (row, col)
            self.valid_moves = self.get_valid_moves(row, col)
            self.draw_board()
        


    # --------------------------------------------------
    # Minimal Move Logic Hook
    # (Keep your existing logic if already implemented)
    # --------------------------------------------------
    def get_valid_moves(self, r, c):
        return []  # Keep your existing logic

    def move_piece(self, start, end):
        sr, sc = start
        er, ec = end
        self.board[er][ec] = self.board[sr][sc]
        self.board[sr][sc] = ""

    def switch_turn(self):
        self.current_player = "b" if self.current_player == "w" else "w"
        self.turn_label.text = "White Turn" if self.current_player == "w" else "Black Turn"
        
    def is_in_bounds(self, r, c):
        return 0 <= r < 8 and 0 <= c < 8


    def is_enemy(self, piece):
        return piece and piece[0] != self.current_player


    def is_friend(self, piece):
        return piece and piece[0] == self.current_player

    def get_valid_moves(self, r, c):
        piece = self.board[r][c]
        if not piece:
            return []

        raw_moves = self.get_raw_moves(r, c, piece)

        legal_moves = []
        for move in raw_moves:
            if not self.would_cause_check((r, c), move):
                legal_moves.append(move)

        return legal_moves
    def would_cause_check(self, start, end):
        temp = [row[:] for row in self.board]

        sr, sc = start
        er, ec = end

        temp[er][ec] = temp[sr][sc]
        temp[sr][sc] = ""

        return self.is_in_check(self.current_player, temp)
    
    def is_in_check(self, color, board):
        king_pos = None

        for r in range(8):
            for c in range(8):
                if board[r][c] == color + "K":
                    king_pos = (r, c)
                    break

        enemy = "b" if color == "w" else "w"

        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece and piece[0] == enemy:
                    moves = self.get_raw_moves(r, c, piece, board_override=board)
                    if king_pos in moves:
                        return True

        return False
    
    def get_raw_moves(self, r, c, piece, board_override=None):
        board = board_override if board_override else self.board
        color = piece[0]
        p = piece[1]
        moves = []

        directions = []

        if p == "P":
            direction = -1 if color == "w" else 1
            if self.is_in_bounds(r + direction, c) and not board[r + direction][c]:
                moves.append((r + direction, c))

            for dc in [-1, 1]:
                nr, nc = r + direction, c + dc
                if self.is_in_bounds(nr, nc):
                    if board[nr][nc] and board[nr][nc][0] != color:
                        moves.append((nr, nc))

        elif p == "R":
            directions = [(1,0),(-1,0),(0,1),(0,-1)]

        elif p == "B":
            directions = [(1,1),(1,-1),(-1,1),(-1,-1)]

        elif p == "Q":
            directions = [(1,0),(-1,0),(0,1),(0,-1),
                        (1,1),(1,-1),(-1,1),(-1,-1)]

        elif p == "N":
            jumps = [(2,1),(2,-1),(-2,1),(-2,-1),
                    (1,2),(1,-2),(-1,2),(-1,-2)]
            for dr, dc in jumps:
                nr, nc = r + dr, c + dc
                if self.is_in_bounds(nr, nc):
                    if not board[nr][nc] or board[nr][nc][0] != color:
                        moves.append((nr, nc))
            return moves

        elif p == "K":
            for dr in [-1,0,1]:
                for dc in [-1,0,1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if self.is_in_bounds(nr, nc):
                        if not board[nr][nc] or board[nr][nc][0] != color:
                            moves.append((nr, nc))
            return moves

    # Sliding pieces
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while self.is_in_bounds(nr, nc):
                if not board[nr][nc]:
                    moves.append((nr, nc))
                else:
                    if board[nr][nc][0] != color:
                        moves.append((nr, nc))
                    break
                nr += dr
                nc += dc

        return moves
    def serialize_move(self, start, end):
        return {
            "type": "move",
            "from": start,
            "to": end,
            "player": self.current_player
        }
    def apply_remote_move(self, move_data):
        start = tuple(move_data["from"])
        end = tuple(move_data["to"])

        self.move_piece(start, end)
        self.switch_turn()

        self.input_locked = False
        self.draw_board()





