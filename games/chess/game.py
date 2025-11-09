import os
import time
import copy
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.graphics import Rectangle
from kivy.utils import get_color_from_hex
from core.base_game import BaseGame


# Board colors
LIGHT = get_color_from_hex("#EEEED2")
DARK = get_color_from_hex("#769656")
HIGHLIGHT = get_color_from_hex("#f7ec8b")


class ChessGame(BaseGame):
    GAME_NAME = "Chess"

    def __init__(self, db):
        super().__init__(db, self.GAME_NAME)
        self.board = []
        self.buttons = []
        self.selected = None
        self.legal_moves = []
        self.turn = "w"
        self.root_layout = None
        self.grid = None
        self.top_label = None
        self.start_time = None
        self.running = False

        # Automatically detect asset path
        self.asset_path = os.path.join(os.path.dirname(__file__), "assets") + os.sep

    # ---------------------- INIT & SETUP ----------------------
    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def reset(self):
        self._init_board()
        self.selected = None
        self.legal_moves = []
        self.turn = "w"
        self.start_time = time.time()
        self.running = True
        self._render_board()
        self._update_top_label()

    def get_score(self):
        return f"{self.turn} to move"

    def _init_board(self):
        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bP"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["--"] * 8,
            ["wP"] * 8,
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"],
        ]

    # ---------------------- UI ----------------------
    def build_ui(self, app):
        screen = app.game_screen
        screen.clear_widgets()

        self.root_layout = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.top_label = Label(text="White to move", font_size=22, size_hint_y=None, height=44)
        self.root_layout.add_widget(self.top_label)

        # Board
        self.grid = GridLayout(cols=8, rows=8)
        self.buttons = []
        for r in range(8):
            row_buttons = []
            for c in range(8):
                b = Button(on_release=lambda inst, rr=r, cc=c: self._on_square(rr, cc))
                b.background_normal = ''
                b.background_color = LIGHT if (r + c) % 2 == 0 else DARK
                row_buttons.append(b)
                self.grid.add_widget(b)
            self.buttons.append(row_buttons)

        self.root_layout.add_widget(self.grid)

        # Controls
        bottom = BoxLayout(size_hint_y=None, height=56, spacing=10, padding=[8, 6])
        bottom.add_widget(Button(text="Restart", on_release=lambda x: self.reset()))
        bottom.add_widget(Button(text="Back to Menu", on_release=lambda x: app.switch_to("menu")))
        self.root_layout.add_widget(bottom)

        screen.add_widget(self.root_layout)
        app.switch_to("game")

        Window.bind(on_key_down=self._on_key_down)

    def _on_key_down(self, instance, key, scancode, codepoint, modifiers):
        if codepoint and codepoint.lower() == "r":
            self.reset()

    # ---------------------- INPUT ----------------------
    def _on_square(self, r, c):
        if not self.running:
            return
        piece = self.board[r][c]
        piece_color = piece[0] if piece != "--" else None

        if self.selected is None:
            if piece != "--" and piece_color == self.turn:
                self.selected = (r, c)
                self.legal_moves = self._generate_legal_moves_for_piece(r, c)
                self._highlight_selection()
            return

        if self.selected == (r, c):
            self.selected = None
            self.legal_moves = []
            self._render_board()
            return

        if (r, c) in self.legal_moves:
            self._make_move(self.selected, (r, c))
            self.selected = None
            self.legal_moves = []
            self._render_board()
            return

        if piece != "--" and piece_color == self.turn:
            self.selected = (r, c)
            self.legal_moves = self._generate_legal_moves_for_piece(r, c)
            self._highlight_selection()

    # ---------------------- RENDER ----------------------
    def _render_board(self):
        """Render chessboard with visible piece images."""
        for r in range(8):
            for c in range(8):
                b = self.buttons[r][c]
                piece = self.board[r][c]

            # Clear previous drawing layers
                b.canvas.after.clear()
                b.background_normal = ''
                b.background_down = ''
                b.background_color = LIGHT if (r + c) % 2 == 0 else DARK
                b.text = ""

                if piece != "--":
                    img_path = os.path.join(self.asset_path, f"{piece}.png")
                    if os.path.exists(img_path):
                        with b.canvas.after:
                            rect = Rectangle(source=img_path, pos=b.pos, size=b.size)

                    # Keep rectangle in sync with layout
                        def update_rect(instance, value, rect=rect):
                            rect.pos = instance.pos
                            rect.size = instance.size

                        b.bind(pos=update_rect, size=update_rect)
        self._update_top_label()


    def _highlight_selection(self):
        self._render_board()
        if self.selected:
            r, c = self.selected
            self.buttons[r][c].background_color = HIGHLIGHT
        for (mr, mc) in self.legal_moves:
            self.buttons[mr][mc].background_color = [0.2, 0.65, 0.2, 1]

    def _update_top_label(self):
        self.top_label.text = "White to move" if self.turn == "w" else "Black to move"

    # ---------------------- GAME LOGIC ----------------------
    def _make_move(self, src, dst):
        sr, sc = src
        dr, dc = dst
        moving = self.board[sr][sc]
        self.board[dr][dc] = moving
        self.board[sr][sc] = "--"

        # Pawn promotion
        if moving[1] == "P":
            if (moving[0] == "w" and dr == 0) or (moving[0] == "b" and dr == 7):
                self.board[dr][dc] = moving[0] + "Q"

        self.turn = "b" if self.turn == "w" else "w"
        self._update_top_label()

        if not self._player_has_any_legal_moves(self.turn):
            if self._is_in_check(self.turn):
                winner = "White" if self.turn == "b" else "Black"
                self._end_game(f"{winner} wins by checkmate")
            else:
                self._end_game("Draw by stalemate")

    def _end_game(self, result_text):
        self.running = False
        duration = int(time.time() - (self.start_time or time.time()))
        duration_str = f"{duration // 60:02d}:{duration % 60:02d}"
        try:
            if hasattr(self.db, "record_match"):
                self.db.record_match(self.game_name, result_text, duration_str)
            else:
                self.db.insert_game_stat(self.game_name, result_text, duration_str)
        except Exception:
            pass
        from kivy.app import App
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text=result_text, halign="center"))
        btns = BoxLayout(size_hint_y=None, height=40, spacing=10)
        r = Button(text="Restart")
        r.bind(on_release=lambda *_: (popup.dismiss(), self.reset()))
        m = Button(text="Menu")
        m.bind(on_release=lambda *_: (popup.dismiss(), app.switch_to("menu")))
        btns.add_widget(r)
        btns.add_widget(m)
        box.add_widget(btns)
        popup = Popup(title="Game Over", content=box, size_hint=(0.5, 0.4))
        popup.open()

    # ---------------------- MOVE GENERATION ----------------------
    def _generate_legal_moves_for_piece(self, r, c):
        piece = self.board[r][c]
        if piece == "--":
            return []
        color = piece[0]
        pseudo = self._generate_pseudo_moves(r, c, piece)
        legal = []
        for (dr, dc) in pseudo:
            b2 = copy.deepcopy(self.board)
            b2[dr][dc], b2[r][c] = b2[r][c], "--"
            if not self._is_in_check_for_board(b2, color):
                legal.append((dr, dc))
        return legal

    def _generate_pseudo_moves(self, r, c, piece):
        t, color, moves = piece[1], piece[0], []
        if t == "P":
            f = -1 if color == "w" else 1
            s = 6 if color == "w" else 1
            if 0 <= r + f < 8 and self.board[r + f][c] == "--":
                moves.append((r + f, c))
                if r == s and self.board[r + 2 * f][c] == "--":
                    moves.append((r + 2 * f, c))
            for dc in (-1, 1):
                nr, nc = r + f, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    target = self.board[nr][nc]
                    if target != "--" and target[0] != color:
                        moves.append((nr, nc))
            return moves
        if t == "N":
            for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (self.board[nr][nc] == "--" or self.board[nr][nc][0] != color):
                    moves.append((nr, nc))
            return moves
        if t == "K":
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr or dc:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and (self.board[nr][nc] == "--" or self.board[nr][nc][0] != color):
                            moves.append((nr, nc))
            return moves
        dirs = []
        if t == "R": dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        if t == "B": dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        if t == "Q": dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                t2 = self.board[nr][nc]
                if t2 == "--":
                    moves.append((nr, nc))
                else:
                    if t2[0] != color:
                        moves.append((nr, nc))
                    break
                nr += dr; nc += dc
        return moves

    def _is_in_check(self, color):
        return self._is_in_check_for_board(self.board, color)

    def _is_in_check_for_board(self, b, color):
        king, pos = color + "K", None
        for r in range(8):
            for c in range(8):
                if b[r][c] == king:
                    pos = (r, c)
                    break
            if pos: break
        if not pos:
            return True
        opp = "b" if color == "w" else "w"
        for r in range(8):
            for c in range(8):
                p = b[r][c]
                if p != "--" and p[0] == opp:
                    if pos in self._pseudo_moves_for_board(b, r, c):
                        return True
        return False

    def _pseudo_moves_for_board(self, b, r, c):
        p = b[r][c]
        if p == "--":
            return []
        t, color, moves = p[1], p[0], []
        if t == "P":
            f = -1 if color == "w" else 1
            for dc in (-1, 1):
                nr, nc = r + f, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    moves.append((nr, nc))
            return moves
        if t == "N":
            for dr, dc in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    moves.append((nr, nc))
            return moves
        if t == "K":
            for dr in (-1,0,1):
                for dc in (-1,0,1):
                    if dr or dc:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            moves.append((nr, nc))
            return moves
        dirs = []
        if t == "R": dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        if t == "B": dirs = [(-1,-1),(-1,1),(1,-1),(1,1)]
        if t == "Q": dirs = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                moves.append((nr, nc))
                if b[nr][nc] != "--":
                    break
                nr += dr
                nc += dc
        return moves

    def _player_has_any_legal_moves(self, color):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p != "--" and p[0] == color:
                    if self._generate_legal_moves_for_piece(r, c):
                        return True
        return False
