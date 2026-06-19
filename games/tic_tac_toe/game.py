from core.base_game import BaseGame
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label


class TicTacToeGame(BaseGame):

    def __init__(self , db):
        super().__init__(db, "Tic Tac Toe")
        self.board = [''] * 9
        self.current = 'X'

    def start(self, app):
        from kivy.app import App
        self.app = App.get_running_app()

        self.begin_session()
        self.build_ui()
        self.reset()


    def build_ui(self):
        screen = self.app.game_screen
        screen.clear_widgets()

        layout = BoxLayout(orientation="vertical")

        self.grid = GridLayout(cols=3)
        self.buttons = []

        for i in range(9):
            btn = Button(font_size=40)
            btn.bind(on_release=lambda btn, idx=i: self.move(idx))
            self.buttons.append(btn)
            self.grid.add_widget(btn)

        layout.add_widget(self.grid)
        screen.add_widget(layout)
        self.app.switch_to("game")

    def reset(self):
        self.board = [''] * 9
        self.current = 'X'
        for btn in self.buttons:
            btn.text = ''

    def move(self, idx):
        if self.board[idx]:
            return

        self.board[idx] = self.current
        self.buttons[idx].text = self.current

        if self.check_winner():
            self.game_over(self.current)
            return

        self.current = 'O' if self.current == 'X' else 'X'

    def check_winner(self):
        wins = [
            (0,1,2),(3,4,5),(6,7,8),
            (0,3,6),(1,4,7),(2,5,8),
            (0,4,8),(2,4,6)
        ]
        for a,b,c in wins:
            if self.board[a] == self.board[b] == self.board[c] != '':
                return True
        return False

    def game_over(self, winner):
        from kivy.app import App
        app = App.get_running_app()

        if app and hasattr(app, "handle_game_over"):
            app.handle_game_over(self, winner)

