import os
import logging
from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.graphics import RoundedRectangle, Color, PushMatrix, PopMatrix, Scale
from kivy.animation import Animation
from kivy.properties import BooleanProperty, NumericProperty
from kivy.utils import get_color_from_hex

from core.database import Database
from core.game_manager import GameManager


# ------------------ GLOBAL LOGGING CLEANUP ------------------
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("kivy").setLevel(logging.WARNING)
Window.clearcolor = get_color_from_hex("#10121A")


# =========================== HOVER BEHAVIOR ===========================
class HoverBehavior(object):
    hovered = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)

    def on_mouse_pos(self, *args):
        if not self.get_root_window():
            return
        pos = args[1]
        inside = self.collide_point(*self.to_widget(*pos))
        if self.hovered == inside:
            return
        self.hovered = inside
        if inside:
            self.on_enter()
        else:
            self.on_leave()

    def on_enter(self):
        pass

    def on_leave(self):
        pass


# =========================== HOVER CARD ===========================
class HoverCard(HoverBehavior, BoxLayout):
    scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.radius = [20]
        with self.canvas.before:
            PushMatrix()
            self.scale_transform = Scale(self.scale, self.scale, 1)
            self.bg_color = Color(0.1, 0.1, 0.12, 1)
            self.bg_rect = RoundedRectangle(radius=self.radius, pos=self.pos, size=self.size)
        with self.canvas.after:
            PopMatrix()
        self.bind(pos=self.update_bg, size=self.update_bg, scale=self.update_scale)

    def update_bg(self, *args):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

    def update_scale(self, *args):
        self.scale_transform.x = self.scale
        self.scale_transform.y = self.scale

    def on_enter(self):
        Animation.cancel_all(self.bg_color, self)
        Animation(r=0.2, g=0.4, b=0.9, a=1, d=0.15).start(self.bg_color)
        Animation(scale=1.05, d=0.15).start(self)

    def on_leave(self):
        Animation.cancel_all(self.bg_color, self)
        Animation(r=0.1, g=0.1, b=0.12, a=1, d=0.25).start(self.bg_color)
        Animation(scale=1.0, d=0.25).start(self)


# =========================== SCREENS ===========================
class MenuScreen(Screen):
    pass


class GameScreen(Screen):
    pass


class StatsScreen(Screen):
    pass


# =========================== MAIN APP ===========================
class MiniGameCollectionApp(App):
    def build(self):
        self.db = Database()
        try:
            self.db.clear_previous_session()
        except Exception:
            pass

        self.sm = ScreenManager()
        self.menu_screen = MenuScreen(name="menu")
        self.game_screen = GameScreen(name="game")
        self.stats_screen = StatsScreen(name="stats")

        self.sm.add_widget(self.menu_screen)
        self.sm.add_widget(self.game_screen)
        self.sm.add_widget(self.stats_screen)

        self.game_manager = GameManager(self.db)
        self.build_game_hub()
        self.build_stats_screen()

        # Schedule periodic live refresh
        Clock.schedule_interval(self.refresh_stats_live, 5)

        return self.sm

    def switch_to(self, name):
        if name == "stats":
            self.build_stats_screen()
        self.sm.current = name

    # ------------------- GAME HUB -------------------
    def build_game_hub(self):
        self.menu_screen.clear_widgets()
        root = BoxLayout(orientation="vertical", spacing=20, padding=[40, 30, 40, 30])

        header = BoxLayout(orientation="vertical", size_hint_y=None, height=120)
        header.add_widget(Label(text="[b]Game Hub[/b]", markup=True, font_size=40,
                                halign="center", color=(1, 1, 1, 1)))
        header.add_widget(Label(text="Choose your game and start playing",
                                font_size=18, halign="center", color=(0.8, 0.8, 0.8, 1)))
        root.add_widget(header)

        scroll = ScrollView(size_hint=(1, 1))
        grid = GridLayout(cols=3, spacing=25, padding=15, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        available_games = self.game_manager.get_game_list()
        for game_id in available_games:
            display_name = game_id.replace("_", " ").title()
            desc = f"Play {display_name} now!"
            icon_path = f"games/{game_id}/icon.png"
            if not os.path.exists(icon_path):
                icon_path = "assets/default_icon.png"

            card = HoverCard(orientation="vertical", padding=15, spacing=10, size_hint_y=None, height=320)
            card.add_widget(Image(source=icon_path, allow_stretch=True, keep_ratio=True,
                                  size_hint_y=None, height=160))
            card.add_widget(Label(text=display_name, font_size=22, color=(1, 1, 1, 1),
                                  halign="center", size_hint_y=None, height=30))
            card.add_widget(Label(text=desc, font_size=14, color=(0.8, 0.8, 0.8, 1),
                                  halign="center", size_hint_y=None, height=40))
            btn = Button(
                text="Play Now",
                size_hint=(None, None),
                size=(150, 40),
                pos_hint={"center_x": 0.5},
                background_normal="",
                background_color=(0.2, 0.4, 0.9, 1),
                on_release=lambda x, n=game_id: self.launch_game(n),
            )
            card.add_widget(btn)
            grid.add_widget(card)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        stats_btn = Button(
            text="View Recent Matches",
            size_hint=(None, None),
            size=(280, 50),
            pos_hint={"center_x": 0.5},
            background_normal="",
            background_color=(0.25, 0.45, 1, 1),
            on_release=lambda x: self.switch_to("stats"),
        )
        root.add_widget(stats_btn)
        self.menu_screen.add_widget(root)

    # ------------------- STATS SCREEN -------------------
    def build_stats_screen(self):
        """Builds the stats screen dynamically using MongoDB data."""
        from kivy.uix.anchorlayout import AnchorLayout

        self.stats_screen.clear_widgets()
        root = BoxLayout(orientation="vertical", spacing=20, padding=[40, 30, 40, 30])

    # Header
        title = Label(
            text="[b]Recent Matches[/b]",
            markup=True,
            font_size=38,
            color=(1, 1, 1, 1),
            halign="center"
        )
        root.add_widget(title)

        stats = self.db.get_recent_stats(limit=10)

        if not stats:
            root.add_widget(Label(text="No match data available.",
                                color=(0.7, 0.7, 0.7, 1),
                                font_size=20))
        else:
        # Table with equal column widths and fixed row height
            table = GridLayout(cols=3, spacing=[40, 10], padding=[20, 10],
                            size_hint_y=None, row_default_height=40)
            table.bind(minimum_height=table.setter("height"))

            headers = ["Game", "Result", "Duration"]
            for h in headers:
                table.add_widget(Label(
                    text=f"[b]{h}[/b]",
                    markup=True,
                    font_size=20,
                    color=(0.9, 0.9, 0.9, 1),
                    size_hint_x=None,
                    width=200,
                    halign="center",
                    valign="middle"
                ))

        # Add recent records neatly
            for record in stats:
                game = record.get("game_name", "-")
                result = record.get("result", "-")
                duration = record.get("duration", "-")

                for text in [game, result, duration]:
                    lbl = Label(
                        text=str(text),
                        color=(1, 1, 1, 1),
                        font_size=16,
                        size_hint_x=None,
                        width=200,
                        halign="center",
                        valign="middle"
                    )
                    lbl.bind(size=lambda l, _: setattr(l, 'text_size', l.size))
                    table.add_widget(lbl)

            scroll = ScrollView(size_hint=(1, 1))
            scroll.add_widget(table)
            root.add_widget(scroll)

    # Back button centered cleanly
        back_container = AnchorLayout(anchor_y="bottom", size_hint_y=None, height=80)
        back_btn = Button(
            text="Back to Menu",
            size_hint=(None, None),
            size=(220, 50),
            background_normal="",
            background_color=(0.3, 0.5, 0.9, 1),
            on_release=lambda x: self.switch_to("menu"),
        )
        back_container.add_widget(back_btn)
        root.add_widget(back_container)

        self.stats_screen.add_widget(root)

    # ------------------- AUTO REFRESH -------------------
    def refresh_stats_live(self, dt):
        if self.sm.current == "stats":
            self.build_stats_screen()

    # ------------------- GAME LAUNCH -------------------
    def launch_game(self, game_name):
        try:
            key = game_name.lower().replace(" ", "_")
            game = self.game_manager.launch_game(key)
            game.start()
        except Exception as e:
            print(f"[ERROR] Failed to launch {game_name}: {e}")


if __name__ == "__main__":
    MiniGameCollectionApp().run()
