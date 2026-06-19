from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window
from kivy.uix.popup import Popup
import random


class SnakeGame(BaseGame):

    GRID_WIDTH = 40
    GRID_HEIGHT = 40
    MOVE_INTERVAL = 0.1

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
        self.score_label = None
        self.clock_event = None
        self.cell_size = 20

    def start(self , app):
        from kivy.app import App
        self.app = App.get_running_app()

        self.begin_session()
        self.build_ui()
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

    def build_ui(self):
        screen = self.app.game_screen
        screen.clear_widgets()

        layout = BoxLayout(orientation="vertical", spacing=8, padding=5)

        self.score_label = Label(text="Score: 0", font_size=22, size_hint_y=None, height=40)
        layout.add_widget(self.score_label)

        self.grid_widget = Widget()
        layout.add_widget(self.grid_widget)

        btn_box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_box.add_widget(Button(text="Restart", on_release=lambda *_: self.reset()))
        btn_box.add_widget(Button(text="Back to Menu", on_release=lambda *_: self.app.switch_to("menu")))
        layout.add_widget(btn_box)

        screen.add_widget(layout)
        self.app.switch_to("game")

        Window.bind(on_key_down=self.handle_key)
        self.grid_widget.bind(size=lambda *_: self.update_grid())

    def spawn_food(self):
        while True:
            pos = (random.randint(0, self.GRID_WIDTH - 1),
                   random.randint(0, self.GRID_HEIGHT - 1))
            if pos not in self.snake:
                self.food = pos
                break

    def handle_key(self, instance, key, *_):
        if not self.running:
            return

        mapping = {
            273: 'up', 274: 'down',
            276: 'left', 275: 'right',
            119: 'up', 115: 'down',
            97: 'left', 100: 'right'
        }

        if key in mapping:
            new_dir = mapping[key]
            opposite = {
                ('up', 'down'), ('down', 'up'),
                ('left', 'right'), ('right', 'left')
            }
            if (self.direction, new_dir) not in opposite:
                self.direction = new_dir

    def update(self, dt):
        if not self.running:
            return

        dx, dy = self.DIRECTIONS[self.direction]
        head_x, head_y = self.snake[0]
        new_head = (head_x + dx, head_y + dy)

        if (new_head in self.snake or
                not (0 <= new_head[0] < self.GRID_WIDTH) or
                not (0 <= new_head[1] < self.GRID_HEIGHT)):
            self.game_over()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 1
            self.score_label.text = f"Score: {self.score}"
            self.spawn_food()
        else:
            self.snake.pop()

        self.update_grid()

    def game_over(self):
        self.running = False

        if self.clock_event:
            self.clock_event.cancel()

        layout = BoxLayout(
            orientation="vertical",
            spacing=20,
            padding=20
        )

        layout.add_widget(Label(
            text=f"Game Over\nScore: {self.score}",
            font_size=24
        ))

        btn_row = BoxLayout(
            size_hint_y=None,
            height=50,
            spacing=10
        )

        restart_btn = Button(text="Restart")
        restart_btn.bind(on_release=lambda *_: self.restart_game())

        menu_btn = Button(text="Menu")
        menu_btn.bind(on_release=lambda *_: self.back_to_menu())

        btn_row.add_widget(restart_btn)
        btn_row.add_widget(menu_btn)

        layout.add_widget(btn_row)

        self.popup = Popup(
            title="Snake",
            content=layout,
            size_hint=(0.4, 0.4),
            auto_dismiss=False
        )

        self.popup.open()


    def update_grid(self):
        self.grid_widget.canvas.clear()
        self.cell_size = min(
            self.grid_widget.width / self.GRID_WIDTH,
            self.grid_widget.height / self.GRID_HEIGHT
        )

        with self.grid_widget.canvas:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=self.grid_widget.pos, size=self.grid_widget.size)

            Color(0, 1, 0, 1)
            for x, y in self.snake:
                Rectangle(
                    pos=(self.grid_widget.x + x * self.cell_size,
                         self.grid_widget.y + y * self.cell_size),
                    size=(self.cell_size, self.cell_size)
                )

            Color(1, 0, 0, 1)
            Rectangle(
                pos=(self.grid_widget.x + self.food[0] * self.cell_size,
                     self.grid_widget.y + self.food[1] * self.cell_size),
                size=(self.cell_size, self.cell_size)
            )
