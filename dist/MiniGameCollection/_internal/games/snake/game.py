# =====================================
# Snake Game — Image-Based, Scaled & Aligned
# =====================================
from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.uix.popup import Popup
import os
import random


class SnakeGame(BaseGame):
    GRID_WIDTH = 40
    GRID_HEIGHT = 40
    MOVE_INTERVAL = 0.1  # seconds per move

    DIRECTIONS = {
        'up': (0, 1),
        'down': (0, -1),
        'left': (-1, 0),
        'right': (1, 0),
    }

    def __init__(self, db):
        super().__init__(db, "Snake")
        self.snake = [(5, 5), (5, 4), (5, 3)]
        self.direction = 'right'
        self.food = (10, 10)
        self.score = 0
        self.running = False
        self.grid_widget = None
        self.turn_label = None
        self.clock_event = None
        self.cell_size = 20

        # Asset paths
        asset_dir = os.path.join(os.path.dirname(__file__), "assets")
        self.head_img = os.path.join(asset_dir, "head.png")
        self.body_img = os.path.join(asset_dir, "body.png")
        self.food_img = os.path.join(asset_dir, "food.png")

    # -----------------------------------------------------------
    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def reset(self):
        self.snake = [(5, 5), (5, 4), (5, 3)]
        self.direction = 'right'
        self.spawn_food()
        self.score = 0
        self.running = True
        self.update_grid()
        if self.clock_event:
            self.clock_event.cancel()
        self.clock_event = Clock.schedule_interval(self.update, self.MOVE_INTERVAL)

    def get_score(self):
        return self.score

    def end_game(self, message="Game Over"):
        self.running = False
        if self.clock_event:
            self.clock_event.cancel()
        duration = self.end_session()
        self.db.record_match(self.game_name, str(self.score), duration)
        self.show_popup(f"{message}\nScore: {self.score}")

    # -----------------------------------------------------------
    # UI
    # -----------------------------------------------------------
    def build_ui(self, app):
        screen = app.game_screen
        screen.clear_widgets()

        # Main vertical layout
        layout = BoxLayout(orientation="vertical", spacing=8, padding=5)

        # Score label (top)
        self.turn_label = Label(
            text="Score: 0",
            font_size=22,
            size_hint_y=None,
            height=40
        )
        layout.add_widget(self.turn_label)

        # Grid widget (center)
        self.grid_widget = Widget(size_hint=(1, 1))
        layout.add_widget(self.grid_widget)

        # Buttons (bottom)
        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10, padding=[10, 0])
        btn_box.add_widget(Button(text="Restart", on_release=lambda x: self.reset()))
        btn_box.add_widget(Button(text="Back to Menu", on_release=lambda x: app.switch_to("menu")))

        # Optional background for buttons
        with btn_box.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            self.btn_bg = Rectangle(pos=btn_box.pos, size=btn_box.size)
        btn_box.bind(pos=lambda i, v: setattr(self.btn_bg, 'pos', i.pos))
        btn_box.bind(size=lambda i, v: setattr(self.btn_bg, 'size', i.size))

        layout.add_widget(btn_box)

        # Add layout to screen
        screen.add_widget(layout)
        app.switch_to("game")

        # Bind updates
        Window.bind(on_key_down=self.handle_key)
        self.grid_widget.bind(size=lambda *a: self.update_grid())

    def show_popup(self, message):
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text=message, font_size=20))
        ok_btn = Button(text="OK", size_hint_y=None, height=40)
        popup = Popup(title="Game Over", content=box, size_hint=(0.6, 0.4))
        ok_btn.bind(on_release=lambda x: popup.dismiss())
        ok_btn.bind(on_release=lambda x: self.return_to_menu())
        box.add_widget(ok_btn)
        popup.open()

    def return_to_menu(self):
        from kivy.app import App
        app = App.get_running_app()
        app.switch_to("stats")

    # -----------------------------------------------------------
    # Input
    # -----------------------------------------------------------
    def handle_key(self, instance, key, scancode, codepoint, modifiers):
        if not self.running:
            return
        mapping = {
            273: 'up', 274: 'down', 276: 'left', 275: 'right',  # Arrows
            119: 'up', 115: 'down', 97: 'left', 100: 'right',   # WASD
        }
        if key in mapping:
            new_dir = mapping[key]
            if (self.direction, new_dir) not in [
                ('up', 'down'), ('down', 'up'),
                ('left', 'right'), ('right', 'left')
            ]:
                self.direction = new_dir

    # -----------------------------------------------------------
    # Logic + Drawing
    # -----------------------------------------------------------
    def spawn_food(self):
        while True:
            pos = (random.randint(0, self.GRID_WIDTH - 1),
                   random.randint(0, self.GRID_HEIGHT - 1))
            if pos not in self.snake:
                self.food = pos
                break

    def update(self, dt):
        if not self.running:
            return
        dx, dy = self.DIRECTIONS[self.direction]
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        if (new_head in self.snake or
                not (0 <= new_head[0] < self.GRID_WIDTH) or
                not (0 <= new_head[1] < self.GRID_HEIGHT)):
            self.end_game("You crashed!")
            return

        self.snake.insert(0, new_head)
        if new_head == self.food:
            self.score += 1
            self.turn_label.text = f"Score: {self.score}"
            self.spawn_food()
        else:
            self.snake.pop()

        self.update_grid()

    def update_grid(self):
        """Draw snake and food using images — brighter, more visible playfield."""
        self.grid_widget.canvas.clear()

    # Compute dynamic cell size
        self.cell_size = min(
            self.grid_widget.width / self.GRID_WIDTH,
            self.grid_widget.height / self.GRID_HEIGHT
        )

        grid_px_width = self.GRID_WIDTH * self.cell_size
        grid_px_height = self.GRID_HEIGHT * self.cell_size
        offset_x = (self.grid_widget.width - grid_px_width) / 2
        offset_y = (self.grid_widget.height - grid_px_height) / 2
        base_x, base_y = self.grid_widget.pos

        with self.grid_widget.canvas:
        # ✅ Slightly brighter background (was 0.05, now 0.15)
            Color(0.15, 0.15, 0.15, 1)
            Rectangle(pos=self.grid_widget.pos, size=self.grid_widget.size)

        # ✅ Sharper, lighter walls
            Color(0.6, 0.6, 0.6, 1)
            border = 4
            Rectangle(pos=(base_x + offset_x, base_y + offset_y + grid_px_height - border),
                    size=(grid_px_width, border))  # top
            Rectangle(pos=(base_x + offset_x, base_y + offset_y),
                    size=(grid_px_width, border))  # bottom
            Rectangle(pos=(base_x + offset_x, base_y + offset_y),
                    size=(border, grid_px_height))  # left
            Rectangle(pos=(base_x + offset_x + grid_px_width - border, base_y + offset_y),
                    size=(border, grid_px_height))  # right

        # ✅ Brighter overall image tone
            Color(1, 1, 1, 1)

        # Snake (head + body images)
            for i, (x, y) in enumerate(self.snake):
                img_path = self.head_img if i == 0 else self.body_img
                Rectangle(
                    source=img_path,
                    pos=(base_x + offset_x + x * self.cell_size,
                        base_y + offset_y + y * self.cell_size),
                    size=(self.cell_size, self.cell_size),
                )

        # Food (image)
            Rectangle(
                source=self.food_img,
                pos=(base_x + offset_x + self.food[0] * self.cell_size,
                    base_y + offset_y + self.food[1] * self.cell_size),
                size=(self.cell_size, self.cell_size),
            )
