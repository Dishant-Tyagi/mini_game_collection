# =====================================
# Pong Game — Clean Stable Version
# =====================================
from core.base_game import BaseGame
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color
from kivy.uix.popup import Popup


class PongGame(BaseGame):

    BALL_SPEED = 300
    PADDLE_SPEED = 600

    def __init__(self, db):
        super().__init__(db, "Pong")

        self.ball = None
        self.left_paddle = None
        self.right_paddle = None

        self.ball_vx = self.BALL_SPEED
        self.ball_vy = self.BALL_SPEED

        self.left_score = 0
        self.right_score = 0

        self.running = False
        self.clock_ev = None

        self.play_area = None
        self.score_lbl = None

        # smooth paddle control states
        self.left_up = False
        self.left_down = False
        self.right_up = False
        self.right_down = False

    # --------------------------------------------------
    def start(self, app):
        from kivy.app import App
        self.app = App.get_running_app()

        self.begin_session()
        self.build_ui()
        self.reset()

    # --------------------------------------------------
    def build_ui(self):
        screen = self.app.game_screen
        screen.clear_widgets()

        root = BoxLayout(orientation="vertical", spacing=6, padding=6)

        self.score_lbl = Label(
            text="0  :  0",
            font_size=30,
            size_hint_y=None,
            height=50
        )
        root.add_widget(self.score_lbl)

        self.play_area = Widget()
        root.add_widget(self.play_area)

        btns = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btns.add_widget(Button(text="Restart", on_release=lambda *_: self.reset()))
        btns.add_widget(Button(text="Back to Menu", on_release=lambda *_: self.app.switch_to("menu")))
        root.add_widget(btns)

        screen.add_widget(root)
        self.app.switch_to("game")

        self.create_objects()

        from kivy.core.window import Window
        Window.bind(on_key_down=self.on_key)
        Window.bind(on_key_up=self.on_key_up)

        self.play_area.bind(size=lambda *_: self.center_objects())

    # --------------------------------------------------
    def create_objects(self):
        self.play_area.canvas.clear()
        with self.play_area.canvas:
            Color(1, 1, 1, 1)
            self.left_paddle = Rectangle(size=(15, 100))
            self.right_paddle = Rectangle(size=(15, 100))
            self.ball = Rectangle(size=(16, 16))

    def center_objects(self):
        if not self.play_area:
            return

        w, h = self.play_area.size
        x, y = self.play_area.pos

        self.left_paddle.pos = (x + 20, y + h / 2 - 50)
        self.right_paddle.pos = (x + w - 35, y + h / 2 - 50)
        self.ball.pos = (x + w / 2 - 8, y + h / 2 - 8)

    # --------------------------------------------------
    def reset(self):
        self.left_score = 0
        self.right_score = 0
        self.score_lbl.text = "0  :  0"

        self.center_objects()

        self.ball_vx = self.BALL_SPEED
        self.ball_vy = self.BALL_SPEED

        self.running = True

        if self.clock_ev:
            self.clock_ev.cancel()

        self.clock_ev = Clock.schedule_interval(self.update, 1 / 60)

    # --------------------------------------------------
    def on_key(self, _, key, *__):
        if key == 119:
            self.left_up = True
        elif key == 115:
            self.left_down = True
        elif key == 273:
            self.right_up = True
        elif key == 274:
            self.right_down = True

    def on_key_up(self, _, key, *__):
        if key == 119:
            self.left_up = False
        elif key == 115:
            self.left_down = False
        elif key == 273:
            self.right_up = False
        elif key == 274:
            self.right_down = False

    def move_paddle(self, paddle, dy):
        x, y = paddle.pos
        y += dy

        min_y = self.play_area.y
        max_y = self.play_area.top - paddle.size[1]

        paddle.pos = (x, max(min_y, min(y, max_y)))

    # --------------------------------------------------
    def update(self, dt):
        if not self.running:
            return

        # smooth paddle movement
        if self.left_up:
            self.move_paddle(self.left_paddle, self.PADDLE_SPEED * dt)

        if self.left_down:
            self.move_paddle(self.left_paddle, -self.PADDLE_SPEED * dt)

        if self.right_up:
            self.move_paddle(self.right_paddle, self.PADDLE_SPEED * dt)

        if self.right_down:
            self.move_paddle(self.right_paddle, -self.PADDLE_SPEED * dt)

        bx, by = self.ball.pos
        bw, bh = self.ball.size

        bx += self.ball_vx * dt
        by += self.ball_vy * dt

        # Wall collision
        if by <= self.play_area.y:
            by = self.play_area.y
            self.ball_vy *= -1

        elif by + bh >= self.play_area.top:
            by = self.play_area.top - bh
            self.ball_vy *= -1

        # Paddle collision
        if self.check_collision(self.left_paddle) and self.ball_vx < 0:
            bx = self.left_paddle.pos[0] + self.left_paddle.size[0]
            self.ball_vx *= -1

        elif self.check_collision(self.right_paddle) and self.ball_vx > 0:
            bx = self.right_paddle.pos[0] - bw
            self.ball_vx *= -1

        # Score
        if bx + bw < self.play_area.x:
            self.right_score += 1
            self.update_score()
            self.center_objects()
            return

        if bx > self.play_area.right:
            self.left_score += 1
            self.update_score()
            self.center_objects()
            return

        self.ball.pos = (bx, by)

    def check_collision(self, paddle):
        bx, by = self.ball.pos
        px, py = paddle.pos
        bw, bh = self.ball.size
        pw, ph = paddle.size

        return (
            bx < px + pw and
            bx + bw > px and
            by < py + ph and
            by + bh > py
        )

    # --------------------------------------------------
    def update_score(self):
        self.score_lbl.text = f"{self.left_score}  :  {self.right_score}"

        if self.left_score == 5 or self.right_score == 5:
            winner = "Left Player" if self.left_score > self.right_score else "Right Player"
            self.game_over(winner)

    def game_over(self, winner):
        self.running = False

        if self.clock_ev:
            self.clock_ev.cancel()

        # Delegate to app (central handler)
        from kivy.app import App
        app = App.get_running_app()

        if app and hasattr(app, "handle_game_over"):
            app.handle_game_over(self, winner)