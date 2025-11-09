# =====================================
# main.py — FINAL FIXED VERSION
# =====================================
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout


from core.database import Database
from core.game_manager import GameManager


# -----------------------------------------------------------
#  Kivy Screens
# -----------------------------------------------------------
class MenuScreen(Screen):
    def on_enter(self):
        """Populate game list dynamically when entering."""
        if not hasattr(self, "app_ref") or self.app_ref is None:
            print("[MenuScreen] app_ref not set yet. Skipping game list load.")
            return

        game_list = self.ids.game_list
        game_list.clear_widgets()

        for game_name in self.app_ref.game_manager.get_game_list():
            btn = Button(
                text=game_name.title(),
                size_hint_y=None,
                height=50,
                on_release=lambda x, name=game_name: self.app_ref.launch_game(name)
            )
            game_list.add_widget(btn)


class GameScreen(Screen):
    pass


class StatsScreen(Screen):
    def on_enter(self):
        """Display match stats with session summary and tabular grid."""
        if not hasattr(self, "app_ref") or self.app_ref is None:
            return

        stats_list = self.ids.stats_list
        stats_list.clear_widgets()

        matches = self.app_ref.db.get_matches()
        if not matches:
            stats_list.add_widget(Label(text="No matches this session.", size_hint_y=None, height=30))
            return

        # 🧮 Calculate summary stats
        total_games = len(matches)
        wins = sum(1 for m in matches if m["result"].lower() == "win")
        draws = sum(1 for m in matches if m["result"].lower() == "draw")
        others = total_games - (wins + draws)

        # 🏁 Summary header
        summary_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=40, spacing=10)
        summary_box.add_widget(Label(text=f"[b]Games Played:[/b] {total_games}", markup=True))
        summary_box.add_widget(Label(text=f"[b]Wins:[/b] {wins}", markup=True))
        summary_box.add_widget(Label(text=f"[b]Draws:[/b] {draws}", markup=True))
        if others > 0:
            summary_box.add_widget(Label(text=f"[b]Other:[/b] {others}", markup=True))
        stats_list.add_widget(summary_box)

        # Header row
        header = GridLayout(cols=4, spacing=5, size_hint_y=None, height=30)
        for h in ["Game", "Result", "Winner", "Time"]:
            header.add_widget(Label(text=f"[b]{h}[/b]", markup=True))
        stats_list.add_widget(header)

        # Data rows
        for m in matches:
            row = GridLayout(cols=4, spacing=5, size_hint_y=None, height=25)
            row.add_widget(Label(text=m["game_name"]))
            row.add_widget(Label(text=m["result"]))
            row.add_widget(Label(text=m["winner"]))
            row.add_widget(Label(text=m["timestamp"].split("T")[1][:5]))
            stats_list.add_widget(row)




# -----------------------------------------------------------
#  Root App
# -----------------------------------------------------------
class MiniGameCollectionApp(App):
    def build(self):
        Builder.load_file("core/ui_manager.kv")

        self.db = Database()
        self.game_manager = GameManager(self.db)

        self.sm = ScreenManager()
        self.menu_screen = MenuScreen(name="menu")
        self.game_screen = GameScreen(name="game")
        self.stats_screen = StatsScreen(name="stats")

        # Attach reference before adding
        for s in [self.menu_screen, self.game_screen, self.stats_screen]:
            s.app_ref = self
            self.sm.add_widget(s)

        return self.sm

    # -------------------------------------------------------
    #  Screen helpers
    # -------------------------------------------------------
    def switch_to(self, screen_name):
        self.sm.current = screen_name

    def launch_game(self, game_name):
        print(f"[App] Launching {game_name}")
        game = self.game_manager.launch_game(game_name)
        game.start()  # stays on GameScreen until game ends

    def get_stats(self):
        return self.db.get_scores()


if __name__ == "__main__":
    MiniGameCollectionApp().run()
