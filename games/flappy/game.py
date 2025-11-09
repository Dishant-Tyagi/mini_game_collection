# games/flappy/game.py
from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.graphics import Rectangle
from kivy.core.image import Image as CoreImage
from kivy.core.window import Window
from kivy.uix.popup import Popup
from random import randint
import time


class FlappyGame(BaseGame):
    GAME_NAME = "Flappy Bird"

    def __init__(self, db):
        super().__init__(db, self.GAME_NAME)
        self.play_area = None
        self.layout = None
        self.score_label = None
        self.bg_img = None
        self.pipe_img = None
        self.bird_img = None
        self.pipes = []

        # physics
        self.gravity = -850.0
        self.jump_velocity = 320.0
        self.bird_y = 0.0
        self.bird_vy = 0.0

        # pipes
        self.pipe_speed = 200.0
        self.pipe_gap = 180
        self.pipe_width = 80
        self.pipe_spawn_timer = 0.0
        self.pipe_interval = 1.5

        # score
        self.score = 0
        self.running = False
        self.start_time = None
        self._clock_ev = None

        # assets
        self.asset_path = "games/flappy/assets/"
        self.bg_img = CoreImage(self.asset_path + "background.png").texture
        self.pipe_img = CoreImage(self.asset_path + "pipe.png").texture
        self.bird_img = CoreImage(self.asset_path + "bird.png").texture

    # ------------------------------------------------------
    def start(self):
        from kivy.app import App
        app = App.get_running_app()
        self.begin_session()
        self.build_ui(app)
        self.reset()

    def build_ui(self, app):
        screen = app.game_screen
        screen.clear_widgets()

        # Main vertical layout — no padding, no spacing
        self.layout = BoxLayout(orientation="vertical", spacing=0, padding=0)

        # Score label
        self.score_label = Label(
            text="Score: 0",
            font_size=28,
            size_hint_y=None,
            height=50
        )
        self.layout.add_widget(self.score_label)

        # Play area — takes 85% of height
        self.play_area = Widget(size_hint_y=0.85)
        self.layout.add_widget(self.play_area)

        # Bottom button bar
        btns = BoxLayout(size_hint_y=0.15, height=60, spacing=10, padding=[10, 6])
        btns.add_widget(Button(text="Restart", on_release=lambda x: self.reset()))
        btns.add_widget(Button(text="Back to Menu", on_release=lambda x: app.switch_to("menu")))
        self.layout.add_widget(btns)

        screen.add_widget(self.layout)
        app.switch_to("game")

        Window.bind(on_key_down=self._on_key_down)
        self.play_area.bind(size=lambda *a: self._on_resize())

    # ------------------------------------------------------
    def reset(self):
        self.score = 0
        self.bird_vy = 0
        self.bird_y = self.play_area.height / 2 if self.play_area.height else 300
        self.pipes.clear()
        self.pipe_spawn_timer = 0.0
        self.running = True
        self.start_time = time.time()

        if self._clock_ev:
            self._clock_ev.cancel()
        self._clock_ev = Clock.schedule_interval(self.update, 1 / 60.0)
        self.update_canvas()

    def _on_key_down(self, instance, key, scancode, codepoint, modifiers):
        if key == 32 and self.running:  # Space key
            self.bird_vy = self.jump_velocity

    def _on_resize(self):
        self.update_canvas()

    # ------------------------------------------------------
    def update(self, dt):
        if not self.running:
            return

        # Update physics
        self.bird_vy += self.gravity * dt
        self.bird_y += self.bird_vy * dt

        # Spawn new pipes
        self.pipe_spawn_timer += dt
        if self.pipe_spawn_timer >= self.pipe_interval:
            self.pipe_spawn_timer = 0
            self._spawn_pipe()

        # Move pipes
        for p in self.pipes:
            p["x"] -= self.pipe_speed * dt
        self.pipes = [p for p in self.pipes if p["x"] + self.pipe_width > 0]

        # Check collisions & scoring
        self._check_collisions()
        self.update_canvas()

    def _spawn_pipe(self):
        h = self.play_area.height or 600
        gap_y = randint(int(h * 0.3), int(h * 0.7))
        self.pipes.append({
            "x": self.play_area.width,
            "gap_y": gap_y,
            "passed": False
        })

    def _check_collisions(self):
        h = self.play_area.height or 600
        w = self.play_area.width or 800
        bird_size = 40
        bx = w * 0.25
        by = self.bird_y
        COLLISION_OFFSET = 12  # reduced hitbox padding

        # Ground / ceiling
        if by < 0 or by + bird_size > h:
            self._game_over()
            return

        for p in self.pipes:
            px = p["x"]
            gap_y = p["gap_y"]

            # Collision detection
            if bx + bird_size - COLLISION_OFFSET > px and bx + COLLISION_OFFSET < px + self.pipe_width:
                if by + COLLISION_OFFSET < gap_y - self.pipe_gap / 2 or by + bird_size - COLLISION_OFFSET > gap_y + self.pipe_gap / 2:
                    self._game_over()
                    return

            # Scoring
            if not p["passed"] and px + self.pipe_width < bx:
                p["passed"] = True
                self.score += 1
                self.score_label.text = f"Score: {self.score}"

    def _game_over(self):
        self.running = False
        if self._clock_ev:
            self._clock_ev.cancel()
            self._clock_ev = None

        duration_seconds = int(time.time() - (self.start_time or time.time()))
        duration = f"{duration_seconds // 60:02d}:{duration_seconds % 60:02d}"

        try:
            if hasattr(self.db, "record_match"):
                self.db.record_match(self.game_name, self.score, duration)
            else:
                self.db.insert_game_stat(self.game_name, self.score, duration)
        except Exception:
            pass

        self._show_game_over()

    def _show_game_over(self):
        from kivy.app import App
        app = App.get_running_app()
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text=f"Game Over!\nScore: {self.score}", halign="center"))
        btns = BoxLayout(size_hint_y=None, height=40, spacing=10)
        r = Button(text="Restart")
        r.bind(on_release=lambda *_: (popup.dismiss(), self.reset()))
        m = Button(text="Menu")
        m.bind(on_release=lambda *_: (popup.dismiss(), app.switch_to("menu")))
        btns.add_widget(r)
        btns.add_widget(m)
        box.add_widget(btns)
        popup = Popup(title="Flappy Bird", content=box, size_hint=(0.5, 0.4))
        popup.open()

    # ------------------------------------------------------
    def update_canvas(self):
        self.play_area.canvas.clear()
        with self.play_area.canvas:
        # Background — fill only the play area (not the buttons below)
            Rectangle(
                texture=self.bg_img,
                pos=self.play_area.pos,
                size=self.play_area.size
            )

        # Draw pipes
            for p in self.pipes:
                px = p["x"]
                gap_y = p["gap_y"]

            # Top pipe
                Rectangle(
                    texture=self.pipe_img,
                    pos=(px, self.play_area.y + gap_y + self.pipe_gap / 2),
                    size=(self.pipe_width, self.play_area.height - (gap_y + self.pipe_gap / 2))
                )

            # Bottom pipe
                Rectangle(
                    texture=self.pipe_img,
                    pos=(px, self.play_area.y),
                    size=(self.pipe_width, gap_y - self.pipe_gap / 2)
                )

        # Bird
            bird_x = self.play_area.width * 0.25
            Rectangle(
                texture=self.bird_img,
                pos=(bird_x, self.play_area.y + self.bird_y),
                size=(40, 40)
            )
