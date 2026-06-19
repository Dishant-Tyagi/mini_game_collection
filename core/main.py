# =====================================
# core/main.py — PyInstaller Safe
# =====================================

import os

import sys
import logging
from core.game_state_manager import GameStateManager
from core.multiplayer.multiplayer_manager import MultiplayerManager
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
from core.game_manager import GameManager, resource_path
from games.chess import game


# ------------------ LOGGING CLEANUP ------------------
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
        self.on_enter() if inside else self.on_leave()

    def on_enter(self): pass
    def on_leave(self): pass


# =========================== HOVER CARD ===========================
class HoverCard(HoverBehavior, BoxLayout):
    scale = NumericProperty(1.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            PushMatrix()
            self.scale_t = Scale(1, 1, 1)
            self.bg = Color(0.1, 0.1, 0.12, 1)
            self.rect = RoundedRectangle(radius=[20], pos=self.pos, size=self.size)
        with self.canvas.after:
            PopMatrix()

        self.bind(pos=self._update, size=self._update)

    def _update(self, *_):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_enter(self):
        Animation(scale=1.05, d=0.15).start(self)
        Animation(r=0.2, g=0.4, b=0.9, d=0.15).start(self.bg)

    def on_leave(self):
        Animation(scale=1.0, d=0.2).start(self)
        Animation(r=0.1, g=0.1, b=0.12, d=0.2).start(self.bg)


# =========================== SCREENS ===========================
class MenuScreen(Screen): pass
class GameScreen(Screen): pass
class StatsScreen(Screen): pass


# =========================== MAIN APP ===========================
class MiniGameCollectionApp(App):
    def start_host(self):
        print("[MP] Starting Server...")
        self.multiplayer_enabled = True
        self.multiplayer_manager.host_game(port=5000)

    def start_client(self):
        print("[MP] Connecting to Server...")
        self.multiplayer_enabled = True
        self.multiplayer_manager.join_game("127.0.0.1", port=5000)

    def pause_game(self):
        game = self.state_manager.get_active_game()
        if not game:
            return

        self.state_manager.set_state("PAUSED")

    # Stop clock safely
        if hasattr(game, "clock_event") and game.clock_event:
            game.clock_event.cancel()

        if hasattr(game, "clock_ev") and game.clock_ev:
            game.clock_ev.cancel()

    # Show pause overlay
        from kivy.uix.popup import Popup
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.uix.button import Button

        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="Game Paused"))

        resume_btn = Button(text="Resume")
        resume_btn.bind(on_release=lambda *_: self._close_pause())

        menu_btn = Button(text="Menu")
        menu_btn.bind(on_release=lambda *_: self._pause_to_menu())

        box.add_widget(resume_btn)
        box.add_widget(menu_btn)

        self._pause_popup = Popup(title="Paused",
                                content=box,
                                size_hint=(0.5, 0.4),
                                auto_dismiss=False)
        self._pause_popup.open()
    
    def _close_pause(self):
        if hasattr(self, "_pause_popup"):
            self._pause_popup.dismiss()
        self.resume_game()
    
    def resume_game(self):
        game = self.state_manager.get_active_game()
        if not game:
            return

        self.state_manager.set_state("PLAYING")

    # Resume clock
        from kivy.clock import Clock

        if hasattr(game, "update"):
            if hasattr(game, "MOVE_INTERVAL"):
                game.clock_event = Clock.schedule_interval(
                    game.update, game.MOVE_INTERVAL
                )
            else:
                game.clock_ev = Clock.schedule_interval(
                    game.update, 1 / 60
                )

    def _pause_to_menu(self):
        if hasattr(self, "_pause_popup"):
            self._pause_popup.dismiss()

        self.state_manager.set_state("MENU")
        self.state_manager.clear_active_game()
        self.sm.current = "menu"


    
    def _global_key_handler(self, instance, key, *args):
    # ESC key
        if key == 27:
            if self.state_manager.get_state() == "PLAYING":
                self.pause_game()
            elif self.state_manager.get_state() == "PAUSED":
                self.resume_game()
    
    def _override_escape(self, window, key, scancode, codepoint, modifiers):
    # 27 = ESC
        if key == 27:
        # If playing → pause
            if self.state_manager.get_state() == "PLAYING":
                self.pause_game()
        # If paused → resume
            elif self.state_manager.get_state() == "PAUSED":
                self.resume_game()
        # If in menu → allow exit
            elif self.state_manager.get_state() == "MENU":
                return False  # allow app to close

            return True  # VERY IMPORTANT → prevents app from closing

        return False


    
    def handle_game_over(self, game, result=None):
        duration = game.end_session()

        print("DEBUG → Saving Match")
        print("Game:", game.game_name)
        print("Duration:", duration)

        try:
            if game.db:
                game.db.record_match(
                    game.game_name,
                    result,   # ← direct result only
                    duration
                )
                print("DEBUG → Saved successfully")
        except Exception as e:
            print("[DB ERROR]", e)

        self.state_manager.set_state("MENU")
        self.state_manager.clear_active_game()
        self.sm.current = "menu"




    def build(self):
        

        from core.multiplayer.multiplayer_manager import MultiplayerManager

        self.multiplayer_manager = MultiplayerManager(self)
        self.multiplayer_enabled = False  # default


        self.db = Database()
        try:
            self.db.clear_previous_session()
        except Exception:
            pass
        
        self.state_manager = GameStateManager()
        self.sm = ScreenManager()
        self.menu_screen = MenuScreen(name="menu")
        self.game_screen = GameScreen(name="game")
        self.stats_screen = StatsScreen(name="stats")
        Window.bind(on_keyboard=self._override_escape)


        self.sm.add_widget(self.menu_screen)
        self.sm.add_widget(self.game_screen)
        self.sm.add_widget(self.stats_screen)

        
        self.game_manager = GameManager(self.db)

        self.build_game_hub()
        self.build_stats_screen()
        
        Clock.schedule_interval(self.refresh_stats_live, 5)
        return self.sm

    # --------------------------------------------------
    def switch_to(self, name):
        if name == "stats":
            self.build_stats_screen()

        if name == "menu":
            self.state_manager.set_state("MENU")
            self.state_manager.clear_active_game()

        self.sm.current = name



    # --------------------------------------------------
    def build_game_hub(self):
        self.menu_screen.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=40, spacing=20)

        root.add_widget(Label(
            text="[b]Game Hub[/b]",
            markup=True,
            font_size=40,
            size_hint_y=None,
            height=80
        ))

        scroll = ScrollView()
        grid = GridLayout(cols=3, spacing=25, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))

        for game in self.game_manager.get_game_list():
            icon = resource_path(f"games/{game}/icon.png")
            if not os.path.exists(icon):
                icon = resource_path("assets/default_icon.png")

            card = HoverCard(orientation="vertical", size_hint_y=None, height=320, padding=15, spacing=10)
            card.add_widget(Image(source=icon, size_hint_y=None, height=160))
            card.add_widget(Label(text=game.replace("_", " ").title(), font_size=22))
            card.add_widget(Button(
                text="Play Now",
                size_hint=(None, None),
                size=(150, 40),
                pos_hint={"center_x": 0.5},
                on_release=lambda x, g=game: self.launch_game(g)
            ))
            grid.add_widget(card)

        scroll.add_widget(grid)
        root.add_widget(scroll)

        root.add_widget(Button(
            text="View Stats",
            size_hint=(None, None),
            size=(220, 50),
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self.switch_to("stats")
        ))

        self.menu_screen.add_widget(root)

        host_btn = Button(
            text="Host Multiplayer",
            size_hint=(1, None),
            height=50
            )
        host_btn.bind(on_release=lambda *_: self.start_host())
        root.add_widget(host_btn)

        join_btn = Button(
            text="Join Multiplayer",
            size_hint=(1, None),
            height=50
            )
        join_btn.bind(on_release=lambda *_: self.start_client())
        root.add_widget(join_btn)

    # --------------------------------------------------
    def build_stats_screen(self):
        self.stats_screen.clear_widgets()
        root = BoxLayout(orientation="vertical", padding=40, spacing=20)

        root.add_widget(Label(
            text="[b]Recent Matches[/b]",
            markup=True,
            font_size=36
        ))

        stats = self.db.get_recent_stats(10)
        if not stats:
            root.add_widget(Label(text="No data available"))
        else:
            for s in stats:
                root.add_widget(Label(
                    text=f"{s['game_name']} | {s['result']} | {s['duration']}",
                    font_size=18
                ))

        root.add_widget(Button(
            text="Back",
            size_hint=(None, None),
            size=(200, 50),
            pos_hint={"center_x": 0.5},
            on_release=lambda x: self.switch_to("menu")
        ))

        self.stats_screen.add_widget(root)

    # --------------------------------------------------
    def refresh_stats_live(self, dt):
        if self.sm.current == "stats":
            self.build_stats_screen()

    # --------------------------------------------------
    def launch_game(self, game_name):
        try:
            key = game_name.lower().replace(" ", "_")

        # 1️⃣ Create game FIRST
            game = self.game_manager.launch_game(key)

        # 2️⃣ Attach multiplayer AFTER game exists
            if self.multiplayer_enabled:
                self.multiplayer_manager.attach_game(game)
                game.multiplayer_enabled = True
            else:
                game.multiplayer_enabled = False

        # 3️⃣ Update state
            self.state_manager.set_active_game(game)
            self.state_manager.set_state(self.state_manager.PLAYING)

        # 4️⃣ Start game
            game.start(self)

        except Exception as e:
            print(f"[ERROR] Failed to launch {game_name}: {e}")


if __name__ == "__main__":
    print("RUNNING APP")
    MiniGameCollectionApp().run()
