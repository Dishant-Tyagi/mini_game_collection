# =====================================
# Tic Tac Toe — Classic X/O with Animated Pop + Winner Glow
# =====================================
from core.base_game import BaseGame
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.animation import Animation
from kivy.clock import Clock
from datetime import datetime


class TicTacToeGame(BaseGame):
    COLORS = {
        "": (0.1, 0.3, 0.8, 1),     # blue background
        "X": (0.9, 0.1, 0.1, 1),    # red highlight
        "O": (0.95, 0.9, 0.1, 1),   # yellow highlight
    }

    def __init__(self, db):
        super().__init__(db, "TicTacToe")
        self.board = [""] * 9
        self.current_player = "X"
        self.cell_map = [None] * 9
        self.turn_label = None
        self._popup = None

    # -----------------------------------------------------------
    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def reset(self):
        self.board = [""] * 9
        self.current_player = "X"
        for i in range(9):
            self.update_cell(i)
        if self.turn_label:
            self.turn_label.text = f"Player {self.current_player}'s Turn"


    # -----------------------------------------------------------
    # Gameplay
    # -----------------------------------------------------------
    def handle_input(self, index):
        if self.board[index] != "":
            return
        self.board[index] = self.current_player
        self.update_cell(index)

        winner, combo = self.check_winner()
        if winner:
            self.highlight_winner(combo)
            # delay popup slightly to allow glow to finish
            Clock.schedule_once(lambda dt: self.end_game(f"Player {winner} wins!", winner, "Win"), 0.8)
        elif "" not in self.board:
            self.end_game("It's a Draw!", "None", "Draw")
        else:
            self.current_player = "O" if self.current_player == "X" else "X"
            self.turn_label.text = f"Player {self.current_player}'s Turn"

    def check_winner(self):
        combos = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6],
        ]
        for combo in combos:
            a, b, c = combo
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                return self.board[a], combo
        return None, None

    # -----------------------------------------------------------
    # UI
    # -----------------------------------------------------------
    def build_ui(self, app):
        screen = app.game_screen
        screen.clear_widgets()

        layout = BoxLayout(orientation="vertical", padding=10, spacing=10)

        self.turn_label = Label(
            text=f"Player {self.current_player}'s Turn",
            font_size=22,
            size_hint_y=None,
            height=40,
        )
        layout.add_widget(self.turn_label)

        self.grid = GridLayout(cols=3, spacing=5)
        for i in range(9):
            cell = Button(
                font_size=60,
                on_release=lambda x, idx=i: self.handle_input(idx)
            )
            self.cell_map[i] = cell
            self.update_cell(i)
            self.grid.add_widget(cell)
        layout.add_widget(self.grid)

        layout.add_widget(Button(text="Restart", size_hint_y=None, height=40, on_release=lambda x: self.reset()))
        layout.add_widget(Button(text="Back to Menu", size_hint_y=None, height=40, on_release=lambda x: app.switch_to("menu")))

        screen.add_widget(layout)
        app.switch_to("game")

    # -----------------------------------------------------------
    # Draw + Animate X/O
    # -----------------------------------------------------------
    def update_cell(self, index):
        cell = self.cell_map[index]
        state = self.board[index]
        cell.canvas.before.clear()

        with cell.canvas.before:
            Color(0.05, 0.05, 0.05, 1)
            Rectangle(pos=cell.pos, size=cell.size)
            if state:
                Color(*self.COLORS[state])
                disc_size = min(cell.width, cell.height) * 0.9
                offset_x = cell.x + (cell.width - disc_size) / 2
                offset_y = cell.y + (cell.height - disc_size) / 2
                Ellipse(pos=(offset_x, offset_y), size=(disc_size, disc_size))

        cell.text = state
        if state:
            cell.color = (1, 1, 1, 0)
            cell.font_size = 0
            anim = (
                Animation(color=(1, 1, 1, 1), font_size=72, duration=0.2, t='out_back')
                + Animation(font_size=60, duration=0.1)
            )
            anim.start(cell)

        cell.bind(pos=lambda i, v: self.update_cell(index))
        cell.bind(size=lambda i, v: self.update_cell(index))

    # -----------------------------------------------------------
    # Winner Glow Animation
    # -----------------------------------------------------------
    def highlight_winner(self, combo):
        """Blink winning cells 3 times (yellow-white)."""
        if not combo:
            return

        def glow_cycle(cell, repeat=3):
            if repeat <= 0:
                return
            anim = Animation(color=(1, 1, 0, 1), duration=0.2) + Animation(color=(1, 1, 1, 1), duration=0.2)
            anim.bind(on_complete=lambda *a: glow_cycle(cell, repeat - 1))
            anim.start(cell)

        for idx in combo:
            cell = self.cell_map[idx]
            glow_cycle(cell)

    # -----------------------------------------------------------
    # Popups
    # -----------------------------------------------------------
    def end_game(self, message, winner, result):
        self.show_popup(message, winner, result)

    def show_popup(self, message, winner, result):
        from kivy.app import App
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text=message, font_size=20))
        ok_btn = Button(text="OK", size_hint_y=None, height=40)
        ok_btn.bind(on_release=lambda x: self.close_popup(app, winner, result))
        box.add_widget(ok_btn)
        self._popup = Popup(title="Game Over", content=box, size_hint=(0.6, 0.4))
        self._popup.open()

    def close_popup(self, app, winner, result):
        if self._popup:
            self._popup.dismiss()
        self.db.record_match(self.game_name, winner, result)
        app.switch_to("stats")
