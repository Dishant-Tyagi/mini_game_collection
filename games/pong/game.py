# games/pong/game.py
from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.core.window import Window
from kivy.uix.popup import Popup
import time


class PongGame(BaseGame):
    GAME_NAME = "Pong"
    WIN_SCORE = 5
    PADDLE_WIDTH_RATIO = 0.02
    PADDLE_HEIGHT_RATIO = 0.18
    BALL_SIZE_RATIO = 0.02

    PADDLE_SPEED = 450.0
    AI_MAX_SPEED = 380.0
    BALL_BASE_SPEED = 320.0
    BALL_ACCEL_ON_HIT = 1.07
    BALL_MAX_SPEED = 1200.0

    def __init__(self, db):
        super().__init__(db, self.GAME_NAME)
        self.left_score = 0
        self.right_score = 0
        self.running = False
        self.start_time = None
        self.layout = None
        self.play_area = None
        self.score_label = None
        self.btn_box = None
        self.paddle_w = 0
        self.paddle_h = 0
        self.ball_size = 0
        self.left_y = 0.0
        self.right_y = 0.0
        self.ball_x = 0.0
        self.ball_y = 0.0
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self._clock_ev = None

    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def reset(self):
        self.left_score = 0
        self.right_score = 0
        self.running = True
        self.start_time = time.time()
        self._setup_initial_positions()
        self.update_canvas()
        if self._clock_ev:
            self._clock_ev.cancel()
        self._clock_ev = Clock.schedule_interval(self.update, 1 / 60.0)

    def get_score(self):
        return f"{self.left_score}-{self.right_score}"

    def end_game(self, winner_text=""):
        self.running = False
        if self._clock_ev:
            self._clock_ev.cancel()
            self._clock_ev = None
        duration_seconds = int(time.time() - (self.start_time or time.time()))
        duration = f"{duration_seconds // 60:02d}:{duration_seconds % 60:02d}"
        result = "Win" if winner_text == "You" else "Loss" if winner_text == "AI" else winner_text
        try:
            if hasattr(self.db, "record_match"):
                self.db.record_match(self.game_name, result, duration)
            else:
                self.db.insert_game_stat(self.game_name, result, duration)
        except Exception:
            pass
        self._show_end_popup(winner_text, duration)

    def build_ui(self, app):
        screen = app.game_screen
        screen.clear_widgets()
        self.layout = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.score_label = Label(text="0 - 0", font_size=28, size_hint_y=None, height=44)
        self.layout.add_widget(self.score_label)
        self.play_area = Widget()
        self.layout.add_widget(self.play_area)
        self.btn_box = BoxLayout(size_hint_y=None, height=48, spacing=10, padding=[10, 6])
        self.btn_box.add_widget(Button(text="Restart", on_release=lambda x: self.reset()))
        self.btn_box.add_widget(Button(text="Back to Menu", on_release=lambda x: app.switch_to("menu")))
        self.layout.add_widget(self.btn_box)
        screen.add_widget(self.layout)
        app.switch_to("game")
        Window.bind(on_key_down=self._on_key_down)
        Window.bind(on_key_up=self._on_key_up)
        self.play_area.bind(size=lambda *a: self._on_resize())
        self._keys_pressed = set()

    def _show_end_popup(self, winner_text, duration):
        from kivy.app import App
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        title = f"{winner_text} won!" if winner_text else "Match ended"
        box.add_widget(Label(text=f"{title}\nDuration: {duration}\nScore: {self.left_score} - {self.right_score}", halign="center"))
        btns = BoxLayout(size_hint_y=None, height=40, spacing=10)
        r = Button(text="Restart")
        r.bind(on_release=lambda *_: (popup.dismiss(), self.reset()))
        m = Button(text="Menu")
        m.bind(on_release=lambda *_: (popup.dismiss(), app.switch_to("menu")))
        btns.add_widget(r)
        btns.add_widget(m)
        box.add_widget(btns)
        popup = Popup(title="Match Over", content=box, size_hint=(0.5, 0.4))
        popup.open()

    def _on_key_down(self, instance, key, scancode, codepoint, modifiers):
        self._keys_pressed.add(key)

    def _on_key_up(self, instance, key, scancode):
        if key in self._keys_pressed:
            self._keys_pressed.remove(key)

    def _on_resize(self):
        self._setup_initial_positions()
        self.update_canvas()

    def _setup_initial_positions(self):
        import random, math
        w, h = self.play_area.width or Window.width, self.play_area.height or (Window.height - 100)
        self.paddle_w = max(8, int(w * self.PADDLE_WIDTH_RATIO))
        self.paddle_h = max(40, int(h * self.PADDLE_HEIGHT_RATIO))
        self.ball_size = max(8, int(min(w, h) * self.BALL_SIZE_RATIO))
        center_y = h / 2.0
        self.left_x = int(w * 0.02)
        self.right_x = int(w * (1 - 0.02) - self.paddle_w)
        self.left_y = center_y - self.paddle_h / 2
        self.right_y = center_y - self.paddle_h / 2
        self.ball_x = w / 2 - self.ball_size / 2
        self.ball_y = center_y - self.ball_size / 2
        angle = random.choice([30, -30, 150, -150])
        rad = math.radians(angle)
        speed = self.BALL_BASE_SPEED
        self.ball_vx = speed * math.cos(rad)
        self.ball_vy = speed * math.sin(rad)

    def update(self, dt):
        if not self.running:
            return
        move = 0.0
        if 119 in self._keys_pressed or 273 in self._keys_pressed:
            move -= 1
        if 115 in self._keys_pressed or 274 in self._keys_pressed:
            move += 1
        self.left_y += move * self.PADDLE_SPEED * dt
        w, h = self.play_area.width or Window.width, self.play_area.height or (Window.height - 100)
        self.left_y = max(0, min(h - self.paddle_h, self.left_y))
        target = self.ball_y + self.ball_size / 2 - self.paddle_h / 2
        delta = target - self.right_y
        max_move = self.AI_MAX_SPEED * dt
        if abs(delta) > max_move:
            delta = max_move if delta > 0 else -max_move
        self.right_y = max(0, min(h - self.paddle_h, self.right_y + delta))
        self.ball_x += self.ball_vx * dt
        self.ball_y += self.ball_vy * dt
        if self.ball_y <= 0:
            self.ball_y = 0
            self.ball_vy = abs(self.ball_vy)
        if self.ball_y + self.ball_size >= h:
            self.ball_y = h - self.ball_size
            self.ball_vy = -abs(self.ball_vy)
        if (self.ball_x <= self.left_x + self.paddle_w and
                self.ball_x + self.ball_size >= self.left_x and
                self.ball_y + self.ball_size >= self.left_y and
                self.ball_y <= self.left_y + self.paddle_h and
                self.ball_vx < 0):
            self._reflect_from_paddle(left=True)
        if (self.ball_x + self.ball_size >= self.right_x and
                self.ball_x <= self.right_x + self.paddle_w and
                self.ball_y + self.ball_size >= self.right_y and
                self.ball_y <= self.right_y + self.paddle_h and
                self.ball_vx > 0):
            self._reflect_from_paddle(left=False)
        if self.ball_x + self.ball_size < 0:
            self.right_score += 1
            self._on_score()
            if self._check_end():
                return
            self._serve(direction=1)
        elif self.ball_x > w:
            self.left_score += 1
            self._on_score()
            if self._check_end():
                return
            self._serve(direction=-1)
        self.update_canvas()

    def _reflect_from_paddle(self, left=True):
        import math
        rel = (self.ball_y + self.ball_size / 2) - ((self.left_y if left else self.right_y) + self.paddle_h / 2)
        norm = rel / (self.paddle_h / 2)
        angle = norm * 60
        rad = math.radians(angle)
        speed = min(self.BALL_MAX_SPEED, (abs(self.ball_vx)**2 + abs(self.ball_vy)**2)**0.5 * self.BALL_ACCEL_ON_HIT)
        self.ball_vx = abs(speed * math.cos(rad)) * (1 if left else -1)
        self.ball_vy = speed * math.sin(rad)
        self.ball_x += (1 if left else -1) * (self.paddle_w + 1)

    def _serve(self, direction=1):
        import math, random
        w, h = self.play_area.width or Window.width, self.play_area.height or (Window.height - 100)
        self.ball_x = w / 2 - self.ball_size / 2
        self.ball_y = h / 2 - self.ball_size / 2
        angle = random.uniform(-30, 30)
        rad = math.radians(angle)
        speed = self.BALL_BASE_SPEED
        self.ball_vx = direction * speed * math.cos(rad)
        self.ball_vy = speed * math.sin(rad)

    def _on_score(self):
        self.score_label.text = f"{self.left_score} - {self.right_score}"

    def _check_end(self):
        if self.left_score >= self.WIN_SCORE:
            self.end_game("You")
            return True
        if self.right_score >= self.WIN_SCORE:
            self.end_game("AI")
            return True
        return False

    def update_canvas(self):
        self.play_area.canvas.clear()
        with self.play_area.canvas:
            Color(0.06, 0.06, 0.06, 1)
            Rectangle(pos=self.play_area.pos, size=self.play_area.size)
            base_x, base_y = self.play_area.pos
            w, h = self.play_area.size
            Color(0.35, 0.35, 0.35, 1)
            dash_h = max(6, int(h * 0.03))
            gap = dash_h
            cx = base_x + w / 2 - 2
            y = base_y + 10
            while y < base_y + h - 10:
                Rectangle(pos=(cx, y), size=(4, dash_h))
                y += dash_h + gap
            Color(0.9, 0.9, 0.9, 1)
            Rectangle(pos=(base_x + self.left_x, base_y + self.left_y), size=(self.paddle_w, self.paddle_h))
            Rectangle(pos=(base_x + self.right_x, base_y + self.right_y), size=(self.paddle_w, self.paddle_h))
            Color(1, 0.6, 0.0, 1)
            Ellipse(pos=(base_x + self.ball_x, base_y + self.ball_y), size=(self.ball_size, self.ball_size))
