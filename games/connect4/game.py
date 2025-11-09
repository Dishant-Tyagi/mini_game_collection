# =====================================
# Connect 4 — Circular Disc with Drop Animation
# =====================================
from core.base_game import BaseGame
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Color, Ellipse, Rectangle
from kivy.animation import Animation
from datetime import datetime


class Connect4Game(BaseGame):
    ROWS = 6
    COLS = 7

    COLORS = {
        "": (0.1, 0.3, 0.8, 1),     # board blue
        "X": (0.9, 0.1, 0.1, 1),    # red
        "O": (0.95, 0.9, 0.1, 1),   # yellow
    }

    def __init__(self, db):
        super().__init__(db, "Connect4")
        self.board = [["" for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_player = "X"
        self.cell_map = [[None for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.turn_label = None
        self.grid = None
        self._popup = None

    # -----------------------------------------------------------
    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def reset(self):
        self.board = [["" for _ in range(self.COLS)] for _ in range(self.ROWS)]
        self.current_player = "X"
        for r in range(self.ROWS):
            for c in range(self.COLS):
                self.update_cell_disc(r, c)
        if self.turn_label:
            self.turn_label.text = f"Player {self.current_player}'s Turn"

    def get_score(self):
        return 0

    def update(self, dt):
        pass

    # -----------------------------------------------------------
    # Gameplay
    # -----------------------------------------------------------
    def handle_input(self, col):
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][col] == "":
                self.board[row][col] = self.current_player
                self.update_cell_disc(row, col)

                if self.check_winner(row, col):
                    self.end_game(f"Player {self.current_player} wins!", self.current_player, "Win")
                elif all(self.board[r][c] != "" for r in range(self.ROWS) for c in range(self.COLS)):
                    self.end_game("It's a Draw!", "None", "Draw")
                else:
                    self.current_player = "O" if self.current_player == "X" else "X"
                    self.turn_label.text = f"Player {self.current_player}'s Turn"
                return
        self.show_message("Column is full!")

    def check_winner(self, row, col):
        player = self.board[row][col]
        if not player:
            return False

        def count_dir(dr, dc):
            r, c, count = row + dr, col + dc, 0
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                count += 1
                r += dr
                c += dc
            return count

        for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:
            total = 1 + count_dir(dr, dc) + count_dir(-dr, -dc)
            if total >= 4:
                return True
        return False

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

        top_row = GridLayout(cols=self.COLS, spacing=5, size_hint_y=None, height=50)
        for c in range(self.COLS):
            btn = Button(
                text=str(c + 1),
                font_size=20,
                on_release=lambda x, col=c: self.handle_input(col),
            )
            top_row.add_widget(btn)
        layout.add_widget(top_row)

        self.grid = GridLayout(cols=self.COLS, spacing=3)
        for r in range(self.ROWS):
            for c in range(self.COLS):
                cell = Button(disabled=True)
                self.cell_map[r][c] = cell
                self.update_cell_disc(r, c)
                self.grid.add_widget(cell)
        layout.add_widget(self.grid)

        layout.add_widget(Button(text="Restart", size_hint_y=None, height=40, on_release=lambda x: self.reset()))
        layout.add_widget(Button(text="Back to Menu", size_hint_y=None, height=40, on_release=lambda x: app.switch_to("menu")))

        screen.add_widget(layout)
        app.switch_to("game")

    # -----------------------------------------------------------
    # Drawing + Animation
    # -----------------------------------------------------------
    def update_cell_disc(self, row, col):
        """Draw a disc and animate falling."""
        cell = self.cell_map[row][col]
        state = self.board[row][col]
        cell.canvas.before.clear()

        # Base
        with cell.canvas.before:
            Color(0.05, 0.05, 0.05, 1)
            Rectangle(pos=cell.pos, size=cell.size)

        if state:
            color = self.COLORS[state]
            disc_size = min(cell.width, cell.height) * 0.8
            start_y = cell.top + 150
            end_y = cell.y + (cell.height - disc_size) / 2
            x_pos = cell.x + (cell.width - disc_size) / 2

            with cell.canvas.after:
                Color(*color)
                disc = Ellipse(pos=(x_pos, start_y), size=(disc_size, disc_size))

            self._animate_disc_fall(disc, (x_pos, end_y))

        cell.bind(pos=lambda i, v: self.update_cell_disc(row, col))
        cell.bind(size=lambda i, v: self.update_cell_disc(row, col))
        cell.text = ""

    def _animate_disc_fall(self, disc, final_pos):
        anim = Animation(pos=final_pos, duration=0.35, t='out_bounce')
        anim.start(disc)

    # -----------------------------------------------------------
    # Popups
    # -----------------------------------------------------------
    def show_message(self, message):
        box = BoxLayout(orientation="vertical", padding=10, spacing=5)
        box.add_widget(Label(text=message, font_size=18))
        ok_btn = Button(text="OK", size_hint_y=None, height=40)
        popup = Popup(title="Notice", content=box, size_hint=(0.5, 0.3))
        ok_btn.bind(on_release=popup.dismiss)
        box.add_widget(ok_btn)
        popup.open()

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
        duration = str(datetime.now() - self.start_time).split(".")[0]
        self.db.record_match(self.game_name, winner, result)
        app.switch_to("stats")
